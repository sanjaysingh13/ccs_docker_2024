# Create your tasks here
import datetime
import re
import uuid

# import face_recognition
import xmltodict
from celery import group
from dateutil.parser import parse
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

# from demoapp.models import Widget
from neomodel import db

from ccs_docker.backend.models import Address
from ccs_docker.backend.models import Crime
from ccs_docker.backend.models import CrimeNewsSheet
from ccs_docker.backend.models import Criminal
from ccs_docker.backend.models import DailyArrest
from ccs_docker.backend.models import PoliceStation as BackendPoliceStation
from ccs_docker.backend.models import Stats
from ccs_docker.backend.models import Tag
from ccs_docker.backend.models import Vehicle
from ccs_docker.charts.models import AdvancedCrimeSearchChart
from ccs_docker.searches.models import AdvancedCrimeSearch
from ccs_docker.searches.models import AdvancedCriminalSearch
from ccs_docker.users.models import PoliceStation as UserPoliceStation
from ccs_docker.users.models import User
from config.celery_app import app

# vehicle regexes
engine = re.compile(
    r"eng.{0,6}\s{0,3}no.?\s{0,3}(.{0,20}\d\s?\d\s?\d\s?\d\s?\d\s?)",
    re.IGNORECASE,
)
chassis = re.compile(
    r"ch.{0,6}\s{0,3}no.?\s{0,3}(.{0,20}\d\s?\d\s?\d\s?\d\s?\d\s?)",
    re.IGNORECASE,
)
reg = re.compile(
    r"[A-Z][A-Z][\-\/\s]{0,2}\d\d[\-\/\s]{0,2}[A-Z]{1,2}[\-\/\s]{0,2}\d{4}",
    re.IGNORECASE,
)
non_alpha_numeric = re.compile(r"[^0-9a-zA-Z]+")

# crime classification regexes
firearms = re.compile(r"25.{0,10}A.{0,4}act", re.IGNORECASE)
narcotics = re.compile(r"n.{0,2}d.{0,2}p.{0,2}s.{0,3}act", re.IGNORECASE)
murder = re.compile(r"302|396")
rape = re.compile(r"376")
gang_rape = re.compile(r"376.{0,3}d", re.IGNORECASE)
dacoity = re.compile(r"395|396|397")
theft = re.compile(r"379|380")
dowry_death = re.compile(r"304.{0,2}b", re.IGNORECASE)
immoral_trafficking = re.compile(
    r"i.{0,2}t.{0,2}p.{0,5}act|immoral.{0,2}trafficking.{0,2}prevention.{0,5}act",
    re.IGNORECASE,
)
trafficking = re.compile(r"370")
sedition = re.compile(r"124.{0,2}a", re.IGNORECASE)
waging_war = re.compile(r"121", re.IGNORECASE)
harbouring = re.compile(r"216a", re.IGNORECASE)
communal_provocation = re.compile(r"153.{0,2}[ab]", re.IGNORECASE)
adulteration = re.compile(r"27[245]", re.IGNORECASE)
abetment_suicide = re.compile(r"306")
culpable_homicide = re.compile(
    r"304(?!.{0,2}b)",
    re.IGNORECASE,
)  # negative pattern matching
kidnapping = re.compile(r"36[4356789]")
abduction = re.compile(r"36[2456789]")
attempt_murder = re.compile(r"307")
ransom = re.compile(r"364.{0,2}a", re.IGNORECASE)
compel_marriage = re.compile(r"366")
importation = re.compile(r"366.{0,2}b", re.IGNORECASE)
minor = re.compile(r"366.{0,2}a|372", re.IGNORECASE)
prostitution = re.compile(r"37[23]")
extortion = re.compile(r"38[3456789]")
robbery = re.compile(r"39[0234]")
preparation_dacoity = re.compile(r"399.{0,4}402")
criminal_breach_trust = re.compile(r"40[56789]")
misappropriation = re.compile(r"40[34]")
cheating = re.compile(r"41[56789]|420")
forgery = re.compile(r"46[3456789]|47[012]")
ficn = re.compile(r"489")
outraging_modesty = re.compile(r"354")
acid_attack = re.compile(r"326a", re.IGNORECASE)
conspiracy = re.compile(r"120b", re.IGNORECASE)
carnal_intercourse = re.compile(r"377")
drugging = re.compile(r"328")
carnal_intercourse = re.compile(r"377")
foreigners_act = re.compile(
    r"14.{0,2}f.{0,2}act|14.{0,2}a.{0,2}f.{0,2}act|14.{0,2}a.{0,2}b.{0,2}f.{0,2}act",
    re.IGNORECASE,
)
gambling_act = re.compile(
    r"3.{1,2}4.{0,3}w.{0,1}b.{0,1}g.{0,4}p.{0,1}c.{0,2}act",
    re.IGNORECASE,
)
pocso = re.compile(r"pocso", re.IGNORECASE)
sc_st = re.compile(
    r"sc.{1,5}st.{1,3}prevention.{1,2}of.{1,2}atrocities|sc.{1,5}st.{1,3}p.{1,2}o.{1,2}a",
    re.IGNORECASE,
)
wild_life = re.compile(r"wild.{0,2}life.{0,3}protection", re.IGNORECASE)
recovery = re.compile(r"41[134]", re.IGNORECASE)

