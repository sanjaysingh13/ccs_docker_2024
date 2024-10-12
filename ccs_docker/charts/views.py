import re
from collections import Counter
from itertools import groupby

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from django.shortcuts import render
from neomodel import db

from ccs_docker.backend.models import PoliceStation
from ccs_docker.searches.views import crime_search_query_generator

from .forms import CrimeSearchChartForm
from .forms import TransCrimePS
from .models import AdvancedCrimeSearchChart

non_alpha_numeric = re.compile(r"[^0-9a-zA-Z\s\.\-,?]+")


@login_required
# @cache_page(None)
# @csrf_protect
@permission_required("users.view_user", raise_exception=True)
def crime_search(request):
    template_name = "searches/crime_search.html"

    if request.method == "GET":
        form = CrimeSearchChartForm(initial={"full_text_search_type": 0})
    elif request.method == "POST":
        form = CrimeSearchChartForm(request.POST)
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
            advanced_crime_search_chart = AdvancedCrimeSearchChart.objects.create(
                keywords=keywords,
                full_text_search_type=full_text_search_type,
                tags=tags,
                search_any_tags=search_any_tags,
                districts=districts,
                ps_list=ps_list,
                min_date=min_date,
                max_date=max_date,
            )
            return redirect(advanced_crime_search_chart)
    return render(
        request,
        template_name,
        {
            "form": form,
            "form_title": "Comparison Charts for Crimes",
            "title": "Crime Charts",
        },
    )


