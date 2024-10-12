import logging
import uuid as unique_universal_identifier
from contextlib import suppress

# import face_recognition
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect
from django.views.generic.detail import DetailView
from neomodel import db

from ccs_docker.backend.models import Address
from ccs_docker.backend.models import BufferImage
from ccs_docker.backend.models import Court
from ccs_docker.backend.models import Crime
from ccs_docker.backend.models import Criminal
from ccs_docker.backend.models import IdentificationMark
from ccs_docker.backend.models import Image
from ccs_docker.backend.models import Judge
from ccs_docker.backend.models import PoliceStation
from ccs_docker.backend.models import Tag
from ccs_docker.backend.models import Vehicle
from ccs_docker.backend.models import Witness

from .forms import AddressFormSet
from .forms import AddressFormSetHelper
from .forms import CalendarForm
from .forms import CrimeFinalReportForm
from .forms import CrimeForm
from .forms import CrimeFormSet
from .forms import CrimeFormSetHelper
from .forms import CrimeSubjudiceForm
from .forms import CriminalFinalFormFormSet
from .forms import CriminalFinalFormFormSetHelper
from .forms import CriminalForm
from .forms import CriminalFormSet
from .forms import CriminalFormSetHelper
from .forms import DailyReportForm
from .forms import ImageFieldForm
from .forms import StfForm
from .forms import VehicleSearchForm
from .forms import WitnessFormSet
from .forms import WitnessFormSetHelper
from .forms import WitnessFormSetHelperUnderscored
from .nodeutils import Calendar
from .nodeutils import check_privileged_rights
from .nodeutils import resize_image
from .nodeutils import vehicle_search_query
from .tasks import generate_daily_report

logger = logging.getLogger(__name__)


# from .tasks import criminal_crime_record
def criminal_crime_record(unique_id):
    query = """
    MATCH (criminal:Criminal {uuid:$uuid})
CALL apoc.path.subgraphAll(criminal, {
relationshipFilter: "INVOLVED_IN",
maxLevel: 2
})
YIELD nodes, relationships
WITH nodes,relationships
UNWIND nodes as node
WITH node,relationships
CALL apoc.case([
    labels(node)[0] = "Crime",
  'WITH node MATCH (ps:PoliceStation)--(node) RETURN {label:ps.name + " " + node.case_no + "/"+node.year, title:ps.name + " P.S. C/No. " + node.case_no + " dated "+coalesce(node.case_date , node.year) + " u/s " + coalesce(node.sections, "Not Given") , id:node.uuid, group:labels(node)[0]} AS node',
  labels(node)[0] = "Criminal",
  'WITH node OPTIONAL MATCH (node)--(add:Address)  RETURN {label:coalesce(node.first_name , "")+ " " + coalesce(node.last_name , ""), title:" s/o "+coalesce(node.guardian_first_name , "") + " r/o " + coalesce(add.name , ""), id:node.uuid, group:labels(node)[0]} AS node LIMIT 1'
  ],

  "",{node:node})
YIELD value
WITH [node in collect(value)| node.node] as nodes,
     [rel in relationships | rel {.*, from:startNode(rel).uuid, to:endNode(rel).uuid}] as rels
WITH {nodes:nodes, relationships:rels} as json
RETURN apoc.convert.toJson(json) as crime_record

    """
    results, meta = db.cypher_query(query, params={"uuid": unique_id})
    network = results[0][0]
    return network


class CrimeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    # def dispatch(self, request, *args, **kwargs):
    #     request = check_view_rights(request)
    #     return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["criminal_list"] = self.object.criminal_list
        return context

    permission_required = "users.view_user"
    model = Crime
    template_name = "backend/crime_detail.html"

    def get_object(self, queryset=None):
        return Crime.nodes.get(uuid=self.kwargs.get("uuid"))

        # To get UUID object from uuuid-like string self.object.uuid = uuid.UUID(object.uuid)


@login_required
@permission_required("users.add_user", raise_exception=True)
@cache_page(None)
@csrf_protect
def create_crime_with_criminals(request):
    template_name = "backend/crime_form.html"
    helper = CriminalFormSetHelper()
    if request.method == "GET":
        crimeform = CrimeForm(request.GET or None)
        formset = CriminalFormSet()
    elif request.method == "POST":
        crimeform = CrimeForm(request.POST)
        formset = CriminalFormSet(request.POST)
        if crimeform.is_valid() and formset.is_valid():
            crime_data = crimeform.cleaned_data
            crime_params = {
                key: crime_data[key]
                for key in ["case_no", "case_date", "sections", "gist"]
            }
            year = str(crime_params["case_date"].year)[-2:]
            case_no = crime_params["case_no"]
            case_date = crime_params["case_date"]
            gist = crime_params["gist"]
            sections = crime_params["sections"]
            police_station_with_distt = crime_data["police_station_with_distt"]
            ps = PoliceStation.nodes.get(ps_with_distt=police_station_with_distt)
            police_station_uuid = ps.uuid
            police_station_id = ps.police_stationId
            query = """
      MATCH (ps:PoliceStation {uuid:$police_station_uuid})
      MERGE (crime:Crime {case_no: $case_no, year:$year,police_station_id:$police_station_id})
      ON CREATE
      SET crime.uuid = apoc.create.uuid(),
          crime.case_date = $case_date,
          crime.gist = $gist,
          crime.sections = $sections
      ON MATCH
      SET crime.gist = $gist,
         crime.sections = $sections
      MERGE (crime)-[:BELONGS_TO_PS]->(ps)
      RETURN crime
      """
            results, meta = db.cypher_query(
                query,
                params={
                    "case_no": case_no,
                    "year": year,
                    "case_date": case_date,
                    "gist": gist,
                    "sections": sections,
                    "police_station_uuid": str(police_station_uuid),
                    "police_station_id": police_station_id,
                },
            )
            crime = next(Crime.inflate(row[0]) for row in results)
            crime.save()
            # Tags
            tags = crime_data.get("tags").split(",")
            tags = list(filter(None, tags))
            for tag in tags:
                tag_ = Tag.nodes.get_or_none(name=tag)
                if not tag_:
                    tag_ = Tag(name=tag).save()
                crime.tags.connect(tag_)

            for form in formset:
                if form.is_valid:
                    if form.cleaned_data.get("first_name", ""):
                        criminal_involvement_data = {
                            key: value
                            for key, value in form.cleaned_data.items()
                            if value
                        }
                        criminal_params = {
                            key: value
                            for key, value in criminal_involvement_data.items()
                            if key
                            in [
                                "first_name",
                                "last_name",
                                "guardian_first_name",
                                "aliases",
                            ]
                        }
                        involvement_params = {
                            key: value
                            for key, value in criminal_involvement_data.items()
                            if key
                            in [
                                "fir_named",
                                "suspected",
                                "arrested",
                                "arrest_date",
                                "absconding",
                                "bailed",
                                "bailed_date",
                                "p_a_done",
                                "p_a_date",
                            ]
                        }
                        criminal = Criminal(**criminal_params)
                        criminal.uuid = unique_universal_identifier.uuid4()
                        criminal.save()
                        if "address" in criminal_involvement_data:
                            address = Address(name=criminal_involvement_data["address"])
                            address.uuid = unique_universal_identifier.uuid4()
                            address.save()
                            criminal.addresses.connect(address)
                            if (
                                "address_police_station_with_distt"
                                in criminal_involvement_data
                            ):
                                # if "adress_ps" in criminal_involvement_data:
                                address_ps = PoliceStation.nodes.get(
                                    ps_with_distt=criminal_involvement_data[
                                        "address_police_station_with_distt"
                                    ],
                                )
                                try:
                                    address.police_station.connect(address_ps)
                                except Exception:
                                    logger.exception(
                                        f"Failed to connect address to police station"
                                    )
                        # work on tag
                        crime.criminals.connect(criminal, involvement_params)
            return redirect(crime)
    return render(
        request,
        template_name,
        {
            "crimeform": crimeform,
            "formset": formset,
            "helper": helper,
            "title": "Add Crime",
            "formset_model": "Criminals",
        },
    )