tag_matchers = [
    (firearms, "Firearms"),
    (narcotics, "Narcotics"),
    (murder, "Murder"),
    (rape, "Rape"),
    (gang_rape, "gang-rape"),
    (dacoity, "Dacoity"),
    (theft, "Theft"),
    (dowry_death, "Dowry Death"),
    (immoral_trafficking, "Immoral Trafficking"),
    (trafficking, "Trafficking"),
    (sedition, "sedition"),
    (waging_war, "Waging War against state"),
    (harbouring, "Harbouring"),
    (communal_provocation, "communal provocation"),
    (adulteration, "adulteration"),
    (abetment_suicide, "Abetment to Suicide"),
    (culpable_homicide, "Culpable Homicide"),
    (kidnapping, "Kidnapping"),
    (abduction, "Abduction"),
    (attempt_murder, "ATTEMPT TO MURDER"),
    (ransom, "Ransom"),
    (compel_marriage, "Compel Marriage"),
    (importation, "Importation"),
    (minor, "Minor"),
    (prostitution, "Prostitution"),
    (extortion, "Extortion"),
    (robbery, "Robbery"),
    (preparation_dacoity, "Preparation for Dacoity"),
    (criminal_breach_trust, "Criminal Breach of Trust"),
    (misappropriation, "Misappropriation"),
    (cheating, "Cheating"),
    (forgery, "Forgery"),
    (ficn, "FICN"),
    (outraging_modesty, "Outraging Modesty"),
    (acid_attack, "Acid Attack"),
    (conspiracy, "Criminal Conspiracy"),
    (carnal_intercourse, "Carnal Intercourse"),
    (drugging, "Drugging"),
    (foreigners_act, "Foreigners Act"),
    (gambling_act, "Gambling Act"),
    (pocso, "POCSO Act"),
    (sc_st, "SC & ST (POA) Act"),
    (wild_life, "Wildlife Act"),
    (recovery, "Recovery"),
]


def add_classification_to_crime(crime, classification):
    tag = Tag.nodes.get_or_none(name=classification)
    if not tag:
        tag = Tag(name=classification, uuid=uuid.uuid4()).save()
    if not crime.tags.is_connected(tag):
        crime.tags.connect(tag)


@app.task
def add_classifications_task(crime_uuid):
    crime = Crime.nodes.get_or_none(uuid=crime_uuid)
    sections = crime.sections
    for regex, tag in tag_matchers:
        if re.search(regex, sections):
            add_classification_to_crime(crime, tag)


@app.task(task_soft_time_limit=100)
def create_crimes_from_cns_row(crime):
    ps_id = crime["ps_id"]
    case_no = crime["case_no"]
    case_date = crime["case_date"]
    case_date = parse(case_date).date()
    sections = crime["sections"]
    gist = crime["gist"]
    gist = gist.replace('"', "'")
    year = str(case_date.year)[2:]
    classifications = crime["tags"]
    # crime_uuid = None
    # failed_gist = None
    ps = BackendPoliceStation.nodes.get_or_none(police_stationId=ps_id)
    if ps:
        query = """
          MATCH (ps:PoliceStation)
          WHERE id(ps) = $ps_id
          MERGE (crime:Crime {case_no: $case_no, year: $year, police_station_id:$police_station_id})
          ON CREATE
          SET
          crime.case_date =  $case_date,
          crime.sections = $sections,
          crime.gist = $gist,
          crime.uuid = apoc.create.uuid()
          ON MATCH
          SET
          crime.gist = $gist
          MERGE (ps)<-[:BELONGS_TO_PS]-(crime)
          RETURN crime
          """
        params = {
            "ps_id": ps.id,
            "case_no": case_no,
            "year": year,
            "case_date": case_date,
            "sections": sections,
            "gist": gist,
            "police_station_id": ps_id,
        }
        results, meta = db.cypher_query(query, params=params)
        crime = next(Crime.inflate(row[0]) for row in results)
        crime.save()  # VERY IMPORTANT! UNLESS THIS LINE IS THERE, CALLBACKS ARE NOT TRIGGERED
        tags = [tag.strip() for tag in classifications.split(",")]
        for tag in tags:
            tag_ = Tag.nodes.get_or_none(name=tag)
            if not tag_:
                tag_ = Tag(name=tag).save()
            if not crime.tags.is_connected(tag_):
                crime.tags.connect(tag_)
    # else:
    #   failed_gist = gist
    # return json.dumps({"crime_uuid":crime_uuid,"failed_gist":failed_gist})


