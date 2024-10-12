import io
import re
from calendar import HTMLCalendar

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from neomodel import db
from PIL import Image

from .models import CourtDate
from .models import District
from .models import PoliceStation

non_alpha_numeric = re.compile(r"[^0-9a-zA-Z]+")


def resize_image(image, size):
    # Reset the file pointer to the beginning
    image.seek(0)

    # Open the image file
    img = Image.open(io.BytesIO(image.read()))
    img = img.convert("RGB")

    # Calculate the aspect ratio of the original image
    aspect_ratio = img.width / img.height

    # Set the new width and height
    new_width = size
    new_height = int(size / aspect_ratio)

    # Resize the image while maintaining aspect ratio
    img = img.resize((new_width, new_height), Image.ANTIALIAS)

    # Save the resized image
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)

    return img_io


def check_view_rights(request: HttpRequest) -> HttpRequest:
    if request.user.is_staff or request.user.username == "sanjaysingh13":
        request.can_view = True
        return request
    raise PermissionDenied


def check_privileged_rights(request: HttpRequest, unique_id) -> HttpRequest:
    district = District.nodes.get_or_none(uuid=unique_id)
    police_station = PoliceStation.nodes.get_or_none(uuid=unique_id)
    if (
        request.user.category in ["ADMIN", "CID_ADMIN"]
        or (
            district
            and request.user.category == "DISTRICT_ADMIN"
            and request.user.district.name.strip() == district.name.strip()
        )
        or police_station
        and (
            (
                request.user.is_oc
                and request.user.police_station.ps_with_distt.strip()
                == police_station.ps_with_distt.strip()
            )
            or (
                request.user.category == "DISTRICT_ADMIN"
                and request.user.district.name.strip()
                == police_station.district.single().name.strip()
            )
        )
    ):
        request.can_view = True
        return request
    raise PermissionDenied


class Calendar(HTMLCalendar):
    def __init__(self, unique_id, year=None, month=None):
        self.unique_id = unique_id
        self.year = year
        self.month = month
        super().__init__()

    def formatday(self, day, events):
        events_per_day = [c for c in events if c.next_date.day == day]
        d = ""
        for event in events_per_day:
            d += f'<li class="calendar_list"> {event.get_html_url} </li>'
        if day != 0:
            return f"<td><span class='date'>{day}</span><ul> {d} </ul></td>"
        return "<td></td>"

    def formatweek(self, theweek, events):
        week = ""
        for d, _ in theweek:
            week += self.formatday(d, events)
        return f"<tr> {week} </tr>"

    def formatmonth(self, withyear=True):
        try:
            police_station = PoliceStation.nodes.get(uuid=self.unique_id)
            query = """
            MATCH (n:CourtDate)-[:COURT_DATE]-(:Crime)-[:BELONGS_TO_PS]-(ps:PoliceStation)
            WHERE date(n.next_date).year = $year AND date(n.next_date).month = $month AND ps.uuid = $police_station_id
            RETURN n
            """
            results, meta = db.cypher_query(
                query,
                params={
                    "year": self.year,
                    "month": self.month,
                    "police_station_id": police_station.uuid,
                },
            )
            court_dates = [CourtDate.inflate(row[0]) for row in results]
            cal = '<table border="1" cellpadding="20" cellspacing="0"     class="calendar">\n'
            cal += f"{self.formatmonthname(self.year, self.month, withyear=withyear)}\n"
            cal += f"{self.formatweekheader()}\n"
            for week in self.monthdays2calendar(self.year, self.month):
                cal += f"{self.formatweek(week, court_dates)}\n"
            return cal
        except Exception as e:
            print(e)
            district = District.nodes.get(uuid=self.unique_id)
            query = """
            MATCH (n:CourtDate)-[:COURT_DATE]-(:Crime)-[:BELONGS_TO_PS]-(:PoliceStation)-[:BELONGS_TO_DISTRICT]-(district:District)
            WHERE date(n.next_date).year = $year AND date(n.next_date).month = $month AND district.uuid = $district_id
            RETURN n
            """
            results, meta = db.cypher_query(
                query,
                params={
                    "year": self.year,
                    "month": self.month,
                    "district_id": district.uuid,
                },
            )
            court_dates = [CourtDate.inflate(row[0]) for row in results]
            cal = '<table border="0" cellpadding="20" cellspacing="0"     class="calendar">\n'
            cal += f"{self.formatmonthname(self.year, self.month, withyear=withyear)}\n"
            cal += f"{self.formatweekheader()}\n"
            for week in self.monthdays2calendar(self.year, self.month):
                cal += f"{self.formatweek(week, court_dates)}\n"
            return cal


def vehicle_search_query(registration_no, engine_no, chassis_no):
    query = []
    if registration_no != "":
        registration_no = re.sub(non_alpha_numeric, " ", registration_no)
        query.append(
            """CALL db.index.fulltext.queryNodes('registration_no', $registration_no)
    YIELD node, score
    RETURN node, score""",
        )
    if engine_no != "":
        engine_no = re.sub(non_alpha_numeric, " ", engine_no)
        query.append(
            """CALL db.index.fulltext.queryNodes('engine_no', $engine_no)
    YIELD node, score
    RETURN node, score""",
        )
    if chassis_no != "":
        chassis_no = re.sub(non_alpha_numeric, " ", chassis_no)
        query.append(
            """CALL db.index.fulltext.queryNodes('chassis_no', $chassis_no)
    YIELD node, score
    RETURN node, score""",
        )

    compiled_query = """
     UNION ALL
    """.join(
        query,
    )
    compiled_query = (
        """CALL {
  """
        + compiled_query
        + "}"
        + """
    WITH node, sum(score) AS totalScore
    MATCH (node)-[:VEHICLE]-(crime:Crime)
    RETURN node as vehicle,crime,totalScore
    ORDER BY totalScore DESC"""
    )
    params = {
        "registration_no": registration_no,
        "engine_no": engine_no,
        "chassis_no": chassis_no,
    }
    return compiled_query, params