@login_required
@permission_required("users.add_user", raise_exception=True)
def edit_crime_with_criminals(
    request,
    unique_id,
):  # sample crime uuid 06ce13f0-dfe3-4383-8ae1-8b5f41e05b47
    user = request.user
    deletion_power = user.has_perm("users.delete_user")
    template_name = "backend/crime_form.html"
    helper = CriminalFormSetHelper()
    crime = Crime.nodes.first_or_none(uuid=unique_id)
    crime_params = {
        k: crime.__dict__[k]
        for k in ["uuid", "case_no", "case_date", "sections", "gist"]
    }
    crime_params["police_station_with_distt"] = (
        crime.police_station.single().ps_with_distt
    )
    crime_params["tags"] = ",".join([tag.name for tag in crime.tags.all()])
    criminals_with_involvement = [
        (criminal, crime.criminals.relationship(criminal))
        for criminal in crime.criminals
    ]
    criminals_with_involvement_and_addresses = [
        (
            criminal,
            criminal.addresses[0].uuid,
            criminal.addresses[0],
            involvement.id,
            involvement,
        )
        if len(criminal.addresses) != 0
        else (criminal, None, None, involvement.id, involvement)
        for (criminal, involvement) in criminals_with_involvement
    ]
    criminals_with_involvement_and_addresses_ps = [
        (
            criminal,
            address_uuid,
            address,
            address.police_station.single().ps_with_distt,
            involvement_id,
            involvement,
        )
        if (address and len(address.police_station) != 0)
        else (criminal, address_uuid, address, None, involvement_id, involvement)
        for (
            criminal,
            address_uuid,
            address,
            involvement_id,
            involvement,
        ) in criminals_with_involvement_and_addresses
    ]
    criminals_with_involvement_and_addresses_ps = [
        (criminal, address_uuid, address.name, address_ps, involvement_id, involvement)
        if address
        else (criminal, address_uuid, address, address_ps, involvement_id, involvement)
        for (
            criminal,
            address_uuid,
            address,
            address_ps,
            involvement_id,
            involvement,
        ) in criminals_with_involvement_and_addresses_ps
    ]
    criminal_params = [
        {
            "uuid": criminal.uuid,
            "first_name": criminal.first_name,
            "last_name": criminal.last_name,
            "guardian_first_name": criminal.guardian_first_name,
            "address_uuid": address_uuid,
            "address": address,
            "address_police_station_with_distt": address_ps,
            "involvement_id": involvement_id,
            "fir_named": involvement.fir_named,
            "suspected": involvement.suspected,
            "arrested": involvement.arrested,
            "arrest_date": involvement.arrest_date,
            "absconding": involvement.absconding,
            "bailed": involvement.bailed,
            "bailed_date": involvement.bailed_date,
            "p_a_done": involvement.p_a_done,
            "p_a_date": involvement.p_a_date,
        }
        for (
            criminal,
            address_uuid,
            address,
            address_ps,
            involvement_id,
            involvement,
        ) in criminals_with_involvement_and_addresses_ps
    ]
    existing_criminal_uuids = [criminal["uuid"] for criminal in criminal_params]

    if request.method == "GET":
        crimeform = CrimeForm(crime_params)
        formset = CriminalFormSet(initial=criminal_params)
    elif request.method == "POST":
        crimeform = CrimeForm(request.POST, initial=crime_params)
        formset = CriminalFormSet(request.POST, initial=criminal_params)
        criminal_fields = {"first_name", "last_name", "guardian_first_name", "aliases"}
        address_fields = {"address", "address_police_station_with_distt"}
        involvement_fields = {
            "fir_named",
            "suspected",
            "arrested",
            "arrest_date",
            "absconding",
            "bailed",
            "bailed_date",
            "p_a_done",
            "p_a_date",
        }
        if crimeform.is_valid() and formset.is_valid():
            submitted_criminal_uuids = [
                criminal["uuid"]
                for criminal in formset.cleaned_data
                if "uuid" in criminal
            ]
            list_difference = [
                item
                for item in existing_criminal_uuids
                if item not in submitted_criminal_uuids
            ]

            cleaned_data = crimeform.cleaned_data
            crime = Crime.nodes.get(uuid=cleaned_data.get("uuid", ""))
            if crimeform.has_changed():
                changed_data = crimeform.changed_data
                if "police_station_with_distt" in changed_data:
                    changed_data.remove("police_station_with_distt")
                    police_station = PoliceStation.nodes.get(
                        ps_with_distt=cleaned_data.get("police_station_with_distt", ""),
                    )
                    crime.police_station.reconnect(
                        old_node=crime.police_station.single(),
                        new_node=police_station,
                    )
                    crime.police_station_id = police_station.police_stationId
                if "tags" in changed_data:
                    changed_data.remove("tags")
                    tags = cleaned_data.get("tags", "").split(",")
                    tags = list(filter(None, tags))
                    tags = [tag.strip() for tag in tags]
                    for tag in tags:
                        tag_ = Tag.nodes.get_or_none(name=tag)
                        if not tag_:
                            tag_ = Tag(name=tag).save()
                        if not crime.tags.is_connected(tag_):
                            crime.tags.connect(tag_)
                for item in changed_data:
                    crime.__setattr__(item, cleaned_data.get(item, ""))
                crime.save()

            # Criminals
            for form in formset:
                changed_data = set(form.changed_data)
                cleaned_data = form.cleaned_data
                if (
                    cleaned_data.get("first_name", "") != ""
                    or cleaned_data.get("last_name", "") != ""
                    or cleaned_data.get("guardian_first_name", "") != ""
                ):
                    if form.has_changed:
                        # Check if existing criminal
                        if cleaned_data.get("uuid", "") != "":
                            criminal = Criminal.nodes.get(
                                uuid=cleaned_data.get("uuid", ""),
                            )
                            criminal_params = list(changed_data & criminal_fields)
                            if len(criminal_params) != 0:
                                for item in criminal_params:
                                    criminal.__setattr__(
                                        item,
                                        cleaned_data.get(item, ""),
                                    )
                                criminal.save()
                            involvement_params = list(changed_data & involvement_fields)
                            if len(involvement_params) != 0:
                                involvement = crime.criminals.relationship(criminal)
                                for item in involvement_params:
                                    involvement.__setattr__(
                                        item,
                                        cleaned_data.get(item, ""),
                                    )
                                involvement.save()
                        else:
                            criminal_params = {
                                k: cleaned_data[k] for k in criminal_fields
                            }
                            criminal = Criminal(**criminal_params)
                            criminal.uuid = unique_universal_identifier.uuid4()
                            criminal.save()
                            involvement_params = {
                                k: cleaned_data[k] for k in involvement_fields
                            }
                            crime.criminals.connect(criminal, involvement_params)
                        address_params = list(changed_data & address_fields)
                        if len(address_params) != 0:
                            if cleaned_data.get("address_uuid", ""):  # existing address
                                address = Address.nodes.get(
                                    uuid=cleaned_data.get("address_uuid", ""),
                                )
                                if "address" in address_params:
                                    address.name = cleaned_data.get("address", "")
                                    address.save()
                                if (
                                    "address_police_station_with_distt"
                                    in address_params
                                ):
                                    address_ps = PoliceStation.nodes.get(
                                        ps_with_distt=cleaned_data.get(
                                            "address_police_station_with_distt",
                                            "",
                                        ),
                                    )
                                    address.police_station.reconnect(
                                        old_node=address.police_station.single(),
                                        new_node=address_ps,
                                    )
                            else:  # new address
                                address = Address(name=cleaned_data.get("address", ""))
                                address.uuid = unique_universal_identifier.uuid4()
                                address.save()
                                criminal.addresses.connect(address)
                                if (
                                    "address_police_station_with_distt"
                                    in address_params
                                    and cleaned_data.get("address", "")
                                ):
                                    try:
                                        address_ps = PoliceStation.nodes.get(
                                            ps_with_distt=cleaned_data.get(
                                                "address_police_station_with_distt",
                                                "",
                                            ),
                                        )
                                        address.police_station.connect(address_ps)
                                    except Exception:
                                        logger.exception(
                                            "Failed to connect address to police station"
                                        )

            # delete all related data of criminal
            for uuid in list_difference:
                criminal_marked_for_deletion = Criminal.nodes.get(uuid=uuid)
                for address in criminal_marked_for_deletion.addresses.all():
                    address.delete()
                criminal_marked_for_deletion.delete()

            # return redirect('backend:crime-edit', unique_id=unique_id)
            return redirect(crime)
    return render(
        request,
        template_name,
        {
            "crimeform": crimeform,
            "formset": formset,
            "helper": helper,
            "title": "Edit Crime",
            "formset_model": "Criminals",
            "deletion_power": deletion_power,
        },
    )