@app.task(task_soft_time_limit=3000, ignore_result=True)
def create_crimes_from_cns(cns_id):
    print(f"CNS id is {cns_id}")
    cns = CrimeNewsSheet.objects.get(id=int(cns_id))
    # rejected = ""
    # existing = None
    # cases_added = 0
    # crime_list = []
    path = cns.cns.url
    print(path)
    # raw_data = default_storage.open(path).read()
    raw_data = cns.cns.read()
    raw_data_dict = xmltodict.parse(raw_data)
    group(
        create_crimes_from_cns_row.s(crime_row)
        for crime_row in raw_data_dict["dataroot"]["cns_for_web_upload"]
    )()


@app.task(soft_time_limit=3000)
def generate_daily_report(
    daily_report_police_station_with_distt,
    daily_report_district,
    case_date,
):
    if daily_report_police_station_with_distt != "":
        ps = BackendPoliceStation.nodes.get(
            ps_with_distt=daily_report_police_station_with_distt,
        )
        uuid = ps.uuid
        query = """
        MATCH (n:Stats)-[:STATS]-(crime:Crime {case_date:$case_date})-[:BELONGS_TO_PS]-(ps:PoliceStation {uuid:$uuid})
        RETURN n,crime
        """
        results, meta = db.cypher_query(
            query,
            params={"case_date": case_date, "uuid": uuid},
        )
        if results != []:
            results = [
                (Stats.inflate(row[0]), Crime.inflate(row[1])) for row in results
            ]
            results = [
                (
                    stats.level,
                    stats.classification,
                    ("red" if stats.remarkable else "normal"),
                    str(crime)
                    + "\n"
                    + crime.police_station.single().district.single().name,
                    crime.uuid,
                    crime.criminal_count,
                    crime.gist,
                )
                for (stats, crime) in results
            ]
            results.sort(key=lambda x: x[0])
    elif daily_report_district != "Null":
        uuid = daily_report_district
        query = (
            "MATCH (n:Stats)-[:STATS]-(crime:Crime {case_date:$case_date})"
            "-[:BELONGS_TO_PS]-(ps:PoliceStation)"
            "-[:BELONGS_TO_DISTRICT]-(:District {uuid:$uuid}) "
            "RETURN n,crime"
        )
        results, meta = db.cypher_query(
            query,
            params={"case_date": case_date, "uuid": uuid},
        )
        if results != []:
            results = [
                (Stats.inflate(row[0]), Crime.inflate(row[1])) for row in results
            ]
            results = [
                (
                    stats.level,
                    stats.classification,
                    ("red" if stats.remarkable else "normal"),
                    str(crime)
                    + "\n"
                    + crime.police_station.single().district.single().name,
                    crime.uuid,
                    crime.criminal_count,
                    crime.gist,
                )
                for (stats, crime) in results
            ]
            results.sort(key=lambda x: x[0])
    else:
        today = datetime.date.today()
        lastMonth = today - datetime.timedelta(days=30)
        if case_date < lastMonth.strftime("%Y-%m-%d"):
            query = """
            MATCH (n:Stats)-[:STATS]-(crime:Crime {case_date:$case_date})
            RETURN n,crime
            """
            results, meta = db.cypher_query(query, params={"case_date": case_date})
            if results != []:
                results = [
                    (Stats.inflate(row[0]), Crime.inflate(row[1])) for row in results
                ]
                results = [
                    (
                        stats.level,
                        stats.classification,
                        ("red" if stats.remarkable else "normal"),
                        str(crime)
                        + "\n"
                        + crime.police_station.single().district.single().name,
                        crime.uuid,
                        crime.criminal_count,
                        crime.gist,
                    )
                    for (stats, crime) in results
                ]
                results.sort(key=lambda x: x[0])
        else:
            query = """
                MATCH (crime:Crime {case_date:$case_date})
                RETURN count(crime)
                """
            results, meta = db.cypher_query(query, params={"case_date": case_date})
            count = results[0][0]

            results = cache.get(f"daily_report_{count}_{today.day}")
            if not results:
                query = """
                MATCH (n:Stats)-[:STATS]-(crime:Crime {case_date:$case_date})
                RETURN n,crime
                """
                results, meta = db.cypher_query(query, params={"case_date": case_date})
                if results != []:
                    results = [
                        (Stats.inflate(row[0]), Crime.inflate(row[1]))
                        for row in results
                    ]
                    results = [
                        (
                            stats.level,
                            stats.classification,
                            ("red" if stats.remarkable else "normal"),
                            str(crime)
                            + "\n"
                            + crime.police_station.single().district.single().name,
                            crime.uuid,
                            crime.criminal_count,
                            crime.gist,
                        )
                        for (stats, crime) in results
                    ]
                    results.sort(key=lambda x: x[0])

                cache.set(
                    f"daily_report_{count}_{today.day}",
                    results,
                    2419200,
                )  # expire cache in 28 days
    return results


