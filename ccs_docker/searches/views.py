# CHANGE TO UUID
import csv
import re
from datetime import timedelta

import pytz
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from neomodel import db

from ccs_docker.backend.models import Crime
from ccs_docker.backend.models import PoliceStation

from .forms import CrimeSearchForm
from .forms import CriminalSearchForm
from .models import AdvancedCrimeSearch
from .models import AdvancedCriminalSearch
from .nodeutils import basic_criminal_search

no_ps = re.compile(r"P.S. $")
no_address = re.compile(r" r/o  ")
non_alpha_numeric = re.compile(r"[^0-9a-zA-Z\s\.\-,?]+")

# Define the timezone for India
INDIA_TZ = pytz.timezone("Asia/Kolkata")


def get_current_date():
    return timezone.now().astimezone(INDIA_TZ).date()


def get_last_year_date():
    return (timezone.now().astimezone(INDIA_TZ) - timedelta(days=365)).date()


def crime_search_query_generator(
    keywords,
    full_text_search_type,
    tags,
    search_any_tags,
    districts,
    ps_list,
    min_date,
    max_date,
):
    keyword_param = None
    districts_param = None
    police_stations = None
    query = []
    if keywords != "":
        keywords = re.sub(non_alpha_numeric, "-", keywords)
        if full_text_search_type == 2:
            keyword_param = f'{" AND ".join([keyword.strip()+"~" for keyword in keywords.split(" ") if keyword])}'
            query.append(
                """CALL db.index.fulltext.queryNodes('crime_gist', $keyword_param) YIELD node, score
            """,
            )
        elif full_text_search_type == 1:
            keyword_param = f'{" AND ".join(["*"+keyword.strip()+"*" for keyword in keywords.split(" ") if keyword])}'
            query.append(
                """CALL db.index.fulltext.queryNodes('crime_gist', $keyword_param) YIELD node, score
            """,
            )
        else:
            keyword_param = f'{" AND ".join([keyword.strip() for keyword in keywords.split(" ") if keyword])}'
            query.append(
                """CALL db.index.fulltext.queryNodes('crime_gist', $keyword_param ) YIELD node, score
            """,
            )
        if tags != "":
            tags = list(filter(None, [tag.strip() for tag in tags.split(",") if tag]))
            if tags != []:
                if search_any_tags:
                    query.append(
                        """WITH node,score
                        MATCH (node)-[:HAS_TAG]->(tag:Tag)
          WHERE tag.name IN $tags
          """,
                    )
                else:
                    query.append(
                        """WITH node,score, $tags as tags
            MATCH (node)-[:HAS_TAG]-(tag:Tag)
            WHERE tag.name in tags
            WITH node,score, size(tags) as inputCnt, count(DISTINCT tag) as cnt
            WHERE cnt = inputCnt
            """,
                    )

        if districts != "Null":
            districts_param = districts.split(",")
            query.append(
                """WITH node,score
          MATCH (node)-[:BELONGS_TO_PS]-(:PoliceStation)-[:BELONGS_TO_DISTRICT]-(district:District)
          WHERE district.uuid IN $districts_param
          """,
            )
        if ps_list != "":
            police_stations = list(
                filter(
                    None,
                    [
                        police_station.strip()
                        for police_station in ps_list.split(",")
                        if police_station
                    ],
                ),
            )
            if police_stations != []:
                query.append(
                    """WITH node,score
            MATCH (node)-[:BELONGS_TO_PS]-(police_station:PoliceStation)
          WHERE police_station.uuid IN $police_stations
          """,
                )
        if min_date and max_date:
            query.append(
                """WITH node,score
                MATCH (node)
          WHERE node.case_date >= $min_date And node.case_date <= $max_date
          """,
            )
        elif min_date:
            query.append(
                """
                WITH node,score
                MATCH (node)
          WHERE node.case_date >= $min_date
          """,
            )
        elif max_date:
            query.append(
                """WITH node,score
                MATCH (node)
          WHERE node.case_date <= $max_date
          """,
            )
        elif query != []:
            max_date = get_current_date().strftime("%Y-%m-%d")
            min_date = get_last_year_date().strftime("%Y-%m-%d")
            query.append(
                """WITH node,score
                    MATCH (node)
          WHERE node.case_date >= $min_date And node.case_date <= $max_date
          """,
            )
    elif tags != "":
        tags = list(filter(None, [tag.strip() for tag in tags.split(",") if tag]))
        if tags != []:
            if search_any_tags:
                query.append(
                    """
                        MATCH (node)-[:HAS_TAG]->(tag:Tag)
          WHERE tag.name IN $tags
          """,
                )
            else:
                query.append(
                    """
            WITH $tags as tags
            MATCH (node)-[:HAS_TAG]-(tag:Tag)
            WHERE tag.name in tags
            WITH node, size(tags) as inputCnt, count(DISTINCT tag) as cnt
            WHERE cnt = inputCnt
            """,
                )

        if districts != "Null":
            districts_param = districts.split(",")
            query.append(
                """WITH node
              MATCH (node)-[:BELONGS_TO_PS]-(:PoliceStation)-[:BELONGS_TO_DISTRICT]-(district:District)
              WHERE district.uuid IN $districts_param
              """,
            )
        if ps_list != "":
            police_stations = list(
                filter(
                    None,
                    [
                        police_station.strip()
                        for police_station in ps_list.split(",")
                        if police_station
                    ],
                ),
            )
            if police_stations != []:
                query.append(
                    """WITH node
                MATCH (node)-[:BELONGS_TO_PS]-(police_station:PoliceStation)
              WHERE police_station.uuid IN $police_stations
              """,
                )
        if min_date and max_date:
            query.append(
                """WITH node
                    MATCH (node)
              WHERE node.case_date >= $min_date And node.case_date <= $max_date
              """,
            )
        elif min_date:
            query.append(
                """
                    WITH node
                    MATCH (node)
              WHERE node.case_date >= $min_date
              """,
            )
        elif max_date:
            query.append(
                """WITH node
                    MATCH (node)
              WHERE node.case_date <= $max_date
              """,
            )
        elif query != []:
            max_date = get_current_date().strftime("%Y-%m-%d")
            min_date = get_last_year_date().strftime("%Y-%m-%d")
            query.append(
                """WITH node
                        MATCH (node)
              WHERE node.case_date >= $min_date And node.case_date <= $max_date
              """,
            )
    elif districts != "Null":
        districts_param = districts.split(",")
        query.append(
            """
              MATCH (node)-[:BELONGS_TO_PS]-(:PoliceStation)-[:BELONGS_TO_DISTRICT]-(district:District)
              WHERE district.uuid IN $districts_param
              """,
        )
        if ps_list != "":
            police_stations = list(
                filter(
                    None,
                    [
                        police_station.strip()
                        for police_station in ps_list.split(",")
                        if police_station
                    ],
                ),
            )
            if police_stations != []:
                query.append(
                    """WITH node
                    MATCH (node)-[:BELONGS_TO_PS]-(police_station:PoliceStation)
                  WHERE police_station.uuid IN $police_stations
                  """,
                )
        if min_date and max_date:
            query.append(
                """WITH node
                        MATCH (node)
                  WHERE node.case_date >= $min_date And node.case_date <= $max_date
                  """,
            )
        elif min_date:
            query.append(
                """
                        WITH node
                        MATCH (node)
                  WHERE node.case_date >= $min_date
                  """,
            )
        elif max_date:
            query.append(
                """WITH node
                        MATCH (node)
                  WHERE node.case_date <= $max_date
                  """,
            )
        elif query != []:
            max_date = get_current_date().strftime("%Y-%m-%d")
            min_date = get_last_year_date().strftime("%Y-%m-%d")
            query.append(
                """WITH node
                            MATCH (node)
                  WHERE node.case_date >= $min_date And node.case_date <= $max_date
                  """,
            )
    elif ps_list != "":
        police_stations = list(
            filter(
                None,
                [
                    police_station.strip()
                    for police_station in ps_list.split(",")
                    if police_station
                ],
            ),
        )
        if police_stations != []:
            query.append(
                """
                    MATCH (node)-[:BELONGS_TO_PS]-(police_station:PoliceStation)
                  WHERE police_station.uuid IN $police_stations
                  """,
            )
        if min_date and max_date:
            query.append(
                """WITH node
                            MATCH (node)
                      WHERE node.case_date >= $min_date And node.case_date <= $max_date
                      """,
            )
        elif min_date:
            query.append(
                """
                            WITH node
                            MATCH (node)
                      WHERE node.case_date >= $min_date
                      """,
            )
        elif max_date:
            query.append(
                """WITH node
                            MATCH (node)
                      WHERE node.case_date <= $max_date
                      """,
            )
        elif query != []:
            max_date = get_current_date().strftime("%Y-%m-%d")
            min_date = get_last_year_date().strftime("%Y-%m-%d")
            query.append(
                """WITH node
                                MATCH (node)
                      WHERE node.case_date >= $min_date And node.case_date <= $max_date
                      """,
            )
    elif min_date and max_date:
        query.append(
            """
                            MATCH (node:Crime)
                      WHERE node.case_date >= $min_date And node.case_date <= $max_date
                      """,
        )
    elif min_date:
        query.append(
            """
                            MATCH (node:Crime)
                      WHERE node.case_date >= $min_date
                      """,
        )
    elif max_date:
        query.append(
            """
                            MATCH (node:Crime)
                      WHERE node.case_date <= $max_date
                      """,
        )
    elif query != []:
        max_date = get_current_date().strftime("%Y-%m-%d")
        min_date = get_last_year_date().strftime("%Y-%m-%d")
        query.append(
            """
                                MATCH (node:Crime)
                      WHERE node.case_date >= $min_date And node.case_date <= $max_date
                      """,
        )
    return (
        query,
        keyword_param,
        districts_param,
        police_stations,
        tags,
        min_date,
        max_date,
    )