######################################


@login_required
@permission_required("users.add_user", raise_exception=True)
@cache_page(None)
@csrf_protect  # However, if you use cache decorators on individual views, the CSRF middleware will not yet have been able to set the Vary header or the CSRF cookie, and the response will be cached without either one. In this case, on any views that will require a CSRF token to be inserted you should use the django.views.decorators.csrf.csrf_protect() decorator first:
def create_criminal_with_crimes(request):
    template_name = "backend/criminal_form.html"
    helper = CrimeFormSetHelper()
    addressform_helper = AddressFormSetHelper()
    if request.method == "GET":
        criminalform = CriminalForm(request.GET or None)
        addressform = AddressFormSet(request.GET or None, prefix="address")
        formset = CrimeFormSet()
        imagesform = ImageFieldForm()

    elif request.method == "POST":
        criminalform = CriminalForm(request.POST, request.FILES)
        addressform = AddressFormSet(request.POST, request.FILES, prefix="address")
        formset = CrimeFormSet(request.POST, request.FILES)
        imagesform = ImageFieldForm(request.POST, request.FILES)
        # ######
        # if criminalform.is_valid():
        #     if criminalform.cleaned_data.get("combined_id_mark", ""):
        #         print(f"idm  {criminalform.cleaned_data.get('combined_id_mark', '')}")
        #     else:
        #         print(criminalform.cleaned_data)
        # return HttpResponse("OK")
        ######
        if (
            criminalform.is_valid()
            and imagesform.is_valid()
            and addressform.is_valid()
            and formset.is_valid()
        ):
            criminal_fields = {
                "first_name",
                "last_name",
                "guardian_first_name",
                "aliases",
                "birth_date",
            }
            criminal_params = {k: criminalform.cleaned_data[k] for k in criminal_fields}

            criminal = Criminal(**criminal_params)
            criminal.uuid = unique_universal_identifier.uuid4()
            criminal.save()
            if criminalform.cleaned_data.get("combined_id_mark", ""):
                combined_id_marks = criminalform.cleaned_data.get(
                    "combined_id_mark",
                    "",
                ).split("|")
                for id_mark_text in combined_id_marks:
                    id_mark_obj = IdentificationMark(id_mark=id_mark_text).save()
                    criminal.identification_marks.connect(id_mark_obj)
            files = request.FILES.getlist("avatar_url")
            for f in files:
                buffer_image_600 = BufferImage(criminal_id=criminal.uuid, icon=False)
                resized_image_600 = resize_image(f, 600)
                buffer_image_600.avatar_url.save(
                    f.name,
                    InMemoryUploadedFile(
                        resized_image_600,
                        None,
                        f.name,
                        "image/jpeg",
                        resized_image_600.getbuffer().nbytes,
                        None,
                    ),
                )
                buffer_image_600.save()

                buffer_image_64 = BufferImage(criminal_id=criminal.uuid, icon=True)
                resized_image_64 = resize_image(f, 64)
                buffer_image_64.avatar_url.save(
                    f.name,
                    InMemoryUploadedFile(
                        resized_image_64,
                        None,
                        f.name,
                        "image/jpeg",
                        resized_image_64.getbuffer().nbytes,
                        None,
                    ),
                )
                buffer_image_64.save()
                # image = Image(avatar_url=image.avatar_url.url).save()
                # criminal.images.connect(image)
            for form in addressform:
                if form.is_valid():
                    if form.cleaned_data.get("name", "") != "":
                        address = Address(name=form.cleaned_data.get("name", ""))
                        address.uuid = unique_universal_identifier.uuid4()
                        address.save()
                        if form.cleaned_data.get(
                            "address_police_station_with_distt",
                            "",
                        ):
                            address_ps = PoliceStation.nodes.get(
                                ps_with_distt=form.cleaned_data.get(
                                    "address_police_station_with_distt",
                                    "",
                                ),
                            )
                            address.police_station.connect(address_ps)
                        criminal.addresses.connect(address)
            for form in formset:
                if form.is_valid():
                    if (
                        form.cleaned_data.get("police_station_with_distt", "")
                        and form.cleaned_data.get("case_no", "")
                        and form.cleaned_data.get("case_date", "")
                        and form.cleaned_data.get("sections", "")
                    ):
                        crime_data = form.cleaned_data
                        crime_params = {
                            key: crime_data[key]
                            for key in ["case_no", "case_date", "sections"]
                        }
                        police_station_with_distt = form.cleaned_data.get(
                            "police_station_with_distt",
                            "",
                        )
                        case_date = crime_params.get("case_date", "")
                        year = str(case_date.year)[-2:]
                        ps = PoliceStation.nodes.get(
                            ps_with_distt=police_station_with_distt,
                        )
                        if ps:
                            query = """
                      MATCH (ps:PoliceStation)
                      WHERE ps.uuid = $ps_uuid
                      MERGE (crime:Crime {case_no: $case_no, year: $year, police_station_id:$police_station_id})
                      ON CREATE
                      SET crime.uuid = apoc.create.uuid(),
                      crime.sections = $sections,
                      crime.case_date = $case_date
                      MERGE (ps)<-[:BELONGS_TO_PS]-(crime)
                      RETURN crime
                      """
                            params = {
                                "ps_uuid": str(ps.uuid),
                                "case_no": crime_params.get("case_no", ""),
                                "case_date": case_date,
                                "sections": crime_params.get("sections", ""),
                                "police_station_id": ps.police_stationId,
                                "year": year,
                            }
                            results, meta = db.cypher_query(query, params)
                            crime = next(Crime.inflate(row[0]) for row in results)
                            crime.save()
                            involvement_params = {
                                key: value
                                for key, value in crime_data.items()
                                if key
                                in [
                                    "fir_named",
                                    "suspected",
                                    "arrested",
                                    "arrest_date",
                                    "absconding",
                                    "bailed",
                                    "bailed_date",
                                    "p_a_done",
                                    "p_a_date",
                                ]
                            }
                            if not criminal.crimes.is_connected(crime):
                                criminal.crimes.connect(crime, involvement_params)
                    else:
                        pass
                else:
                    pass
                    # print(f"crime formset errors {form.errors}")
            return redirect("graphs:criminal-detail", uuid=criminal.uuid)

        # return redirect('backend:criminal-create')

    return render(
        request,
        template_name,
        {
            "criminalform": criminalform,
            "imagesform": imagesform,
            "addressform": addressform,
            "addressform_helper": addressform_helper,
            "formset": formset,
            "helper": helper,
        },
    )