@app.task
def create_stats_from_crime(uuid):
    crime = Crime.nodes.get(uuid=uuid)
    if crime.stats.all() == []:
        standard_tags = [
            "Firearms",
            "Narcotics",
            "Murder",
            "Rape",
            "gang-rape",
            "Dacoity",
            "Theft",
            "Dowry Death",
            "Immoral Trafficking",
            "Trafficking",
            "sedition",
            "Waging War against state",
            "Harbouring",
            "communal provocation",
            "adulteration",
            "Abetment to Suicide",
            "Culpable Homicide",
            "Kidnapping",
            "abduction",
            "ATTEMPT TO MURDER",
            "ransom",
            "compel marriage",
            "importation",
            "minor",
            "prostitution",
            "Extortion",
            "Robbery",
            "Preparation for dacoity",
            "Criminal Breach of Trust",
            "Misappropriation",
            "Cheating",
            "Forgery",
            "FICN",
            "Outraging Modesty",
            "Acid Attack",
            "CRIMINAL CONSPIRACY",
            "Drugging",
            "Foreigners Act",
            "GAMBLING ACT",
            "POCSO Act.",
            "SC & ST (POA) Act",
            "WILDLIFE ACT",
            "2- wheeler",
            "Recovery",
            "Motor-Cycle",
            "LORRY",
            "Truck",
            "Offences Against Women",
        ]
        query_ps = """
                WITH $tags as tags
                MATCH (ps:PoliceStation {uuid:$ps_uuid})-[:BELONGS_TO_PS]-(crime:Crime)-[:HAS_TAG]-(tag:Tag)
                WHERE tag.name in tags
                and crime.case_date <= $max_date
                and crime.case_date > $min_date
                WITH crime, size(tags) as inputCnt, count(DISTINCT tag) as cnt
                WHERE cnt = inputCnt
                RETURN count(crime)
                """

        query_district = """
                WITH $tags as tags
                MATCH (district:District {uuid:$district_uuid})-[:BELONGS_TO_DISTRICT]-(ps:PoliceStation)-[:BELONGS_TO_PS]-(crime:Crime)-[:HAS_TAG]-(tag:Tag)
                WHERE tag.name in tags
                and crime.case_date <= $max_date
                and crime.case_date > $min_date
                WITH crime, size(tags) as inputCnt, count(DISTINCT tag) as cnt
                WHERE cnt = inputCnt
                RETURN count(crime)
                """

        classification_list = crime.classification_list.split(",")
        head = "Others"
        level = 13
        if ("Firearm" in classification_list) and ("Recovery" in classification_list):
            head = "Firearm Recovery"
            level = 12
        if "FICN" in classification_list:
            head = "FICN"
            level = 11
        if "Narcotics" in classification_list:
            head = "Narcotics"
            level = 10
        if (
            ("Dowry Death" in classification_list)
            or ("Outraging Modesty" in classification_list)
            or ("Offences Against Women" in classification_list)
        ):
            head = "Offence Against Women"
            level = 9
        if (
            ("Cheating" in classification_list)
            or ("Criminal Breach of Trust" in classification_list)
            or ("Misappropriation" in classification_list)
        ):
            head = "Economic Offence"
            level = 8
        if "Theft" in classification_list and (
            "2- wheeler" in classification_list or "Vehicle" in classification_list
        ):
            head = "Vehicle Theft"
            level = 7
        if "Theft" in classification_list:
            head = "Theft"
            level = 6
        if "Burglary" in classification_list:
            head = "Burglary"
            level = 5
        if "Robbery" in classification_list:
            head = "Robbery"
            level = 4
        if "Rape" in classification_list:
            head = "Offence Against Women"
            level = 3
        if "Dacoity" in classification_list:
            head = "Dacoity"
            level = 2
        if "Murder" in classification_list:
            head = "Murder"
            level = 1
        crime_tags = [tag.name for tag in crime.tags.all()]
        comparison_tags = list(set(crime_tags) & set(standard_tags))
        today = crime.case_date.strftime("%Y-%m-%d")
        one_year_ago = crime.case_date.replace(
            crime.case_date.year - 1,
            crime.case_date.month,
            crime.case_date.day,
        ).strftime("%Y-%m-%d")
        two_years_ago = crime.case_date.replace(
            crime.case_date.year - 2,
            crime.case_date.month,
            crime.case_date.day,
        ).strftime("%Y-%m-%d")
        params = {
            "ps_uuid": crime.police_station.single().uuid,
            "tags": comparison_tags,
            "max_date": today,
            "min_date": one_year_ago,
        }
        results, meta = db.cypher_query(query_ps, params=params)
        similar_crimes_last_year_in_ps = results[0][0]
        params = {
            "ps_uuid": crime.police_station.single().uuid,
            "tags": comparison_tags,
            "max_date": one_year_ago,
            "min_date": two_years_ago,
        }
        results, meta = db.cypher_query(query_ps, params=params)
        similar_crimes_year_before_last_in_ps = results[0][0]
        ps_comparison = (
            str(similar_crimes_last_year_in_ps)
            + " / "
            + str(similar_crimes_year_before_last_in_ps)
        )

        params = {
            "district_uuid": crime.police_station.single().district.single().uuid,
            "tags": comparison_tags,
            "max_date": today,
            "min_date": one_year_ago,
        }
        results, meta = db.cypher_query(query_district, params=params)
        similar_crimes_last_year_in_district = results[0][0]
        params = {
            "district_uuid": crime.police_station.single().district.single().uuid,
            "tags": comparison_tags,
            "max_date": one_year_ago,
            "min_date": two_years_ago,
        }
        results, meta = db.cypher_query(query_district, params=params)
        similar_crimes_year_before_last_in_district = results[0][0]

        district_comparison = (
            str(similar_crimes_last_year_in_district)
            + " / "
            + str(similar_crimes_year_before_last_in_district)
        )
        if (
            (
                similar_crimes_year_before_last_in_district != 0
                and similar_crimes_last_year_in_district
                / similar_crimes_year_before_last_in_district
                > 1.2
            )
            or (
                similar_crimes_year_before_last_in_ps != 0
                and similar_crimes_last_year_in_ps
                / similar_crimes_year_before_last_in_ps
                > 1.2
            )
        ) and level in [5, 4, 6, 8, 3, 2, 1]:
            remarkable = True
        else:
            remarkable = False
        stats = Stats(
            level=level,
            classification="( "
            + head
            + " )"
            + "\n"
            + ",".join(comparison_tags)
            + "\n"
            + "\n"
            + "(PS Comparison "
            + "\n"
            + ps_comparison
            + " )"
            + "\n"
            + "(Distt. Comparison "
            + "\n"
            + district_comparison
            + " )",
            remarkable=remarkable,
        ).save()
        crime.stats.connect(stats)