@login_required
@permission_required("users.view_user", raise_exception=True)
def crime_search_chart(request, pk):
    advanced_crime_search = AdvancedCrimeSearchChart.objects.get(pk=pk)
    print(f"<<<<advanced_crime_search : {advanced_crime_search}")
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
    # original_min_date = min_date
    # original_max_date = max_date
    min_date = crime_search_query[5]
    max_date = crime_search_query[6]
    if query != []:
        query = " ".join(query)
        query_results = (
            query
            + """
      WITH node
      MATCH (police_station:PoliceStation)-[:BELONGS_TO_PS]-(node)
      RETURN police_station.uuid,node.case_date
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
        print(params)
        print(query_results)
        results, meta = db.cypher_query(query_results, params=params)
        if len(results) != 0:
            # crimes = [Crime.inflate(result[0])for result in results]
            crimes = [result[1] for result in results]
            if ps_list == "":
                crimes = dict(Counter(crimes))
                crimes = [{"x": k, "y": v} for k, v in crimes.items()]
                number_of_days = len(crimes)
                if number_of_days > 356:
                    time_unit = "year"
                elif number_of_days > 30:
                    time_unit = "month"
                else:
                    time_unit = "day"
                print(crimes)
                return render(
                    request,
                    "charts/crime_chart.html",
                    {
                        "crimes_json": crimes,
                        "stacked": "false",
                        "time_unit": time_unit,
                        "description": str(advanced_crime_search),
                    },
                )
            police_stations = [result[0] for result in results]
            crimes_with_ps = list(zip(police_stations, crimes, strict=False))
            crimes_with_ps.sort(key=lambda x: x[0])

            def key_func(x):
                return x[0]

            crimes_with_ps = groupby(crimes_with_ps, key_func)

            crimes_with_ps = {k: list(v) for (k, v) in crimes_with_ps}
            crimes_with_ps = {
                k: [v[1] for v in values] for k, values in crimes_with_ps.items()
            }
            crimes_with_ps = [
                (PoliceStation.nodes.get(uuid=k).name, dict(Counter(v)))
                for k, v in crimes_with_ps.items()
            ]
            number_of_days = len(
                sorted(crimes_with_ps, key=lambda x: len(x[1]))[-1][1],
            )
            if number_of_days > 356:
                time_unit = "year"
            elif number_of_days > 30:
                time_unit = "month"
            else:
                time_unit = "day"
            crimes_with_ps = [
                {"ps": k, "crimes": [{"x": k, "y": v} for k, v in value.items()]}
                for (k, value) in crimes_with_ps
            ]
            return render(
                request,
                "charts/crime_chart.html",
                {
                    "crimes_json": crimes_with_ps,
                    "stacked": "true",
                    "time_unit": time_unit,
                    "description": str(advanced_crime_search),
                },
            )
        messages.info(request, "No data for your query")
        return redirect("charts:crime_search")

    messages.info(request, "You didn't enter any search ")
    return redirect("charts:crime_search")


@login_required
@permission_required("users.view_user", raise_exception=True)
def trans_ps_activity(request):
    source_or_target = request.GET.get("q", "")
    addresses_with_ps_query = """
    MATCH (address:Address)-[:HAS_ADDRESS]-(:Criminal)-[:INVOLVED_IN]-(crime:Crime)
    WHERE  exists ((address)-[:BELONGS_TO_PS]-(:PoliceStation))
    RETURN count (address)
    """
    results, meta = db.cypher_query(addresses_with_ps_query)
    addresses_with_ps = results[0][0]
    addresses_without_ps_query = """
    MATCH (address:Address)-[:HAS_ADDRESS]-(:Criminal)-[:INVOLVED_IN]-(crime:Crime)
    WHERE  not exists ((address)-[:BELONGS_TO_PS]-(:PoliceStation))
    RETURN count (address)
    """
    results, meta = db.cypher_query(addresses_without_ps_query)
    addresses_without_ps = results[0][0]
    if source_or_target == "target":
        victim_ps_query = """
        MATCH (ps1:PoliceStation)-[:BELONGS_TO_PS]-(:Address)-[:HAS_ADDRESS]-(criminal:Criminal)-[:INVOLVED_IN]-(crime:Crime)-[:BELONGS_TO_PS]-(ps2:PoliceStation),(crime)-[:HAS_TAG]-(tag:Tag)
        WHERE ps1 <> ps2 AND tag.name in ["Dacoity","Robbery","Theft","Burglary","Extortion"] AND not ps2.name CONTAINS 'G.R.P.S.'
        WITH DISTINCT ps1,criminal,crime,ps2
        RETURN ps2.ps_with_distt , count( criminal) ORDER BY count(criminal) DESC LIMIT 20
        """
        victim_ps, meta = db.cypher_query(victim_ps_query)

        # Fix for B018 and first ISC003
        data = [victim[1] for victim in victim_ps]
        title = (
            "<h3>20 PSs  of West Bengal where most trans-PS crimes"
            " (property) are committed<p>* GRPS excluded</p></h3>"
        )
        link = "source"
    else:
        problem_ps_query = """
        MATCH (ps1:PoliceStation)-[:BELONGS_TO_PS]-(:Address)-[:HAS_ADDRESS]-(criminal:Criminal)-[:INVOLVED_IN]-(crime:Crime)-[:BELONGS_TO_PS]-(ps2:PoliceStation),(crime)-[:HAS_TAG]-(tag:Tag)
        WHERE ps1 <> ps2 AND tag.name in ["Dacoity","Robbery","Theft","Burglary","Extortion"]
        WITH DISTINCT ps1,criminal,crime,ps2
        RETURN ps1.ps_with_distt , count(crime) ORDER BY count(crime) DESC LIMIT 20
        """
        problem_ps, meta = db.cypher_query(problem_ps_query)

        labels = [problem[0] for problem in problem_ps]
        data = [problem[1] for problem in problem_ps]
        title = "<h3>20 PSs  of West Bengal from where most trans-PS crimes (property) are committed</h3>"
        link = "target"
    trans_ps_activity = {"labels": labels, "data": data}
    total_addresses = addresses_with_ps + addresses_without_ps
    # Fix for second ISC003
    addresses_with_ps_percentage = int(100 * addresses_with_ps / total_addresses)
    subtitle = (
        f"(Out of {total_addresses} addresses in CCS database, "
        f"{addresses_with_ps_percentage} % have a Police Station "
        "associated with the address. This summary is based on that)"
    )
    return render(
        request,
        "charts/trans_ps_activity.html",
        {
            "trans_ps_activity": trans_ps_activity,
            "total_addresses": total_addresses,
            "addresses_with_ps_percentage": addresses_with_ps_percentage,
            "title": title,
            "link": link,
            "subtitle": subtitle,
        },
    )


@login_required
@permission_required("users.view_user", raise_exception=True)
def trans_ps_activity_in_ps(request):
    template_name = "charts/trans_ps_target.html"
    if request.method == "GET":
        form = TransCrimePS()
    elif request.method == "POST":
        form = TransCrimePS(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            ps_with_distt = cleaned_data.get("police_station_with_distt", "")
            ps = PoliceStation.nodes.get(ps_with_distt=ps_with_distt)
            uuid = ps.uuid
            victim_ps_query = """
                MATCH (ps1:PoliceStation)-[:BELONGS_TO_PS]-(:Address)-[:HAS_ADDRESS]-(criminal:Criminal)-[:INVOLVED_IN]-(crime:Crime)-[:BELONGS_TO_PS]-(ps2:PoliceStation {uuid:$uuid}),(crime)-[:HAS_TAG]-(tag:Tag)
                WHERE ps1 <> ps2 AND tag.name in ["Dacoity","Robbery","Theft","Burglary","Extortion"] AND not ps2.name CONTAINS 'G.R.P.S.'
                WITH DISTINCT ps1,criminal,crime
                RETURN ps1.ps_with_distt , count( *) ORDER BY count(*)
                """
            victim_ps, meta = db.cypher_query(
                victim_ps_query,
                params={"uuid": str(uuid)},
            )

            # Fix for third ISC003
            print(PoliceStation.nodes.get(uuid=uuid).ps_with_distt)
            title = (
                "<h3>PSs  of West Bengal from where most trans-PS crimes are committed in",
                f"  {PoliceStation.nodes.get(uuid=uuid).ps_with_distt}</h3>",
            )
            return render(
                request,
                "charts/trans_ps_activity.html",
                {"trans_ps_activity": trans_ps_activity, "title": title},
            )
    return render(
        request,
        template_name,
        {"form": form, "form_title": "Trans-PS crimes in target PS"},
    )