@login_required
@permission_required("users.add_user", raise_exception=True)
def edit_criminal_with_crimes(
    request,
    unique_id,
):  # sample crime uuid 06ce13f0-dfe3-4383-8ae1-8b5f41e05b47
    user = request.user
    deletion_power = user.has_perm("users.delete_user")
    template_name = "backend/criminal_form.html"
    helper = CrimeFormSetHelper()
    addressform_helper = AddressFormSetHelper()
    criminal = Criminal.nodes.first_or_none(uuid=unique_id)
    criminal_params = {
        k: criminal.__dict__[k]
        for k in set(criminal.__dict__.keys())
        & {
            "uuid",
            "first_name",
            "last_name",
            "guardian_first_name",
            "aliases",
            "birth_date",
        }
    }
    address_params = [
        (address.uuid, address.name, address)
        for address in criminal.addresses
        if address
    ]
    address_params_with_address_ps = [
        (uuid, name, address.police_station.single().ps_with_distt)
        if address.police_station.single()
        else (uuid, name, None)
        for (uuid, name, address) in address_params
    ]
    address_params = [
        {
            "uuid": uuid,
            "name": name,
            "address_police_station_with_distt": address_police_station_with_distt,
        }
        for (
            uuid,
            name,
            address_police_station_with_distt,
        ) in address_params_with_address_ps
    ]
    crimes_with_involvement = [
        (crime, criminal.crimes.relationship(crime)) for crime in criminal.crimes
    ]

    crime_params = [
        {
            "uuid": crime.uuid,
            "police_station_with_distt": crime.police_station.single().ps_with_distt,
            "case_no": crime.case_no,
            "case_date": crime.case_date,
            "sections": crime.sections,
            "fir_named": involvement.fir_named,
            "suspected": involvement.suspected,
            "arrested": involvement.arrested,
            "arrest_date": involvement.arrest_date,
            "absconding": involvement.absconding,
            "bailed": involvement.bailed,
            "bailed_date": involvement.bailed_date,
            "p_a_done": involvement.p_a_done,
            "p_a_date": involvement.p_a_date,
        }
        for (crime, involvement) in crimes_with_involvement
    ]
    existing_crime_uuids = [crime["uuid"] for crime in crime_params]
    existing_address_uuids = [address["uuid"] for address in address_params]
    if request.method == "GET":
        criminalform = CriminalForm(criminal_params)
        addressform = AddressFormSet(initial=address_params, prefix="address")
        formset = CrimeFormSet(initial=crime_params)
        imagesform = ImageFieldForm()
    elif request.method == "POST":
        criminalform = CriminalForm(request.POST, initial=criminal_params)
        addressform = AddressFormSet(
            request.POST,
            initial=address_params,
            prefix="address",
        )
        formset = CrimeFormSet(request.POST, initial=crime_params)
        imagesform = ImageFieldForm(request.POST, request.FILES)
        crime_fields = {"police_station_with_distt", "case_no", "case_date", "sections"}
        address_fields = {"uuid", "name", "address_police_station_with_distt"}
        involvement_fields = {
            "fir_named",
            "suspected",
            "arrested",
            "arrest_date",
            "absconding",
            "bailed",
            "bailed_date",
            "p_a_done",
            "p_a_date",
        }
        if (
            criminalform.is_valid()
            and imagesform.is_valid()
            and addressform.is_valid()
            and formset.is_valid()
        ):
            submitted_crime_uuids = [
                crime["uuid"] for crime in formset.cleaned_data if "uuid" in crime
            ]
            submitted_address_uuids = [
                address["uuid"]
                for address in addressform.cleaned_data
                if "uuid" in address
            ]
            crime_list_difference = [
                item
                for item in existing_crime_uuids
                if item not in submitted_crime_uuids
            ]
            address_list_difference = [
                item
                for item in existing_address_uuids
                if item not in submitted_address_uuids
            ]
            cleaned_data = criminalform.cleaned_data
            criminal = Criminal.nodes.get(uuid=cleaned_data.get("uuid", ""))
            if criminalform.has_changed():
                changed_data = criminalform.changed_data
                # if "police_station_with_distt" in changed_data:
                #     changed_data.remove('police_station_with_distt')
                #     police_station = PoliceStation.nodes.get(ps_with_distt=cleaned_data.get("police_station_with_distt", ""))
                #     crime.police_station.reconnect(old_node=crime.police_station.single(),new_node=police_station)

                for item in changed_data:
                    criminal.__setattr__(item, cleaned_data.get(item, ""))
                criminal.save()
            if criminalform.cleaned_data.get("combined_id_mark", ""):
                combined_id_marks = criminalform.cleaned_data.get(
                    "combined_id_mark",
                    "",
                ).split("|")
                for id_mark_text in combined_id_marks:
                    id_mark_obj = IdentificationMark(id_mark=id_mark_text).save()
                    criminal.identification_marks.connect(id_mark_obj)

            # Addresses
            for form in addressform:
                if form.has_changed:
                    changed_data = set(form.changed_data)
                    cleaned_data = form.cleaned_data
                    # Check if existing address
                    if cleaned_data.get("uuid", "") != "":
                        address = Address.nodes.get(uuid=cleaned_data.get("uuid", ""))
                        address_params = list(changed_data & address_fields)
                        if "name" in address_params:
                            address.name = cleaned_data.get("name", "")
                            address.save()
                        if "address_police_station_with_distt" in address_params:
                            address_ps = PoliceStation.nodes.get(
                                ps_with_distt=cleaned_data.get(
                                    "address_police_station_with_distt",
                                    "",
                                ),
                            )
                            if address.police_station.single():
                                address.police_station.reconnect(
                                    old_node=address.police_station.single(),
                                    new_node=address_ps,
                                )
                            else:
                                address.police_station.connect(address_ps)
                    elif cleaned_data.get("name", "") != "":
                        address = Address(name=cleaned_data.get("name", ""))

                        address.uuid = unique_universal_identifier.uuid4()
                        address.save()
                        if cleaned_data.get("address_police_station_with_distt", ""):
                            address_ps = PoliceStation.nodes.get(
                                ps_with_distt=cleaned_data.get(
                                    "address_police_station_with_distt",
                                    "",
                                ),
                            )
                            address.police_station.connect(address_ps)
                        criminal.addresses.connect(address)

            # Images
            files = request.FILES.getlist("avatar_url")
            for f in files:
                buffer_image_600 = BufferImage(criminal_id=criminal.uuid, icon=False)
                resized_image_600 = resize_image(f, 600)
                buffer_image_600.avatar_url.save(
                    f.name,
                    InMemoryUploadedFile(
                        resized_image_600,
                        None,
                        f.name,
                        "image/jpeg",
                        resized_image_600.getbuffer().nbytes,
                        None,
                    ),
                )
                buffer_image_600.save()

                buffer_image_64 = BufferImage(criminal_id=criminal.uuid, icon=True)
                resized_image_64 = resize_image(f, 64)
                buffer_image_64.avatar_url.save(
                    f.name,
                    InMemoryUploadedFile(
                        resized_image_64,
                        None,
                        f.name,
                        "image/jpeg",
                        resized_image_64.getbuffer().nbytes,
                        None,
                    ),
                )
                buffer_image_64.save()

                # image = Image(avatar_url=image.avatar_url.url).save()
                # criminal.images.connect(image)
            # Crimes
            for form in formset:
                if form.has_changed:
                    changed_data = set(form.changed_data)
                    cleaned_data = form.cleaned_data
                    if (
                        cleaned_data.get("police_station_with_distt", "") != ""
                        and cleaned_data.get("case_no", "") != ""
                        and cleaned_data.get("case_date", "")
                        and cleaned_data.get("case_date", "") != ""
                        and cleaned_data.get("sections", "") != ""
                    ):
                        # Check if existing crime
                        if cleaned_data.get("uuid", "") != "":
                            crime = Crime.nodes.get(uuid=cleaned_data.get("uuid", ""))
                            crime_params = list(changed_data & crime_fields)
                            if len(crime_params) != 0:
                                try:  # to change the attributes of a crime attached to criminal without violating uniqueness constraint
                                    for item in crime_params:
                                        if item != "police_station_with_distt":
                                            crime.__setattr__(
                                                item,
                                                cleaned_data.get(item, ""),
                                            )
                                    crime.save()
                                except:  # The changes would violate the uniqueness constraint. Find the intended crime and attach to criminal
                                    criminal.crimes.disconnect(
                                        crime,
                                    )  # disconnect existing crime
                                    police_station_id = PoliceStation.nodes.get(
                                        ps_with_distt=cleaned_data.get(
                                            "police_station_with_distt",
                                            "",
                                        ),
                                    ).police_stationId
                                    crime = Crime.nodes.get_or_none(
                                        case_no=cleaned_data.get("case_no", ""),
                                        police_station_id=police_station_id,
                                        case_date=cleaned_data.get("case_date", ""),
                                    )
                                    if crime:
                                        crime.connect(criminal)
                                if "police_station_with_distt" in crime_params:
                                    police_station = PoliceStation.nodes.get(
                                        ps_with_distt=cleaned_data.get(
                                            "police_station_with_distt",
                                            "",
                                        ),
                                    )
                                    try:
                                        crime.police_station_id = (
                                            PoliceStation.police_stationId
                                        )
                                        crime.save()
                                        crime.police_station.reconnect(
                                            old_node=crime.police_station.single(),
                                            new_node=police_station,
                                        )
                                    except:
                                        criminal.crimes.disconnect(crime)
                                        crime = Crime.nodes.get_or_none(
                                            case_no=cleaned_data.get("case_no", ""),
                                            police_station_id=police_station.police_stationId,
                                            case_date=cleaned_data.get("case_date", ""),
                                        )
                                        if crime:
                                            crime.connect(criminal)
                            involvement_params = list(changed_data & involvement_fields)
                            if len(involvement_params) != 0:
                                involvement = criminal.crimes.relationship(crime)
                                for item in involvement_params:
                                    involvement.__setattr__(
                                        item,
                                        cleaned_data.get(item, ""),
                                    )
                                involvement.save()
                        else:
                            crime_params = {
                                k: cleaned_data[k]
                                for k in crime_fields
                                if k in cleaned_data
                            }
                            # Merge if existing
                            case_no = crime_params["case_no"]
                            case_date = crime_params["case_date"]
                            sections = crime_params["sections"]
                            year = str(crime_params["case_date"].year)[-2:]
                            police_station_with_distt = cleaned_data.get(
                                "police_station_with_distt",
                                "",
                            )
                            ps = PoliceStation.nodes.get(
                                ps_with_distt=police_station_with_distt,
                            )
                            police_station_uuid = ps.uuid
                            police_station_id = ps.police_stationId
                            query = """
                              MATCH (ps:PoliceStation {uuid:$police_station_uuid})
                              WITH ps
                              MERGE (crime:Crime {case_no: $case_no, year:$year, police_station_id:$police_station_id})
                              ON CREATE
                              SET crime.uuid = apoc.create.uuid(),
                              crime.case_date = $case_date,
                              crime.sections = $sections
                              ON MATCH
                              SET crime.sections = $sections
                              MERGE (crime)-[:BELONGS_TO_PS]->(ps)
                              RETURN crime
                              """
                            results, meta = db.cypher_query(
                                query,
                                params={
                                    "case_no": case_no,
                                    "year": year,
                                    "case_date": case_date,
                                    "sections": sections,
                                    "police_station_uuid": str(police_station_uuid),
                                    "police_station_id": police_station_id,
                                },
                            )
                            crime = next(Crime.inflate(row[0]) for row in results)
                            crime.save()
                            involvement_params = {
                                k: cleaned_data[k] for k in involvement_fields
                            }
                            criminal.crimes.connect(crime, involvement_params)

            # delete all related data of criminal
            for uuid in crime_list_difference:
                crime_marked_for_deletion = Crime.nodes.get(uuid=uuid)
                crime_marked_for_deletion.delete()
            for uuid in address_list_difference:
                address_marked_for_deletion = Address.nodes.get(uuid=uuid)
                address_marked_for_deletion.delete()

            # return redirect('backend:criminal-edit', unique_id=unique_id)
            return redirect("graphs:criminal-detail", uuid=criminal.uuid)
    return render(
        request,
        template_name,
        {
            "criminalform": criminalform,
            "imagesform": imagesform,
            "addressform": addressform,
            "addressform_helper": addressform_helper,
            "formset": formset,
            "helper": helper,
            "deletion_power": deletion_power,
        },
    )