@app.task(task_soft_time_limit=100)
def create_criminal_from_da_row(row):
    first_name = row["FirstName"]
    if first_name:
        first_name = first_name.replace('"', "'")
    last_name = row["LastName"]
    if last_name:
        last_name = last_name.replace('"', "'")
    guardian_first_name = row["GurdianName"]
    if guardian_first_name:
        guardian_first_name = guardian_first_name.replace('"', "'")
    address = row["Address"]
    if address:
        address = address.replace('"', "'")
    address_ps = row["PsID"]
    date_of_arrest = row["Date"]
    date_of_arrest = parse(date_of_arrest).date()
    case_ps_id = row["CasePs_id"]
    case_no = str(int(row["CaseNo"]))
    case_year = row["CaseYear"][-2:]
    ps = BackendPoliceStation.nodes.get_or_none(police_stationId=case_ps_id)
    try:
        crime = ps.crimes.filter(case_no=case_no, year=case_year).first()
        if (first_name, last_name, guardian_first_name) not in [
            (cr[0].first_name, cr[0].last_name, cr[0].guardian_first_name)
            for cr in crime.criminal_list
        ]:
            print(crime)
            criminal = Criminal(
                first_name=first_name,
                last_name=last_name,
                guardian_first_name=guardian_first_name,
                uuid=uuid.uuid4(),
            ).save()
            print(criminal)
            if address:
                address = Address(name=address).save()
                if address_ps:
                    address_ps = BackendPoliceStation.nodes.get_or_none(
                        police_stationId=address_ps,
                    )
                    address.police_station.connect(address_ps)
                criminal.addresses.connect(address)
            involvement_params = {"arrest_date": date_of_arrest}
            crime.criminals.connect(criminal, involvement_params)

    except Exception as e:
        print(e)


