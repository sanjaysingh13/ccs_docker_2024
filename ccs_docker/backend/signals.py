import datetime
import uuid as unique_universal_identifier

from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from neomodel import db

from ccs_docker.backend.models import Crime
from ccs_docker.backend.models import Criminal
from ccs_docker.backend.models import District
from ccs_docker.backend.models import PoliceStation
from ccs_docker.backend.models import User
from ccs_docker.users.models import District as UserDistrict
from ccs_docker.users.models import PoliceStation as UserPoliceStation
from ccs_docker.users.models import User as UserUser

# Removed: from ccs_docker.users.models import User as UserModel
from .tasks import add_classifications_task  # , encode_image
from .tasks import create_stats_from_crime  # , encode_image

# @receiver(post_save, sender=BufferImage)
# def create_image(sender, instance, **kwargs):
#     if instance.criminal_id:
#         if instance.icon:
#             criminal = Criminal.nodes.get(uuid=instance.criminal_id)
#             criminal.icon = instance.avatar_url.url
#             criminal.save()
#         else:
#             image = Image(avatar_url=instance.avatar_url.url).save()
#             criminal = Criminal.nodes.get(uuid=instance.criminal_id)
#             criminal.images.connect(image)
#             print(f"Buffer Image has avatar_url  {instance.avatar_url.url}")
#             print(f"Buffer Image has criminal  {instance.criminal_id}")
#             encode_image.apply_async(
#                 args=[
#                     instance.avatar_url.url,
#                     instance.criminal_id,
#                 ],
#                 countdown=5,
#             )


@receiver(pre_save, sender=Criminal)
def crimeinal_saved_add_date(sender, instance, **kwargs):
    instance.date_added = datetime.date.today()


@receiver(pre_save, sender=Crime)
def crime_saved_add_date(sender, instance, **kwargs):
    instance.created_at = datetime.datetime.now(datetime.UTC)


@receiver(pre_save, sender=Crime)
def crime_created_add_year(sender, instance, **kwargs):
    if instance.case_date:
        instance.year = str(instance.case_date.year)[-2:]


@receiver(post_save, sender=Crime)
def create_vehicles(sender, instance, **kwargs):
    from .tasks import create_vehicles_task

    gist = instance.gist
    if gist:
        create_vehicles_task.apply_async(args=[instance.uuid], countdown=10)


@receiver(post_save, sender=Crime)
def add_classifications(sender, instance, **kwargs):
    add_classifications_task.apply_async(args=[instance.uuid], countdown=5)


@receiver(post_save, sender=Crime)
def add_stats(sender, instance, **kwargs):
    create_stats_from_crime.apply_async(args=[instance.uuid], countdown=10)


# Creating or updating related PoliceStation (District) Node object
# when PoliceStation (District) Model object is created or updated
@receiver(post_save, sender=UserPoliceStation)
def ps_created(sender, instance, **kwargs):
    name = instance.name
    uuid = str(unique_universal_identifier.uuid4())
    police_stationId = instance.police_stationId
    ps_with_distt = instance.ps_with_distt
    latitude = instance.latitude
    longitude = instance.longitude
    address = instance.address
    officer_in_charge = instance.officer_in_charge
    office_telephone = instance.office_telephone
    telephones = instance.telephones
    emails = instance.emails
    district = str(instance.district.name)
    query = """
  MERGE (ps:PoliceStation {police_stationId:$police_stationId})
  ON MATCH
  SET ps.location = point({latitude:$latitude, longitude:$longitude, crs:'wgs-84'}),
  ps.name = $name,
  ps.ps_with_distt = $ps_with_distt,
  ps.address = $address,
  ps.officer_in_charge = $officer_in_charge,
  ps.office_telephone= $office_telephone,
  ps.telephones = $telephones,
  ps.emails= $emails
  ON CREATE
  SET ps.uuid = $uuid,
  ps.location = point({latitude:$latitude, longitude:$longitude, crs:'wgs-84'}),
  ps.name = $name,
  ps.ps_with_distt = $ps_with_distt,
  ps.address = $address,
  ps.officer_in_charge = $officer_in_charge,
  ps.office_telephone= $office_telephone,
  ps.telephones = $telephones,
  ps.emails= $emails
  RETURN ps
  """
    params = {
        "name": name,
        "uuid": uuid,
        "police_stationId": police_stationId,
        "ps_with_distt": ps_with_distt,
        "address": address,
        "officer_in_charge": officer_in_charge,
        "office_telephone": office_telephone,
        "telephones": telephones,
        "emails": emails,
        "longitude": longitude,
        "latitude": latitude,
    }
    results, meta = db.cypher_query(query, params=params)
    ps = next(PoliceStation.inflate(row[0]) for row in results)
    district = District.nodes.get_or_none(name=district)
    if district:
        ps.district.connect(district)