@login_required
@permission_required("users.add_user", raise_exception=True)
def edit_crime_final_form(request, unique_id):
    template_name = "backend/crime_form.html"
    helper = CriminalFinalFormFormSetHelper()
    crime = Crime.nodes.first_or_none(uuid=unique_id)
    crime_params = {
        k: crime.__dict__[k]
        for k in [
            "uuid",
            "final_form_no",
            "final_form_date",
            "final_form_type",
            "alamat",
            "pr_no",
        ]
    }
    with suppress(Exception):
        crime_params["court"] = crime.court.single().uuid
    with suppress(Exception):
        crime_params["judge"] = crime.judge.single().uuid
    criminals_with_involvement = [
        (criminal, crime.criminals.relationship(criminal))
        for criminal in crime.criminals
    ]
    criminal_params = [
        {
            "uuid": criminal.uuid,
            "chargesheeted": involvement.chargesheeted,
            "evidence": involvement.evidence,
            "copy_serve_date": involvement.copy_serve_date,
            "custodial_trial": involvement.custodial_trial,
            "person": str(criminal),
        }
        for (criminal, involvement) in criminals_with_involvement
    ]
    if request.method == "GET":
        crimeform = CrimeFinalReportForm(crime_params)
        formset = CriminalFinalFormFormSet(initial=criminal_params)
    elif request.method == "POST":
        crimeform = CrimeFinalReportForm(request.POST, initial=crime_params)
        formset = CriminalFinalFormFormSet(request.POST, initial=criminal_params)
        involvement_fields = {
            "chargesheeted",
            "evidence",
            "copy_serve_date",
            "custodial_trial",
        }
        if crimeform.is_valid() and formset.is_valid():
            cleaned_data = crimeform.cleaned_data
            crime = Crime.nodes.get(uuid=cleaned_data.get("uuid", ""))
            if crimeform.has_changed():
                changed_data = crimeform.changed_data
                judge = None
                court = None
                if "judge" in changed_data:
                    changed_data.remove("judge")
                    judge = Judge.nodes.get(uuid=cleaned_data.get("judge", ""))
                if "court" in changed_data:
                    changed_data.remove("court")
                    court = Court.nodes.get(uuid=cleaned_data.get("court", ""))
                for item in changed_data:
                    crime.__setattr__(item, cleaned_data.get(item, ""))
                crime.save()
                if judge:
                    if not crime.judge.single():
                        crime.judge.connect(judge)
                    else:
                        crime.judge.reconnect(
                            old_node=crime.judge.single(),
                            new_node=judge,
                        )
                if court:
                    if not crime.court.single():
                        crime.court.connect(court)
                    else:
                        crime.court.reconnect(
                            old_node=crime.court.single(),
                            new_node=court,
                        )

            # Criminals
            for form in formset:
                changed_data = set(form.changed_data)
                cleaned_data = form.cleaned_data
                if form.has_changed:
                    criminal = Criminal.nodes.get(uuid=cleaned_data.get("uuid", ""))
                    involvement_params = list(changed_data & involvement_fields)
                    involvement = crime.criminals.relationship(criminal)
                    for item in involvement_params:
                        involvement.__setattr__(item, cleaned_data.get(item, ""))
                    involvement.save()
            # return redirect('backend:crime-edit', unique_id=unique_id)
            return redirect(crime)
    return render(
        request,
        template_name,
        {
            "crimeform": crimeform,
            "formset": formset,
            "helper": helper,
            "case": str(crime),
            "title": "Add Final Form",
            "formset_model": "Criminals",
        },
    )