@login_required
# @cache_page(None)
# @csrf_protect
@permission_required("users.view_user", raise_exception=True)
def crime_search(request):
    template_name = "searches/crime_search.html"

    if request.method == "GET":
        form = CrimeSearchForm(initial={"full_text_search_type": 0})
    elif request.method == "POST":
        form = CrimeSearchForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            keywords = cleaned_data.get("keywords", "")
            full_text_search_type = cleaned_data.get("full_text_search_type", "")
            tags = cleaned_data.get("tags", "")
            districts = cleaned_data.get("districts", "")
            ps_list = cleaned_data.get("ps_list", "")
            min_date = cleaned_data.get("min_date", "")
            max_date = cleaned_data.get("max_date", "")
            # advanced_search_crime = cleaned_data.get("advanced_search_crime", "")
            search_any_tags = cleaned_data.get("search_any_tags", "")
            if cleaned_data.get("advanced_search_crime", ""):
                advanced_crime_search = AdvancedCrimeSearch.objects.create(
                    keywords=keywords,
                    full_text_search_type=full_text_search_type,
                    tags=tags,
                    search_any_tags=search_any_tags,
                    districts=districts,
                    ps_list=ps_list,
                    min_date=min_date,
                    max_date=max_date,
                )
                # base_url = reverse('searches:crime_search_results')  # 1 /products/
                # query_string =  urlencode({'keywords':keywords,'full_text_search_type':full_text_search_type,'tags':tags,'districts':districts,'ps_list':ps_list,'min_date':min_date,'max_date':max_date,'advanced_search_crime':advanced_search_crime})  # 2 category=42
                # url = '{}?{}'.format(base_url, query_string)  # 3 /products/?category=42
                # return redirect(url)
                return redirect(advanced_crime_search)
            # ps_uuid = None
            case_no = None
            case_year = None
            police_station = PoliceStation.nodes.get_or_none(
                ps_with_distt=cleaned_data.get("police_station_with_distt", ""),
            )
            case_no = cleaned_data.get("case_no", "")
            if cleaned_data.get("case_date", ""):
                case_date = cleaned_data.get("case_date")
                case_year = str(case_date.year)[-2:]
            else:
                case_year = cleaned_data.get("case_year")

            single_crime_query = """
                MATCH (police_station:PoliceStation)-[:BELONGS_TO_PS]-(crime:Crime)
                WHERE police_station.uuid = $ps_uuid
                AND crime.case_no = $case_no
                AND crime.year = $case_year
                RETURN crime

                """
            params = {
                "ps_uuid": police_station.uuid,
                "case_no": case_no,
                "case_year": case_year,
            }
            results, meta = db.cypher_query(single_crime_query, params=params)
            if len(results) != 0:
                crime = Crime.inflate(results[0][0])
                return redirect(crime)

            messages.info(request, "No crime found")
            return redirect("searches:crime_search")

            # template_name = "searches/crime_search_results"

            #####
    return render(
        request,
        template_name,
        {
            "form": form,
            "form_title": "Basic and Advanced Search for Crimes",
            "title": "Crime Search",
        },
    )