@receiver(post_save, sender=UserDistrict)
def district_created(sender, instance, **kwargs):
    name = instance.name
    uuid = str(unique_universal_identifier.uuid4())
    district = District.nodes.get_or_none(name=name)
    if not district:
        district = District(name=name, uuid=uuid).save()


# Creating or updating related User Node object when User Model object is created or updated
@receiver(post_save, sender=UserUser)
def user_changed(sender, instance, **kwargs):
    username = instance.username
    name = instance.name
    email = instance.email
    rank = instance.rank
    category = instance.category
    if instance.district:
        print(f"district is: {instance.district.name}")
        district = str(instance.district.name)
    else:
        district = None
    if instance.police_station:
        print(f"ps is: {instance.police_station.ps_with_distt}")
        police_station = str(instance.police_station.ps_with_distt)
        if instance.police_station.district:
            UserUser.objects.filter(id=instance.id).update(
                district=instance.police_station.district,
            )
            # instance.district = instance.police_station.district
            district = str(instance.police_station.district.name)
    else:
        police_station = None
    is_oc = instance.is_oc
    is_sp_or_cp = instance.is_sp_or_cp
    query = """
  MERGE (user:User {email:$email})
  SET
  user.username= $username,
  user.name = $name,
  user.rank = $rank,
  user.category = $category
  RETURN user
  """
    params = {
        "email": email,
        "name": name,
        "username": username,
        "rank": rank,
        "category": category,
    }
    results, meta = db.cypher_query(query, params=params)
    try:
        user = next(User.inflate(row[0]) for row in results)
        if police_station:
            ps = PoliceStation.nodes.get(ps_with_distt=police_station)
            user.police_station.replace(ps)
            # change existing o/cs labels
            if is_oc:
                # Enable him to log in admin site
                UserUser.objects.filter(username=username).update(is_staff=True)
                query = """
                MATCH (user:User:Officer_In_Charge)-[:BELONGS_TO_PS]-(ps:PoliceStation {ps_with_distt:$ps_with_distt})
                RETURN user
                """
                params = {"ps_with_distt": police_station}
                results, meta = db.cypher_query(query, params=params)
                if results != []:
                    existing_oc = next(User.inflate(row[0]) for row in results)
                    if existing_oc != instance:
                        query = """
                            MATCH (user:User {email:$existing_oc_email})
                            MATCH (user2:User {email:$email})
                            REMOVE user:Officer_In_Charge

                            SET user2:Officer_In_Charge
                            RETURN user,user2
                        """
                        params = {
                            "existing_oc_email": existing_oc.email,
                            "email": email,
                        }
                        results, meta = db.cypher_query(query, params=params)
                        # also change the models
                        UserUser.objects.filter(
                            police_station=instance.police_station,
                            is_oc=True,
                        ).exclude(email=email).update(is_oc=False, is_staff=False)
                else:
                    query = """
                            MATCH (user:User {email:$email})
                            SET user:Officer_In_Charge
                            RETURN user
                        """
                    params = {"email": email}
                    results, meta = db.cypher_query(query, params=params)

        if district:
            distt = District.nodes.get(name=district)
            user.district.connect(distt)
            if is_sp_or_cp:
                query = """
                MATCH (user:User:SP_OR_CP)-[:BELONGS_TO_DISTRICT]-(distt:District {name:$district})
                RETURN user
                """
                params = {"district": district}
                results, meta = db.cypher_query(query, params=params)
                if results != []:
                    existing_sp_or_cp = next(User.inflate(row[0]) for row in results)
                    if existing_sp_or_cp != instance:
                        query = """
                            MATCH (user:User {email:$existing_sp_or_cp_email})
                            MATCH (user2:User {email:$email})
                            REMOVE user:SP_OR_CP
                            SET user2:SP_OR_CP
                            RETURN user2
                        """
                        params = {
                            "existing_sp_or_cp_email": existing_sp_or_cp.email,
                            "email": email,
                        }
                        results, meta = db.cypher_query(query, params=params)
                        # also change the models
                        # all_sps_cps = (
                        #     us.objects.filter(
                        #         district=instance.district, is_sp_or_cp=True
                        #     )
                        #     .exclude(email=email)
                        #     .update(is_sp_or_cp=False)
                        # )
                else:
                    query = """
                            MATCH (user:User {email:$email})
                            SET user:SP_OR_CP
                            RETURN user
                        """
                    params = {"email": email}
                    results, meta = db.cypher_query(query, params=params)
            if not police_station:
                UserUser.objects.filter(username=username).update(is_oc=False)
    except Exception as e:
        print(str(e))


@receiver(post_migrate)
def import_police_stations_districts(sender, **kwargs):
    call_command("import_police_stations_districts")