@login_required
@permission_required("users.add_user", raise_exception=True)
def create_subjudice(request, unique_id):
    crime = Crime.nodes.first_or_none(uuid=unique_id)
    request = check_privileged_rights(request, crime.police_station.single().uuid)
    template_name = "backend/crime_form.html"
    helper = WitnessFormSetHelper()
    crime_params = {
        k: crime.__dict__[k]
        for k in [
            "uuid",
            "gr_no",
            "gr_year",
            "st_case_no",
            "commitment_date",
            "charge_framing_date",
            "monitoring",
            "cs_receipt_date",
            "pp",
            "comments_of_superiors",
            "conviction",
        ]
    }
    witness_params = [
        {"uuid": witness.uuid, "particulars": witness.particulars}
        for witness in crime.witnesses
    ]
    existing_witness_uuids = [witness["uuid"] for witness in witness_params]
    if request.method == "GET":
        crimeform = CrimeSubjudiceForm(crime_params)
        formset = WitnessFormSet(initial=witness_params)
    elif request.method == "POST":
        crimeform = CrimeSubjudiceForm(request.POST, initial=witness_params)
        formset = WitnessFormSet(request.POST, initial=witness_params)
        if crimeform.is_valid() and formset.is_valid():
            cleaned_data = crimeform.cleaned_data
            submitted_witness_uuids = [
                witness["uuid"] for witness in formset.cleaned_data if "uuid" in witness
            ]
            list_difference = [
                item
                for item in existing_witness_uuids
                if item not in submitted_witness_uuids
            ]
            crime_data = crimeform.cleaned_data
            for item in crime_data:
                if cleaned_data.get(item, "") != "":
                    crime.__setattr__(item, cleaned_data.get(item, ""))
            crime.save()

            for form in formset:
                # changed_data = set(form.changed_data)
                cleaned_data = form.cleaned_data
                if form.has_changed:
                    if cleaned_data.get("uuid", "") != "":
                        witness = Witness.nodes.get(uuid=cleaned_data.get("uuid", ""))
                        witness.particulars = cleaned_data.get("particulars", "")
                        witness.save()
                    elif cleaned_data.get("particulars", "") != "":
                        witness = Witness(
                            particulars=cleaned_data.get("particulars", ""),
                        )
                        witness.uuid = unique_universal_identifier.uuid4()
                        witness.save()
                        crime.witnesses.connect(witness)
            for uuid in list_difference:
                witness_marked_for_deletion = Witness.nodes.get(uuid=uuid)
                witness_marked_for_deletion.delete()
            return redirect(crime)
    return render(
        request,
        template_name,
        {
            "crimeform": crimeform,
            "formset": formset,
            "helper": helper,
            "title": "Add Subjudice Details",
            "formset_model": "Witnesses",
        },
    )


@login_required
@permission_required("users.add_user", raise_exception=True)
def trial_monitoring(request, unique_id):
    ffs = {
        0: "CS",
        1: "FRT",
        2: "FRMF",
        3: "FRML",
        4: "FRIF",
        5: "Transfer",
        6: "FR Non-cog",
    }
    crime = Crime.nodes.first_or_none(uuid=unique_id)
    request = check_privileged_rights(request, crime.police_station.single().uuid)

    def format_date_for_output(date):
        try:
            return date.strftime("%d,%b,%Y")
        except:
            return date

    template_name = "backend/crime_trial_monitoring.html"
    helper = WitnessFormSetHelperUnderscored()
    # court_date_formset_helper = CourtDateFormSetHelper()
    crime = Crime.nodes.first_or_none(uuid=unique_id)
    judge = crime.judge.single().name if crime.judge else "Not entered"
    court = crime.court.single().name if crime.court else "Not entered"
    try:
        io_ = crime.io.single().name
    except:
        io_ = None
    criminals_with_involvement = [
        (criminal, crime.criminals.relationship(criminal))
        for criminal in crime.criminals
    ]
    chargesheeted_criminals_with_involvement = [
        (criminal, involvement)
        for (criminal, involvement) in criminals_with_involvement
        if involvement.chargesheeted
    ]
    criminals = [
        (
            str(criminal),
            format_date_for_output(involvement.arrest_date),
            involvement.custodial_trial,
            format_date_for_output(involvement.bailed_date),
            format_date_for_output(involvement.p_a_date),
            format_date_for_output(involvement.copy_serve_date),
            involvement.evidence,
        )
        for (criminal, involvement) in chargesheeted_criminals_with_involvement
    ]
    final_form_description = (
        ffs[crime.final_form_type]
        + " No. "
        + crime.final_form_no
        + ", dt. "
        + crime.final_form_date.strftime("%d,%b,%Y")
        + " in Court of Ld. "
        + judge
        + ", "
        + court
        + ("   |   GR No. " + crime.gr_no if crime.gr_no else "")
        + ("/" + crime.gr_year if crime.gr_year else "")
        + ("   |   ST C/No " + crime.st_case_no if crime.st_case_no else "")
    )  # ("   |   ST C/No " + crime.st_case_no if crime.st_case_no else "")
    court_procedure_timeline = (
        (
            "Date of receipt of CS in court: "
            + format_date_for_output(crime.cs_receipt_date)
            if crime.cs_receipt_date
            else ""
        )
        + (
            "      |       Date of commitment: "
            + format_date_for_output(crime.commitment_date)
            if crime.commitment_date
            else ""
        )
        + (
            "      |      Date of charge-framing: "
            + format_date_for_output(crime.charge_framing_date)
            if crime.charge_framing_date
            else ""
        )
    )
    pp_io = ("Public Prosecutor: " + crime.pp if crime.pp else "") + (
        "       |      IO: " + io_ if io_ else ""
    )
    # crime_params = {
    #     k: crime.__dict__[k]
    #     for k in [
    #         "uuid",
    #         "gr_no",
    #         "gr_year",
    #         "st_case_no",
    #         "commitment_date",
    #         "charge_framing_date",
    #         "monitoring",
    #         "cs_receipt_date",
    #         "pp",
    #         "comments_of_superiors",
    #         "conviction",
    #     ]
    # }
    witness_params = [
        {
            "uuid": witness.uuid,
            "particulars": witness.particulars,
            "dates_of_examination": witness.dates_of_examination,
            "gist_of_deposition": witness.gist_of_deposition,
            "favourable": witness.favourable,
        }
        for witness in crime.witnesses
    ]
    court_dates_params = [
        {
            "uuid": court_date.uuid,
            "hearing_date": format_date_for_output(court_date.hearing_date),
            "comment": court_date.comment,
            "next_date": format_date_for_output(court_date.next_date),
            "next_date_for_comment": court_date.next_date_for_comment,
        }
        for court_date in crime.court_dates.order_by("hearing_date")
    ]

    return render(
        request,
        template_name,
        {
            # 'formset': formset,
            "crime": str(crime),
            "crime_uuid": crime.uuid,
            "helper": helper,
            "final_form_description": final_form_description,
            "pp_io": pp_io,
            "court_procedure_timeline": court_procedure_timeline,
            "criminals": criminals,
            "witnesses_json": witness_params,
            "court_dates_json": court_dates_params,
        },
    )