@login_required
@permission_required("users.view_user", raise_exception=True)
def crime_search_results(request, pk):
    advanced_crime_search = AdvancedCrimeSearch.objects.get(pk=pk)
    keywords = advanced_crime_search.keywords
    full_text_search_type = advanced_crime_search.full_text_search_type
    tags = advanced_crime_search.tags
    search_any_tags = advanced_crime_search.search_any_tags
    districts = advanced_crime_search.districts
    ps_list = advanced_crime_search.ps_list
    min_date = advanced_crime_search.min_date
    max_date = advanced_crime_search.max_date

    crime_search_query = crime_search_query_generator(
        keywords,
        full_text_search_type,
        tags,
        search_any_tags,
        districts,
        ps_list,
        min_date,
        max_date,
    )
    query = crime_search_query[0]
    keyword_param = crime_search_query[1]
    districts_param = crime_search_query[2]
    police_stations = crime_search_query[3]
    tags = crime_search_query[4]
    original_min_date = min_date
    original_max_date = max_date
    min_date = crime_search_query[5]
    max_date = crime_search_query[6]
    if query != []:
        query = " ".join(query)
        query_check_size_of_results = (
            query
            + """
      RETURN count(node) as result_count
      """
        )
        params = {
            "keyword_param": keyword_param,
            "tags": tags,
            "districts_param": districts_param,
            "police_stations": police_stations,
            "min_date": min_date,
            "max_date": max_date,
        }
        results, meta = db.cypher_query(query_check_size_of_results, params=params)
        if results[0][0] < 5000:
            if (
                not (
                    keywords == ""
                    and tags == []
                    and districts == "Null"
                    and ps_list == ""
                )
                and not original_min_date
                and not original_max_date
            ):
                messages.info(
                    request,
                    "Since you didn't specify date range, default period of last one year was set.",
                )
            messages.info(request, f"Your search has {results[0][0]} results.")
            if keywords != "":
                compiled_query_results = (
                    query
                    + """
                      WITH node, score
                      MATCH (district:District)-[:BELONGS_TO_DISTRICT]-(police_station:PoliceStation)-[:BELONGS_TO_PS]-(node)
                      RETURN police_station.name as ps, node.case_no as case_no, node.case_date as case_date, node.year as year, node.sections as sections, node.gist as gist, node.uuid as id,score, district.name as district
                      ORDER BY score DESC
                      """
                )
            else:
                compiled_query_results = (
                    query
                    + """
                      WITH node
                      MATCH (district:District)-[:BELONGS_TO_DISTRICT]-(police_station:PoliceStation)-[:BELONGS_TO_PS]-(node)
                      RETURN police_station.name as ps, node.case_no as case_no, node.case_date as case_date, node.year as year, node.sections as sections, node.gist as gist, node.uuid as id, district.name as district
                      ORDER BY node.case_date DESC
                      """
                )
            results, meta = db.cypher_query(compiled_query_results, params=params)
            crimes = [
                (
                    f"{result[0]} P.S.  C/No. {result[1]}"
                    f"{' of ' + str(result[2].year) if result[2] else ' of ' + result[3]}"
                    f"{' u/s ' + result[4] if result[4] else ''}",
                    result[5],
                    result[7],
                )
                for result in results
            ]
            districts = [result[7] for result in results]
            download_csv = request.GET.get("download_csv")
            if download_csv:
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = (
                    'attachment; filename="crime_search_results.csv"'
                )
                # Combine districts and crimes
                combined_data = list(zip(districts, crimes, strict=False))
                # Create a CSV writer
                writer = csv.writer(response)
                writer.writerow(["Sl No.", "District", "Case", "Gist"])

                # Write the complete search results to the CSV file
                for index, (district, crime) in enumerate(combined_data, start=1):
                    writer.writerow([index, district, crime[0], crime[1]])

                return response

            paginator = Paginator(crimes, 30)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            return render(
                request,
                "searches/crime_search_results.html",
                {"crimes": page_obj},
            )
        messages.info(
            request,
            f"Your search has {results[0][0]} results. Please narrow it down",
        )
        return redirect("searches:crime_search")
    messages.info(request, "You didn't enter any search ")
    return redirect("searches:crime_search")