@app.task(task_soft_time_limit=3000, ignore_result=True)
def create_criminals_from_da(da_id):
    da = DailyArrest.objects.get(id=int(da_id))
    raw_data = da.cns.read()
    raw_data_dict = xmltodict.parse(raw_data)
    group(
        create_criminal_from_da_row.s(row)
        for row in raw_data_dict["ROOT"]["Arrest_Sitrep"]
    )()


@app.task
def create_vehicles_task(uuid):
    crime = Crime.nodes.get(uuid=uuid)
    gist = crime.gist
    engine_nos = [
        re.sub(non_alpha_numeric, "", engine_no) for engine_no in engine.findall(gist)
    ]
    for engine_no in engine_nos:
        vehicle = Vehicle.nodes.first_or_none(engine_no=engine_no)
        if not vehicle:
            vehicle = Vehicle(engine_no=engine_no).save()
            crime.vehicles.connect(vehicle)
        elif not crime.vehicles.is_connected(vehicle):
            crime.vehicles.connect(vehicle)
            if len(vehicle.crimes) != 1:
                all_crimes = "\n".join([str(crime) for crime in vehicle.crimes])
                for crime in vehicle.crimes.all():
                    try:
                        ps = crime.police_station.single()
                        ps_object = UserPoliceStation.objects.get(
                            ps_with_distt=ps.ps_with_distt
                        )
                        user = User.objects.filter(
                            police_station=ps_object,
                            is_oc=True,
                        ).first()
                        user_email = user.email
                        send_mail(
                            "Vehicle Matched",
                            f"There is a match for {vehicle!s} in \n{all_crimes}",
                            "admin@wbpcrime.info",
                            [user_email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print(e)
    chassis_nos = [
        re.sub(non_alpha_numeric, "", chassis_nos)
        for chassis_nos in chassis.findall(gist)
    ]
    for chassis_no in chassis_nos:
        vehicle = Vehicle.nodes.first_or_none(chassis_no=chassis_no)
        if not vehicle:
            vehicle = Vehicle(chassis_no=chassis_no).save()
            crime.vehicles.connect(vehicle)
        elif not crime.vehicles.is_connected(vehicle):
            crime.vehicles.connect(vehicle)
            if len(vehicle.crimes) != 1:
                all_crimes = "\n".join([str(crime) for crime in vehicle.crimes])
                for crime in vehicle.crimes.all():
                    try:
                        ps = crime.police_station.single()
                        ps_object = UserPoliceStation.objects.get(
                            ps_with_distt=ps.ps_with_distt
                        )
                        user = User.objects.filter(
                            police_station=ps_object,
                            is_oc=True,
                        ).first()
                        user_email = user.email
                        send_mail(
                            "Vehicle Matched",
                            f"There is a match for {vehicle!s} in \n{all_crimes}",
                            "admin@wbpcrime.info",
                            [user_email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print(e)
    registration_nos = [
        re.sub(non_alpha_numeric, "", registration_no)
        for registration_no in reg.findall(gist)
        if len(registration_no) != 10
    ]  # because length 10 could mean a wrong match within chassis number
    for registration_no in registration_nos:
        vehicle = Vehicle.nodes.first_or_none(registration_no=registration_no)
        if not vehicle:
            print("adding vehicle")
            vehicle = Vehicle(registration_no=registration_no).save()
            crime.vehicles.connect(vehicle)
        elif not crime.vehicles.is_connected(vehicle):
            crime.vehicles.connect(vehicle)
            if len(vehicle.crimes) != 1:
                all_crimes = "\n".join([str(crime) for crime in vehicle.crimes])
                for crime in vehicle.crimes.all():
                    try:
                        ps = crime.police_station.single()
                        ps_object = UserPoliceStation.objects.get(
                            ps_with_distt=ps.ps_with_distt
                        )
                        user = User.objects.filter(
                            police_station=ps_object,
                            is_oc=True,
                        ).first()
                        user_email = user.email
                        send_mail(
                            "Vehicle Matched",
                            f"There is a match for  {vehicle!s} in \n{all_crimes}",
                            "admin@wbpcrime.info",
                            [user_email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print(e)


def merge_criminals(one, two):
    one = Criminal.nodes.get(uuid=one)
    two = Criminal.nodes.get(uuid=two)
    for crime in one.crimes.all():
        two.crimes.connect(crime)
    for address in one.addresses.all():
        two.addresses.connect(address)
    for identification_mark in one.identification_marks.all():
        two.identification_marks.connect(identification_mark)
    for image in one.images.all():
        two.images.connect(image)
    for tag in one.tags.all():
        two.tags.connect(tag)
    one.delete()


@app.task
def add(x, y):
    return x + y


# Cron Tasks
@app.task
def clearsessions():
    from django.contrib.sessions.models import Session

    Session.objects.all().delete()


@app.task
def clear_searches():
    AdvancedCrimeSearch.objects.filter(
        Q(keywords__exact="") | Q(keywords__isnull=True),
    ).delete()
    AdvancedCriminalSearch.objects.filter(
        Q(keywords__exact="") | Q(keywords__isnull=True),
    ).delete()
    AdvancedCrimeSearchChart.objects.all().delete()


@app.task
def send_summary_mail():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    now = timezone.now()
    query = """
    MATCH (n:Image)
    RETURN count(n) as count
    """
    results, meta = db.cypher_query(query)
    image_count = results[0][0]
    query = query.replace("Image", "Crime")
    results, meta = db.cypher_query(query)
    crime_count = results[0][0]
    query = query.replace("Crime", "Criminal")
    results, meta = db.cypher_query(query)
    criminal_count = results[0][0]
    query = query.replace("Criminal", "CourtDate")
    results, meta = db.cypher_query(query)
    court_date_count = results[0][0]
    crime_search_count = AdvancedCrimeSearch.objects.count()
    criminal_search_count = AdvancedCriminalSearch.objects.count()
    crime_chart_count = AdvancedCrimeSearchChart.objects.count()
    query = """
        MATCH ()-[n:SIMILAR_CRIMINAL]-()
        RETURN count(n) as count
        """
    results, meta = db.cypher_query(query)
    similar_criminal_count = results[0][0] / 2

    yesterday_image_count = cache.get("image_count")
    yesterday_crime_count = cache.get("crime_count")
    yesterday_criminal_count = cache.get("criminal_count")
    yesterday_court_date_count = cache.get("court_date_count")
    yesterday_similar_criminal_count = cache.get("similar_criminal_count")

    if yesterday_similar_criminal_count:
        crimes_added = crime_count - yesterday_crime_count
        criminals_added = criminal_count - yesterday_criminal_count
        images_added = image_count - yesterday_image_count
        court_dates_added = court_date_count - yesterday_court_date_count
        similar_criminal_added = (
            similar_criminal_count - yesterday_similar_criminal_count
        )
        users = len(
            User.objects.filter(last_login__gte=now - datetime.timedelta(days=1)),
        )
        send_mail(
            f"Activity summary for {yesterday}",
            f"""
                Crimes Added : {crimes_added}
                Criminals Added : {criminals_added}
                Photos Added : {images_added}
                Crime Searches : {crime_search_count}
                Criminal Searches : {criminal_search_count}
                Crime Charts  : {crime_chart_count}
                Similar Criminals Marked : {similar_criminal_added}
                Users Visited : {users}
                Court Dates Added: {court_dates_added}
                """,
            None,
            ["sanjaysingh13@gmail.com"],
            fail_silently=False,
        )

    cache.set("image_count", image_count, None)
    cache.set("crime_count", crime_count, None)
    cache.set("criminal_count", criminal_count, None)
    cache.set("court_date_count", court_date_count, None)
    cache.set("similar_criminal_count", similar_criminal_count, None)


@app.task
def merge_duplicate_cases():
    query = """
    MATCH (c1:Crime), (c2:Crime)
    WHERE c1.case_no = c2.case_no
      AND c1.case_date = c2.case_date
      AND c1.police_station_id = c2.police_station_id
      AND id(c1) > id(c2)
      AND c1 <> c2

    WITH
      CASE WHEN size(c1.gist) >= size(c2.gist) THEN c1 ELSE c2 END AS largerNode,
      CASE WHEN size(c1.gist) >= size(c2.gist) THEN c2 ELSE c1 END AS smallerNode

    CALL apoc.refactor.mergeNodes(
      [largerNode, smallerNode],
      { properties: "discard", mergeRels: true }
    ) YIELD node

    RETURN node;
    """
    results, meta = db.cypher_query(query)


@app.task
def make_similar_criminals():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    query = """
     MATCH (criminal:Criminal)
     WHERE criminal.date_added = $yesterday
     RETURN criminal
    """
    results, meta = db.cypher_query(
        query,
        params={"yesterday": yesterday.strftime("%Y-%m-%d")},
    )
    criminals = [Criminal.inflate(result[0]) for result in results]
    i = 0
    j = 0
    for criminal in criminals:
        try:
            j = j + 1
            if (
                isinstance(criminal.first_name, str)
                and isinstance(criminal.last_name, str)
                and isinstance(criminal.guardian_first_name, str)
            ):
                if (
                    criminal.first_name.replace(" ", "") != ""
                    and criminal.last_name.replace(" ", "") != ""
                    and criminal.guardian_first_name.replace(" ", "") != ""
                ):
                    query = """
                    CALL {
                          CALL db.index.fulltext.queryNodes('first_name', $first_name)
                          YIELD node, score
                          RETURN node, score, 'first_name' as category
                          UNION ALL
                          CALL db.index.fulltext.queryNodes('last_name', $last_name)
                          YIELD node, score
                          RETURN node, score, 'last_name' as category
                          UNION ALL
                          CALL db.index.fulltext.queryNodes('guardian_first_name', $guardian_first_name)
                          YIELD node, score
                          RETURN node, score, 'guardian_first_name' as category
                             }
                            WITH node, sum(score) AS totalScore, size(collect(DISTINCT category)) as categories
                            WITH node, totalScore, categories
                            WHERE categories = 3
                            RETURN node as criminal, totalScore, 'basic' as search LIMIT 3
                            ORDER BY totalScore DESC
                    """
                    results, meta = db.cypher_query(
                        query,
                        params={
                            "first_name": criminal.first_name,
                            "last_name": criminal.last_name,
                            "guardian_first_name": criminal.guardian_first_name,
                        },
                    )
                    if results != []:
                        matching_criminals = [
                            Criminal.inflate(row[0]) for row in results
                        ]
                        for matching_criminal in matching_criminals:
                            if matching_criminal != criminal and (
                                not criminal.similar_criminal.is_connected(
                                    matching_criminal,
                                )
                            ):
                                criminal.similar_criminal.connect(matching_criminal)
                                i = i + 1
                        if i > 500:
                            break
        except Exception as e:
            print(str(e))


# @app.task
# def encode_image(avatar_url, uuid):
#     req = urllib.request.urlopen(avatar_url)
#     arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
#     image = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
#     _, img_encoded = cv2.imencode(".jpeg", image)
#     memory_file_output = io.BytesIO()
#     memory_file_output.write(img_encoded)
#     memory_file_output.seek(0)
#     image = face_recognition.load_image_file(memory_file_output)
#     # Load image and encode with face_recognition
#     image_encoding = face_recognition.face_encodings(image)
#     if len(image_encoding) != 0:
#         image_encoding = image_encoding[0]
#         face_encoding = FaceEncoding(uuid=uuid, embedding=image_encoding)
#         face_encoding.save()


@app.task
def delete_unauthorized_users():
    # Calculate the date one month ago from today in a timezone-aware manner
    one_month_ago = timezone.now() - datetime.timedelta(days=30)

    # Find users who joined more than a month ago and are in the "UNAUTHORIZED" category
    unauthorized_users = User.objects.filter(
        date_joined__lt=one_month_ago,
        category="UNAUTHORIZED",
    )

    # Delete the filtered users
    unauthorized_users.delete()


# @shared_task
# def mul(x, y):
#   return x * y


# @shared_task
# def xsum(numbers):
#   return sum(numbers)


# @shared_task
# def count_widgets():
#     return Widget.objects.count()


# @shared_task
# def rename_widget(widget_id, name):
#     w = Widget.objects.get(id=widget_id)
#     w.name = name
#     w.save()