@login_required
@permission_required("users.add_user", raise_exception=True)
def court_date_calendar(
    request,
    unique_id,
    year=None,
    month=None,
):
    current_time = timezone.now()
    year = year or current_time.year
    month = month or current_time.month
    request = check_privileged_rights(request, unique_id)
    cal = Calendar(unique_id, year, month)
    html_cal = cal.formatmonth(withyear=True)
    context = {}
    context["calendar"] = html_cal
    context["prev_month"] = month - 1 if month > 1 else 12
    context["next_month"] = month + 1 if month < 12 else 1
    if 1 < month < 12:
        context["year"] = year
    elif month == 1:
        context["year"] = year - 1
    else:
        context["year"] = year + 1
    context["unique_id"] = unique_id
    return render(request, "backend/calendar.html", context)
    # except Exception as e:
    #   print(f"error is {e}")
    #   district = District.nodes.get(uuid=unique_id)


@login_required
@permission_required("users.add_user", raise_exception=True)
def daily_report(request):
    template_name = "backend/daily_report_form.html"
    if request.method == "GET":
        daily_report_form = DailyReportForm()
    elif request.method == "POST":
        daily_report_form = DailyReportForm(request.POST)
        if daily_report_form.is_valid():
            cleaned_data = daily_report_form.cleaned_data
            case_date = cleaned_data.get("dr_date", "").strftime("%Y-%m-%d")
            daily_report_police_station_with_distt = cleaned_data.get(
                "dr_police_station_with_distt",
                "",
            )
            daily_report_district = cleaned_data.get("dr_districts", "")
            task = generate_daily_report.apply_async(
                args=(
                    daily_report_police_station_with_distt,
                    daily_report_district,
                    case_date,
                ),
            )
            task_id = task.id

            return render(
                request,
                template_name,
                {"daily_report_form": daily_report_form, "task_id": task_id},
            )
    return render(request, template_name, {"daily_report_form": daily_report_form})


def starter(request):
    template_name = "backend/starter.html"
    if request.method == "GET":
        starter_court_date_calendar = CalendarForm(request.GET or None)
        return render(
            request,
            template_name,
            {
                "form": starter_court_date_calendar,
            },
        )
    if request.method == "POST":
        starter_court_date_calendar = CalendarForm(request.POST)
        if starter_court_date_calendar.is_valid():
            cleaned_data = starter_court_date_calendar.cleaned_data
            starter_police_station_with_distt = cleaned_data.get(
                "starter_police_station_with_distt",
                "",
            )
            starter_districts = cleaned_data.get("starter_districts", "")
            if starter_police_station_with_distt != "":
                ps = PoliceStation.nodes.get(
                    ps_with_distt=starter_police_station_with_distt,
                )
                uuid = ps.uuid
            elif starter_districts != "Null":
                uuid = starter_districts
            else:
                return render(
                    request,
                    template_name,
                    {"form": starter_court_date_calendar},
                )
            return redirect("backend:court-date-calendar", unique_id=uuid)


@cache_page(None)
@csrf_protect
def vehicle_search(request):
    template_name = "backend/vehicle_search.html"
    if request.method == "GET":
        form = VehicleSearchForm()
    elif request.method == "POST":
        form = VehicleSearchForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            registration_no = cleaned_data.get("registration_no", "")
            engine_no = cleaned_data.get("engine_no", "")
            chassis_no = cleaned_data.get("chassis_no", "")
            # search_terms = 0
            compiled_query = vehicle_search_query(
                registration_no,
                engine_no,
                chassis_no,
            )[0]
            params = vehicle_search_query(registration_no, engine_no, chassis_no)[1]
            results, meta = db.cypher_query(compiled_query, params=params)
            vehicles = [
                [
                    str(Vehicle.inflate(result[0])),
                    str(Crime.inflate(result[1])),
                    Crime.inflate(result[1]).uuid,
                    Crime.inflate(result[1]).police_station.single().office_telephone,
                ]
                for result in results
            ]

            return render(
                request,
                "backend/vehicle_search_results.html",
                {"vehicles": vehicles},
            )
    return render(request, template_name, {"form": form})


# @login_required
# @permission_required("users.add_user", raise_exception=True)
# def upload_criminal_for_face_match(request):
#     template_name = "backend/criminal_face_search_form.html"
#     if request.method == "GET":
#         imagesform = ImageSearchForm(request.GET or None)
#     elif request.method == "POST":
#         imagesform = ImageSearchForm(request.POST, request.FILES)
#         if imagesform.is_valid():
#             files = request.FILES.getlist("avatar_url")
#             for f in files:
#                 buffer_image_600 = BufferImage(icon=False)
#                 resized_image_600 = resize_image(f, 600)
#                 buffer_image_600.avatar_url.save(
#                     f.name,
#                     InMemoryUploadedFile(
#                         resized_image_600,
#                         None,
#                         f.name,
#                         "image/jpeg",
#                         resized_image_600.getbuffer().nbytes,
#                         None,
#                     ),
#                 )
#                 buffer_image_600.save()
#                 try:
#                     url = buffer_image_600.avatar_url.url
#                     req = urllib.request.urlopen(url)
#                     arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
#                     image = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
#                     _, img_encoded = cv2.imencode(".jpeg", image)
#                     memory_file_output = io.BytesIO()
#                     memory_file_output.write(img_encoded)
#                     memory_file_output.seek(0)
#                     image = face_recognition.load_image_file(memory_file_output)
#                 except:
#                     image = face_recognition.load_image_file(
#                         buffer_image_600.avatar_url.path
#                     )
#                 # Load image and encode with face_recognition
#                 image_encoding = face_recognition.face_encodings(image)
#                 if len(image_encoding) != 0:
#                     test_encoding = image_encoding[0]
#                     similar_faces = FaceEncoding.objects.order_by(
#                         CosineDistance("embedding", test_encoding)
#                     )[:100]