@login_required
# @cache_page(None)
# @csrf_protect
def criminal_search(request):
    template_name = "searches/criminal_search.html"
    if request.method == "GET":
        form = CriminalSearchForm(initial={"full_text_search_type": 0})
    elif request.method == "POST":
        form = CriminalSearchForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            first_name = cleaned_data.get("first_name", "")
            last_name = cleaned_data.get("last_name", "")
            guardian_first_name = cleaned_data.get("guardian_first_name", "")
            aliases = cleaned_data.get("aliases", "")
            exact_name_search = cleaned_data.get("exact_name_search")
            address = cleaned_data.get("address", "")
            id_mark = cleaned_data.get("id_mark", "")

            # no_particulars_search = (
            #     first_name == ""
            #     and last_name == ""
            #     and guardian_first_name == ""
            #     and aliases == ""
            #     and address == ""
            #     and id_mark == ""
            # )
            # query = []
            # query_crime = []
            # compiled_query_crime = ""
            # search_terms = 0
            # advanced_search_terms = 0
            # keyword_param = None
            # districts_param = None
            tags = None
            # police_stations = None
            min_date = cleaned_data.get("min_date", "")
            max_date = cleaned_data.get("max_date", "")
            if not min_date:
                min_date = get_last_year_date().strftime("%Y-%m-%d")
            if not max_date:
                max_date = get_current_date().strftime("%Y-%m-%d")
            keywords = cleaned_data.get("keywords", "")
            full_text_search_type = cleaned_data.get("full_text_search_type", "")
            tags = cleaned_data.get("tags", "")
            search_any_tags = cleaned_data.get("search_any_tags", "")
            districts = cleaned_data.get("districts", "")
            ps_list = cleaned_data.get("ps_list", "")
            advanced_criminal_search = AdvancedCriminalSearch.objects.create(
                first_name=first_name,
                last_name=last_name,
                guardian_first_name=guardian_first_name,
                aliases=aliases,
                exact_name_search=exact_name_search,
                address=address,
                id_mark=id_mark,
                keywords=keywords,
                full_text_search_type=full_text_search_type,
                tags=tags,
                search_any_tags=search_any_tags,
                districts=districts,
                ps_list=ps_list,
                min_date=min_date,
                max_date=max_date,
            )
            return redirect(advanced_criminal_search)
    return render(request, template_name, {"form": form})


