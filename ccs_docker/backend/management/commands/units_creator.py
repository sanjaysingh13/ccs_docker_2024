import re

from ccs_docker.backend.models import District as BackendDistrict
from ccs_docker.backend.models import PoliceStation as BackendPoliceStation
from ccs_docker.users.models import District
from ccs_docker.users.models import PoliceStation

PoliceStation.objects.all().delete()
District.objects.all().delete()
for district in BackendDistrict.nodes.all():
    District.objects.create(name=district.name)
for police_station in BackendPoliceStation.nodes.all():
    print(police_station)
    police_station_ = PoliceStation(
        name=police_station.name,
        police_stationId=police_station.police_stationId,
        address=police_station.address,
        officer_in_charge=police_station.officer_in_charge,
        office_telephone=police_station.office_telephone,
        telephones=police_station.telephones,
        emails=police_station.emails,
    )
    if police_station.district.single():
        print(police_station.district.single().name)
        distt = District.objects.filter(name=police_station.district.single().name)
        police_station_.district_id = distt[0].id
    location = police_station.location
    if location:
        print(location)
        police_station_.latitude = float(re.findall(r"[\d\.]+", location)[0])
        police_station_.longitude = float(re.findall(r"[\d\.]+", location)[1])
    police_station_.save()