#                     encodings = [fe.embedding for fe in similar_faces]
#                     uuids = [fe.uuid for fe in similar_faces]
#                     all_matches = face_recognition.compare_faces(
#                         encodings, test_encoding, tolerance=0.5
#                     )
#                     probable_matches_encodings = [
#                         encodings[i] for i in np.where(all_matches)[0]
#                     ]
#                     face_distances = face_recognition.face_distance(
#                         probable_matches_encodings, test_encoding
#                     )
#                     result_uuids = [uuids[i] for i in np.where(all_matches)[0]]
#                     uuid_distances = list(zip(result_uuids, face_distances))
#                     sums = defaultdict(int)
#                     counts = defaultdict(int)
#                     for key, value in uuid_distances:
#                         sums[key] += value
#                         counts[key] += 1
#                     uuid_weighted_distances = {
#                         key: sums[key] / counts[key] for key in sums
#                     }
#                     sorted_uuid_distances = dict(
#                         sorted(
#                             uuid_weighted_distances.items(),
#                             key=lambda item: item[1],
#                         )
#                     )

#                     sorted_uuids = list(sorted_uuid_distances.keys())
#                     random_string = unique_universal_identifier.uuid4()
#                     cache.set(random_string, sorted_uuids, 300)
#                     return redirect(
#                         "backend:criminal-matches",
#                         matches=random_string,
#                     )
#                 else:
#                     return render(request, template_name, {"imagesform": imagesform})
#     return render(request, template_name, {"imagesform": imagesform})


# def return_matches_to_missing_found(request):
#     url = request.args.get("url")
#     url = urllib.parse.unquote(url)
#     req = urllib.request.urlopen(url)
#     arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
#     img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
#     _, img_encoded = cv2.imencode(".jpeg", img)
#     memory_file_output = io.BytesIO()
#     memory_file_output.write(img_encoded)
#     memory_file_output.seek(0)
#     image = face_recognition.load_image_file(memory_file_output)
#     image_encoding = face_recognition.face_encodings(image)
#     matched_criminals = None
#     if image_encoding != []:
#         test_encoding = image_encoding[0]
#         similar_faces = FaceEncoding.objects.order_by(
#             CosineDistance("embedding", test_encoding)
#         )[:100]

#         encodings = [fe.embedding for fe in similar_faces]
#         uuids = [fe.uuid for fe in similar_faces]
#         all_matches = face_recognition.compare_faces(
#             encodings, test_encoding, tolerance=0.5
#         )
#         probable_matches_encodings = [encodings[i] for i in np.where(all_matches)[0]]
#         face_distances = face_recognition.face_distance(
#             probable_matches_encodings, test_encoding
#         )
#         result_uuids = [uuids[i] for i in np.where(all_matches)[0]]
#         uuid_distances = list(zip(result_uuids, face_distances))
#         sums = defaultdict(int)
#         counts = defaultdict(int)
#         for key, value in uuid_distances:
#             sums[key] += value
#             counts[key] += 1
#         uuid_weighted_distances = {key: sums[key] / counts[key] for key in sums}
#         sorted_uuid_distances = dict(
#             sorted(
#                 uuid_weighted_distances.items(),
#                 key=lambda item: item[1],
#             )
#         )

#         sorted_uuids = list(sorted_uuid_distances.keys())[:20]
#         query = """MATCH (criminal:Criminal)-[:HAS_IMAGE]-(i:Image)
#                         WHERE criminal.uuid in $matches
#                 OPTIONAL MATCH (criminal)-[:HAS_ADDRESS]-(add:Address)
#                 WITH DISTINCT criminal
#                 RETURN  coalesce(criminal.first_name , "")+ " " + coalesce(criminal.last_name , "") + " s/o "+coalesce(criminal.guardian_first_name , "") + " r/o " + coalesce(collect(add)[0].name , "") as criminal ,criminal.uuid as criminal_id, collect(i)[0].avatar_url as image
#                 """
#         params = {"matches": sorted_uuids}
#         results, meta = db.cypher_query(query, params=params)
#         matched_criminals = results
#         data = {"matched_criminals": matched_criminals}
#     return JsonResponse(data)


@login_required
@permission_required("users.add_user", raise_exception=True)
def criminal_matches(request, matches):
    matches = cache.get(matches)
    template_name = "backend/matched_criminals.html"
    if request.method == "GET":
        context = {}
        query = """MATCH (criminal:Criminal)-[:HAS_IMAGE]-(i:Image)
                    WHERE criminal.uuid in $matches
            OPTIONAL MATCH (criminal)-[:HAS_ADDRESS]-(add:Address)
            WITH
              coalesce(criminal.first_name , "")+ " " + coalesce(criminal.last_name , "") + " s/o "+coalesce(criminal.guardian_first_name , "") + " r/o " + coalesce(collect(add)[0].name , "") as criminal_detail ,criminal.uuid as criminal_id,collect(i)[0].avatar_url as image, criminal
              MATCH (criminal)-[:INVOLVED_IN]->(c:Crime)-[:BELONGS_TO_PS]->(ps:PoliceStation)
              RETURN criminal_detail, criminal_id,   collect(ps.name +  " P.S. C/No. " + c.case_no + "/"+c.year  + " u/s " + c.sections)  AS crimes,image

            """
        params = {"matches": matches}
        results, meta = db.cypher_query(query, params=params)
        matched_criminals = results
        output = []
        for _, criminal in enumerate(matched_criminals):
            crimes = "\n".join(criminal[2]) if criminal[2] != [None] else None
            output.append([criminal[0], criminal[1], crimes, criminal[3]])

        paginator = Paginator(output, 3)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context["matched_criminals"] = page_obj
        return render(request, template_name, context)


def add_stf(request, uuid):
    template_name = "backend/vehicle_search.html"
    context = {}
    if request.method == "GET":
        stfform = StfForm(request.GET or None)
        context["form"] = stfform
        context["header"] = "STF Sharing Detail"
        context["title"] = "Add STF Sharing Details"
    elif request.method == "POST":
        stfform = StfForm(request.POST, request.FILES)
        if stfform.is_valid():
            files = request.FILES.getlist("avatar_url")
            for f in files:
                image = BufferImage(avatar_url=f, icon=False)
                image.save()

                image = Image(
                    avatar_url=image.avatar_url.url.replace(
                        "ccs-django",
                        "ccs-django-uploads",
                    ),
                ).save()
                image_id = image.id
                print(image_id)
                query = """MATCH (crime:Crime {uuid:$uuid})
                MATCH (image:Image)
                WHERE id(image) = $image_id
                MERGE (crime)<-[:INFORMED_BY_STF]-(image)
                """
                params = {"uuid": str(uuid), "image_id": image_id}
                results, meta = db.cypher_query(query, params=params)
                crime = Crime.nodes.first_or_none(uuid=uuid)
                return redirect(crime)
    return render(request, template_name, context)
