import re

from crime_criminal_search.backend.models import PoliceStation
from django.conf import settings
from django.contrib.gis.geoip2 import GeoIP2
from django.shortcuts import render

mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN


def police_stations(request):
    g = GeoIP2()
    try:
        ip = request.META.get("REMOTE_ADDR", None)
        location = list(g.lat_lon(ip))
    except Exception as e:
        print(str(e))
        ip = "122.163.1.196"
        location = list(g.lat_lon(ip))
    # ip = "122.163.1.196" # comment in production

    police_stations = [
        (
            ps.location,
            ps.ps_with_distt,
            ps.address,
            ps.officer_in_charge,
            ps.office_telephone,
            ps.emails,
        )
        for ps in PoliceStation.nodes.all()
        if ps.location
    ]
    police_stations.sort(key=lambda x: x[1])
    police_stations = [
        (
            re.findall(r"\d*\.\d*", location)[0],
            re.findall(r"\d*\.\d*", location)[1],
            name,
            address,
            oc,
            tel,
            email,
        )
        for (location, name, address, oc, tel, email) in police_stations
    ]
    police_stations = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                "popup": f"""<h3>{name}</h3>
                                    <p>{address}</p>
                                    <p>O.C.: {oc}</p>
                                    <p>Tel: {tel}</p>
                                    <p>Email: {email} </p>""",
                "properties": {"phoneFormatted": tel, "name": name},
            }
            for (lat, lon, name, address, oc, tel, email) in police_stations
        ],
    }
    return render(
        request,
        "maps/police_stations.html",
        {
            "mapbox_access_token": mapbox_access_token,
            "ip": ip,
            "location": location,
            "police_stations_json": police_stations,
        },
    )