@permission_required("users.view_user", raise_exception=True)
@login_required
def criminal_search_results(request, pk):
    advanced_criminal_search = AdvancedCriminalSearch.objects.get(pk=pk)
    first_name = advanced_criminal_search.first_name
    last_name = advanced_criminal_search.last_name
    exact_name_search = advanced_criminal_search.exact_name_search
    guardian_first_name = advanced_criminal_search.guardian_first_name
    aliases = advanced_criminal_search.aliases
    address = advanced_criminal_search.address
    id_mark = advanced_criminal_search.id_mark
    no_particulars_search = (
        first_name == ""
        and last_name == ""
        and guardian_first_name == ""
        and aliases == ""
        and address == ""
        and id_mark == ""
    )
    keywords = advanced_criminal_search.keywords
    full_text_search_type = advanced_criminal_search.full_text_search_type
    tags = advanced_criminal_search.tags
    search_any_tags = advanced_criminal_search.search_any_tags

    districts = advanced_criminal_search.districts
    ps_list = advanced_criminal_search.ps_list
    min_date = advanced_criminal_search.min_date
    max_date = advanced_criminal_search.max_date
    crime_search_query = crime_search_query_generator(
        keywords,
        full_text_search_type,
        tags,
        search_any_tags,
        districts,
        ps_list,
        min_date,
        max_date,
    )
    crime_query = crime_search_query[0]
    if crime_query != []:
        crime_query = " ".join(crime_query)
        if keywords != "":
            crime_query_with_results = (
                crime_query
                + """
              WITH node, score
              MATCH (criminal:Criminal)-[:INVOLVED_IN]-(node)
              RETURN DISTINCT criminal, score*5 as totalScore,  'adv' as search"""
            )
        else:
            crime_query_with_results = (
                crime_query
                + """
              WITH node
              MATCH (criminal:Criminal)-[:INVOLVED_IN]-(node)
              RETURN DISTINCT criminal, 1 as totalScore,  'adv' as search"""
            )
    keyword_param = crime_search_query[1]
    districts_param = crime_search_query[2]
    police_stations = crime_search_query[3]
    tags = crime_search_query[4]
    # original_min_date = min_date
    # original_max_date = max_date
    min_date = crime_search_query[5]
    max_date = crime_search_query[6]

    basic_criminal_search_query = basic_criminal_search(
        first_name,
        last_name,
        guardian_first_name,
        aliases,
        id_mark,
        address,
        exact_name_search,
    )
    basic_query = basic_criminal_search_query[0]
    basic_search_params = basic_criminal_search_query[1]
    advanced_params = {
        "keyword_param": keyword_param,
        "tags": tags,
        "districts_param": districts_param,
        "police_stations": police_stations,
        "min_date": min_date,
        "max_date": max_date,
    }
    search_mode = "no search"
    if no_particulars_search and crime_query != []:
        search_mode = "advanced only"
        params = advanced_params
    if not no_particulars_search and crime_query == []:
        search_mode = "basic only"
        params = basic_search_params
    if not no_particulars_search and crime_query != []:
        search_mode = "advanced and basic"
        params = {**basic_search_params, **advanced_params}

    if search_mode == "advanced only":
        # Check that there are not too many crimes

        query_check_size_of_results = (
            crime_query
            + """
        WITH node
        MATCH (criminal:Criminal)-[:INVOLVED_IN]-(node)
          RETURN count(DISTINCT criminal) as results"""
        )
        results, meta = db.cypher_query(query_check_size_of_results, params=params)
        if results[0][0] < 5000:
            print("11111")
            # modify crime_query_with_results to return images too
            if keywords != "":
                crime_query_with_results = crime_query_with_results.replace(
                    "RETURN DISTINCT criminal",
                    "OPTIONAL MATCH (criminal)-[:HAS_IMAGE]-(image:Image) \n OPTIONAL MATCH (criminal)-[:HAS_ADDRESS]-(address:Address)\n OPTIONAL MATCH (address)-[:BELONGS_TO_PS]-(ps:PoliceStation) \n WITH DISTINCT criminal.uuid as criminal_uuid , head(collect([criminal, address, image, ps])) as identifier , score \n RETURN   coalesce(identifier[0].first_name , '')+ ' ' + coalesce(identifier[0].last_name , '') + ' s/o ' + coalesce(identifier[0].guardian_first_name , '') + ' r/o ' + coalesce(identifier[1].name , '') + ' P.S. ' + coalesce(identifier[3].name , ''), identifier[2].avatar_url, criminal_uuid",
                )
            else:
                crime_query_with_results = crime_query_with_results.replace(
                    "RETURN DISTINCT criminal",
                    "OPTIONAL MATCH (criminal)-[:HAS_IMAGE]-(image:Image) \n OPTIONAL MATCH (criminal)-[:HAS_ADDRESS]-(address:Address)\n OPTIONAL MATCH (address)-[:BELONGS_TO_PS]-(ps:PoliceStation) \n WITH DISTINCT criminal.uuid as criminal_uuid , head(collect([criminal, address, image, ps])) as identifier  \n RETURN   coalesce(identifier[0].first_name , '')+ ' ' + coalesce(identifier[0].last_name , '') + ' s/o ' + coalesce(identifier[0].guardian_first_name , '') + ' r/o ' + coalesce(identifier[1].name , '') + ' P.S. ' + coalesce(identifier[3].name , ''), identifier[2].avatar_url, criminal_uuid",
                )
            print(crime_query_with_results)
            results, meta = db.cypher_query(crime_query_with_results, params=params)
            criminals = [
                (
                    re.sub(no_address, "", re.sub(no_ps, "", result[0])),
                    result[1],
                    result[2],
                )
                for result in results
            ]
            paginator = Paginator(criminals, 30)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            messages.info(request, f"Your search has {len(criminals)} results.")
            return render(
                request,
                "searches/criminal_search_results.html",
                {"criminals": page_obj},
            )
        messages.info(
            request,
            f"Your search has {results[0][0]} results. Please narrow it down",
        )
        return redirect("searches:criminal_search")
    if search_mode == "advanced and basic":
        combined_query_check_size_of_results = (
            "CALL {"
            + basic_query
            + " UNION ALL "
            + crime_query_with_results
            + """ }
        WITH criminal, count(*) AS matches , sum(totalScore) AS finalScore, collect(search) as search_types
        WITH criminal, matches,finalScore
        WHERE matches = 2  AND size(search_types) = size(apoc.coll.toSet(search_types))
        RETURN count(criminal) as results
         """
        )
        results, meta = db.cypher_query(
            combined_query_check_size_of_results,
            params=params,
        )
        if results[0][0] < 5000:
            print("22222")
            final_query = (
                "CALL {"
                + basic_query
                + " UNION ALL "
                + crime_query_with_results
                + """}
            WITH criminal, count(*) AS matches , sum(totalScore) AS finalScore, collect(search) as search_types
            WITH criminal, matches,finalScore
            WHERE matches = 2 AND size(search_types) = size(apoc.coll.toSet(search_types))
            OPTIONAL MATCH (criminal)-[:HAS_IMAGE]-(image:Image)
            OPTIONAL MATCH (criminal)-[:HAS_ADDRESS]-(address:Address)
            OPTIONAL MATCH (address)-[:BELONGS_TO_PS]-(ps:PoliceStation)
            WITH DISTINCT criminal.uuid as criminal_uuid , head(collect([criminal, address, image, ps,finalScore])) as identifier \n RETURN   coalesce(identifier[0].first_name , '')+ ' ' + coalesce(identifier[0].last_name , '') + ' s/o ' + coalesce(identifier[0].guardian_first_name , '') + ' r/o ' + coalesce(identifier[1].name , '') + ' P.S. ' + coalesce(identifier[3].name , ''), identifier[2].avatar_url, criminal_uuid,identifier[4] as finalScore
            ORDER BY finalScore DESC
             """
            )
            results, meta = db.cypher_query(final_query, params=params)
            criminals = [
                (
                    re.sub(no_address, "", re.sub(no_ps, "", result[0])),
                    result[1],
                    result[2],
                )
                for result in results
            ]
            paginator = Paginator(criminals, 30)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            messages.info(request, f"Your search has {len(criminals)} results.")
            return render(
                request,
                "searches/criminal_search_results.html",
                {"criminals": page_obj},
            )
        messages.info(
            request,
            f"Your search has {results[0][0]} results. Please narrow it down",
        )
        return redirect("searches:criminal_search")
    if search_mode == "basic only":
        modified_basic_query = basic_query.replace(
            "RETURN node as criminal, totalScore, 'basic' as search",
            "RETURN count(node) as criminal",
        )
        modified_basic_query = modified_basic_query.replace(
            "ORDER BY totalScore DESC",
            "",
        )
        basic_query_check_size = modified_basic_query
        results, meta = db.cypher_query(basic_query_check_size, params=params)
        if results[0][0] < 5000:
            print("3333")
            # modify basic_query_with_results to return images too RETURN node as criminal, totalScore, 'basic' as search
            basic_query = basic_query.replace(
                "RETURN node as criminal, totalScore, 'basic' as search",
                " OPTIONAL MATCH (node)-[:HAS_IMAGE]-(image:Image) \n OPTIONAL MATCH (node)-[:HAS_ADDRESS]-(address:Address) \n OPTIONAL MATCH (address)-[:BELONGS_TO_PS]-(ps:PoliceStation) \n WITH DISTINCT node.uuid as criminal_uuid , head(collect([node, address, image, ps,totalScore])) as identifier \n RETURN   coalesce(identifier[0].first_name , '')+ ' ' + coalesce(identifier[0].last_name , '') + ' s/o ' + coalesce(identifier[0].guardian_first_name , '') + ' r/o ' + coalesce(identifier[1].name , '') + ' P.S. ' + coalesce(identifier[3].name , ''), identifier[2].avatar_url, criminal_uuid,identifier[4] as totalScore",
            )
            results, meta = db.cypher_query(basic_query, params=params)
            criminals = [
                (
                    re.sub(no_address, "", re.sub(no_ps, "", result[0])),
                    result[1],
                    result[2],
                )
                for result in results
            ]
            paginator = Paginator(criminals, 30)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            messages.info(request, f"Your search has {len(criminals)} results.")
            return render(
                request,
                "searches/criminal_search_results.html",
                {"criminals": page_obj},
            )
        messages.info(
            request,
            f"Your search has {results[0][0]} results. Please narrow it down",
        )
        return redirect("searches:criminal_search")
