from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django_neomodel import DjangoNode
from neomodel import BooleanProperty
from neomodel import DateProperty
from neomodel import DateTimeProperty
from neomodel import EmailProperty
from neomodel import FloatProperty
from neomodel import IntegerProperty
from neomodel import Relationship
from neomodel import RelationshipFrom
from neomodel import RelationshipTo
from neomodel import StringProperty
from neomodel import StructuredNode
from neomodel import StructuredRel
from neomodel import UniqueIdProperty
from neomodel import ZeroOrOne
from pgvector.django import IvfflatIndex
from pgvector.django import VectorField


class InvolvementRel(StructuredRel):
    fir_named = BooleanProperty()
    suspected = BooleanProperty()
    arrested = BooleanProperty()
    absconding = BooleanProperty()
    w_a_ref = StringProperty()
    chargesheeted = BooleanProperty()
    convicted = BooleanProperty()
    arrest_date = DateProperty()
    comment = StringProperty()
    bailed = BooleanProperty()
    bailed_date = DateProperty()
    p_a_done = BooleanProperty()
    p_a_date = DateProperty()
    evidence = StringProperty()
    copy_serve_date = StringProperty()
    custodial_trial = BooleanProperty()

    def __str__(self):
        a = f"{'FIR-named ' if self.fir_named else ''}"
        b = f"{'Suspected ' if self.suspected else ''}"
        c = f"{'Arrested ' if self.arrested else ''}"
        d = f"{'D.O.A '+self.arrest_date.strftime('%d,%b,%Y')+' '   if self.arrest_date else ''}"
        e = f"{'Absconding ' if self.absconding else ''}"
        f = f"{'Charge-sheeted ' if self.chargesheeted else ''}"
        g = f"{'Convicted ' if self.convicted else ''}"
        description = a + b + c + d + e + f + g
        return description


class TagRel(StructuredRel):
    context = StringProperty()


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Address(DjangoNode):
    uuid = UniqueIdProperty()
    name = StringProperty()
    criminal = RelationshipFrom("Criminal", "HAS_ADDRESS")
    police_station = Relationship(
        "PoliceStation",
        "BELONGS_TO_PS",
        cardinality=ZeroOrOne,
    )


class ArrestAlert(TimeStampedModel):
    first_name = models.CharField(max_length=50, blank=True, default="")
    last_name = models.CharField(max_length=50, blank=True, default="")
    guardian_name = models.CharField(max_length=50, blank=True, default="")
    address = models.CharField(max_length=50, blank=True, default="")
    user_id = models.IntegerField()
    crime_id = models.IntegerField(null=True)
    stop_alerting = models.BooleanField(null=True)
    matched = models.BooleanField(null=True)
    match_details = models.CharField(max_length=50, blank=True, default="")


class BufferImage(TimeStampedModel):
    avatar_url = models.FileField()
    criminal_id = models.UUIDField(null=True)
    icon = models.BooleanField(null=True)
    # def save(self, *args, **kwargs):
    #     super(BufferImage, self).save(*args, **kwargs)
    #     image = Image(avatar_url=self.avatar_url.url).save()
    #     criminal = Criminal.nodes.get(uuid=self.criminal_id)
    #     criminal.images.connect(image)


class Clue(StructuredNode):
    DISPLAY = {"Public": 0, "Police Officers": 1, "CID": 2}
    uuid = UniqueIdProperty()
    question = StringProperty()
    answer = StringProperty()
    answered = BooleanProperty()
    display_level = IntegerProperty(choices=DISPLAY)
    # crime                = RelationshipFrom('.crime.Crime', 'CLUE')
    police_station = Relationship("PoliceStation", "PS")
    # user = Relationship('User', 'CLUE')


class Court(StructuredNode):
    uuid = UniqueIdProperty()
    name = StringProperty()
    crimes = Relationship("Crime", "BELONGS_TO_COURT")


class CourtDate(StructuredNode):
    uuid = UniqueIdProperty()
    hearing_date = DateProperty()
    comment = StringProperty()
    next_date = DateProperty()
    next_date_for_comment = StringProperty()
    crime = Relationship("Crime", "COURT_DATE")

    # prior_court_date = Relationship('CourtDate', 'PRIOR_COURT_DATE')
    def __str__(self):
        crime = str(self.crime.single())
        return crime

    @property
    def get_html_url(self):
        url = reverse(
            "backend:crime-trial-monitoring",
            args=(self.crime.single().uuid,),
        )
        return f'<a href="{url}">{self!s}</a>'


class Crime(DjangoNode):
    uuid = UniqueIdProperty()
    police_station_id = StringProperty()
    crimeId = IntegerProperty()
    case_no = StringProperty()
    case_date = DateProperty()
    sections = StringProperty()
    gist = StringProperty()
    remarks = StringProperty()
    year = StringProperty()
    final_form_no = StringProperty()
    final_form_date = DateProperty()
    final_form_type = IntegerProperty(
        choices={
            0: "CS",
            1: "FRT",
            2: "FRMF",
            3: "FRML",
            4: "FRIF",
            5: "Transfer",
            6: "FR Non-cog",
        },
    )
    # location         = neomodel.PointProperty(crs='wgs-84')
    alamat = StringProperty()
    pr_no = StringProperty()
    gr_no = StringProperty()
    gr_year = StringProperty()
    st_case_no = StringProperty()
    commitment_date = DateProperty()
    charge_framing_date = DateProperty()
    monitoring = BooleanProperty()
    conviction = BooleanProperty()
    cs_receipt_date = DateProperty()
    pp = StringProperty()
    comments_of_superiors = StringProperty()
    cims = StringProperty()
    location = StringProperty()
    created_at = DateTimeProperty()
    criminals = Relationship("Criminal", "INVOLVED_IN", model=InvolvementRel)  # plural?
    police_station = Relationship(
        "PoliceStation",
        "BELONGS_TO_PS",
        cardinality=ZeroOrOne,
    )
    judge = Relationship("Judge", "BELONGS_TO_JUDGE", cardinality=ZeroOrOne)
    court = Relationship("Court", "BELONGS_TO_COURT", cardinality=ZeroOrOne)
    tags = Relationship("Tag", "HAS_TAG", model=TagRel)
    clues = Relationship("Clue", "CLUE")
    io = Relationship("User", "IS_IO", cardinality=ZeroOrOne)
    vehicles = Relationship("Vehicle", "VEHICLE")
    witnesses = Relationship("Witness", "IS_WITNESS")
    next_court_date = Relationship("CourtDate", "NEXT_COURT_DATE")
    court_dates = Relationship("CourtDate", "COURT_DATE")
    stats = Relationship("Stats", "STATS")

    class Meta:
        app_label = "backend"

    # def save(self, *args, **kwargs):
    #     print("1")
    #     self.year = str(self.case_date.year)[-2:]
    #     print(self.year)
    #     super(Crime, self).save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     from .tasks import create_vehicles
    #     super(Crime, self).save(*args, **kwargs)
    #     create_vehicles.apply_async(args=[self.uuid], countdown=10)

    def get_absolute_url(self):
        return reverse("backend:crime-detail", kwargs={"uuid": self.uuid})

    @property
    def criminal_list(self):
        criminals = self.criminals
        return [
            (criminal, self.criminals.relationship(criminal)) for criminal in criminals
        ]

    @property
    def criminal_count(self):
        criminals = self.criminals
        return len(criminals)

    @property
    def classification_list(self):
        return ",".join([tag.name for tag in self.tags.all()])

    def __str__(self):
        if self.case_date:
            dated = " dated " + self.case_date.strftime("%d,%b,%Y")
        else:
            dated = " of " + str(self.year)
        sections = " u/s " + self.sections if self.sections else ""
        return (
            self.police_station.single().name
            + " P.S.  C/No. "
            + str(self.case_no)
            + dated
            + sections
        )

    @property
    def final_form_description(self):
        ffs = {
            0: "CS",
            1: "FRT",
            2: "FRMF",
            3: "FRML",
            4: "FRIF",
            5: "Transfer",
            6: "FR Non-cog",
        }
        if self.final_form_no:
            if self.final_form_date:
                a = f"{ffs[self.final_form_type]} No. {self.final_form_no!s} ,"
                b = f'dt. {self.final_form_date.strftime("%d,%b,%Y")}'
                return a + b
            return f"{self.final_form_type} No. {self.final_form_no!s}"
        return None


class CrimeNewsSheet(TimeStampedModel):
    cns = models.FileField()
    cns_date = models.DateField()
    processed = models.BooleanField(null=True)
    # updated_at, type: DateTime
    casesuploaded = models.IntegerField(blank=True, null=True)
    crime_list = ArrayField(models.CharField(blank=True, max_length=20), null=True)
    csv = models.FileField(null=True, blank=True)
    rejected = models.CharField(max_length=200, blank=True)
    existing = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.cns.url) + " dated " + self.cns_date.strftime("%d,%b,%Y")

    def save(self, *args, **kwargs):
        from .tasks import create_crimes_from_cns

        super().save(*args, **kwargs)
        create_crimes_from_cns.apply_async(
            args=[self.id],
            countdown=30,
        )  # we need to add delay because task seems to be strangely unable to find model with passed ID.


class Criminal(DjangoNode):
    uuid = UniqueIdProperty()
    criminalId = IntegerProperty()
    first_name = StringProperty()
    last_name = StringProperty()
    guardian_first_name = StringProperty()
    dob = StringProperty()
    comment = StringProperty()
    active = BooleanProperty()
    pid = StringProperty()
    ch_ref = StringProperty()
    ch_photo = BooleanProperty()
    aliases = StringProperty()
    # property :ps_op, type: String
    # property :distt_op, type: String
    relatives = StringProperty()
    # property :sex, type: String

    ir_url = StringProperty()
    ir_text = StringProperty()
    date_added = DateProperty()
    crimes = Relationship("Crime", "INVOLVED_IN", model=InvolvementRel)
    addresses = RelationshipTo("Address", "HAS_ADDRESS")
    identification_marks = RelationshipTo(
        "IdentificationMark",
        "HAS_IDENTIFICATION_MARK",
    )
    images = Relationship("Image", "HAS_IMAGE")
    icon = StringProperty()
    similar_criminal = Relationship("Criminal", "SIMILAR_CRIMINAL")
    tags = Relationship("Tag", "HAS_TAG", model=TagRel)

    def __str__(self):
        person = ""
        if self.first_name:
            person = person + self.first_name
        if self.last_name:
            person = person + " " + self.last_name
        if self.guardian_first_name:
            person = person + " s/o " + self.guardian_first_name
        if self.addresses:
            person = person + " r/o " + self.addresses[0].name
            if self.addresses[0].police_station:
                person = (
                    person + " P.S. " + self.addresses[0].police_station.single().name
                )
        return person

    @property
    def jail_pic(self):
        if self.ch_photo:
            jail_pic = [
                "https://s3.amazonaws.com/crime-criminal-profilepics/"
                + ch
                + "/"
                + self.pid.split(",")[idx]
                + ".jpg"
                for idx, ch in enumerate(self.ch_ref.split(","))
            ]
        else:
            jail_pic = None
        return jail_pic

    @property
    def album(self):
        photo_album = [img.avatar_url for img in self.images]
        # if self.jail_pic:
        #     photo_album = (photo_album + self.jail_pic)
        return photo_album

    @property
    def profile_pic(self):
        if self.images:
            return self.images[0].avatar_url
        return None

    @property
    def crimerecord(self):
        query = """MATCH (criminal) WHERE  id(criminal)= $self
      MATCH (criminal)-[involvement]-(crime:Crime)
      WITH crime,criminal,involvement
      OPTIONAL MATCH (crime)--(co_accused:Criminal)
      WHERE co_accused <> criminal
      RETURN crime, involvement, collect(co_accused.uuid) as co_accuseds
      ORDER BY crime.case_date"""
        results, meta = self.cypher(query)
        criminal_crimes = [
            [Crime.inflate(result[0]), result[1], result[2]] for result in results
        ]
        query = """MATCH (criminal) WHERE  id(criminal)= $self
      MATCH (criminal)--(:Crime)--(co_accused:Criminal)
      RETURN DISTINCT co_accused"""
        results_, meta = self.cypher(query)
        criminal_coaccused = [Criminal.inflate(result[0]) for result in results_]
        criminal_coaccused = [
            [criminal.uuid, str(criminal), idx + 1]
            for idx, criminal in enumerate(criminal_coaccused)
        ]
        criminal_uuids = [c[0] for c in criminal_coaccused]
        # Using 1-based index for uuid list of co-accused
        criminal_crimes = [
            [
                c[0].uuid,
                str(c[0]),
                InvolvementRel.inflate(c[1]),
                ",".join(
                    [
                        str(x)
                        for x in sorted(
                            [criminal_uuids.index(uuid) + 1 for uuid in c[2]],
                        )
                    ],
                ),
            ]
            for c in criminal_crimes
        ]
        return [criminal_crimes, criminal_coaccused]


class CriminalDuplicate(TimeStampedModel):
    STATUS = [
        (0, "Merge_Selected_records"),
        (1, "Not_Duplicate"),
        (2, "Doubtful_But_Possible"),
    ]
    reported_dup = models.CharField(max_length=200, blank=True, default="")
    confirmed_dup = models.CharField(max_length=200, blank=True, default="")
    user_id = models.IntegerField()
    processsed = models.BooleanField(null=True)
    selected_name = models.IntegerField(null=True)
    selected_dob = models.IntegerField(null=True)
    status = models.IntegerField(choices=STATUS)


class DailyArrest(TimeStampedModel):
    da_date = models.DateField()
    cns = models.FileField()
    processed = models.BooleanField(null=True)
    criminals_added = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        from .tasks import create_criminals_from_da

        super().save(*args, **kwargs)
        create_criminals_from_da.apply_async(args=[self.id], countdown=30)


class District(StructuredNode):
    uuid = UniqueIdProperty()
    name = StringProperty()
    state_id = IntegerProperty()
    user_count = FloatProperty()
    police_stations = Relationship("PoliceStation", "BELONGS_TO_DISTRICT")
    users = RelationshipFrom("User", "BELONGS_TO_DISTRICT")


class IdentificationMark(StructuredNode):
    id_mark = StringProperty()
    criminal = RelationshipFrom("Criminal", "HAS_IDENTIFICATION_MARK")


class Image(StructuredNode):
    avatar_url = StringProperty()
    criminal = Relationship("Criminal", "HAS_IMAGE")


class Judge(StructuredNode):
    uuid = UniqueIdProperty()
    name = StringProperty()
    crimes = Relationship("Crime", "BELONGS_TO_JUDGE")


class MergeTags(models.Model):
    first = models.CharField(max_length=200, blank=True, default="")
    second = models.CharField(max_length=200, blank=True, default="")


class PoliceStation(StructuredNode):
    uuid = UniqueIdProperty()
    police_stationId = StringProperty()
    name = StringProperty()
    ps_with_distt = StringProperty()
    location = StringProperty()
    address = StringProperty()
    officer_in_charge = StringProperty()
    office_telephone = StringProperty()
    telephones = StringProperty()
    emails = StringProperty()
    district = Relationship("District", "BELONGS_TO_DISTRICT")
    crimes = RelationshipFrom("Crime", "BELONGS_TO_PS")
    addresses = RelationshipFrom("Address", "BELONGS_TO_PS")
    users = RelationshipFrom("User", "BELONGS_TO_PS")


class Stats(StructuredNode):
    level = IntegerProperty()
    classification = StringProperty()
    remarkable = BooleanProperty()
    crime = Relationship("Crime", "STATS")


class Tag(StructuredNode):
    uuid = UniqueIdProperty()
    name = StringProperty()
    crimes = Relationship("Crime", "HAS_TAG", model=TagRel)


class User(StructuredNode):
    username = StringProperty()
    email = EmailProperty()
    name = StringProperty()
    rank = StringProperty()
    category = StringProperty()
    police_station = Relationship(
        "PoliceStation",
        "BELONGS_TO_PS",
        cardinality=ZeroOrOne,
    )
    district = Relationship("District", "BELONGS_TO_DISTRICT", cardinality=ZeroOrOne)
    crimes = Relationship("Crime", "IS_IO")


# class User(AbstractUser):
#     class Categories(models.TextChoices):
#         UNAUTHORIZED = "UNAUTHORIZED", "Unauthorized"
#         VIEWER = "VIEWER", "Viewer"
#         DISTRICT_ADMIN = "DISTRICT_ADMIN", "District_Admin"
#         CID_ADMIN = "CID_ADMIN","CID_Admin"
#         ADMIN = "ADMIN","Admin"
#     base_category = Categories.UNAUTHORIZED
#     category = models.CharField(
#         "Category", max_length=50,
#         choices=Categories.choices,
#         default=Categories.UNAUTHORIZED)
#     def save(self, *args, **kwargs):
#         # If a new user, set the user's type based off the # base_type property
#         if not self.pk:
#             self.category = self.base_category
#         return super().save(*args, **kwargs)


class Vehicle(StructuredNode):
    registration_no = StringProperty()
    chassis_no = StringProperty()
    engine_no = StringProperty()
    crimes = Relationship("Crime", "VEHICLE")

    def __str__(self):
        vehicle = ""
        if self.registration_no:
            vehicle = vehicle + "Regn No: " + self.registration_no
        if self.engine_no:
            vehicle = vehicle + "\n" + "Engine No.: " + self.engine_no
        if self.chassis_no:
            vehicle = vehicle + "\n" + "Chassis No.: " + self.chassis_no
        return vehicle


class Witness(StructuredNode):
    uuid = UniqueIdProperty()
    particulars = StringProperty()
    dates_of_examination = StringProperty()
    gist_of_deposition = StringProperty()
    favourable = BooleanProperty()
    crime = Relationship("Crime", "IS_WITNESS")


class FaceEncoding(models.Model):
    uuid = models.CharField(max_length=36)
    embedding = VectorField(dimensions=128)

    class Meta:
        indexes = [
            IvfflatIndex(
                name="my_index",
                fields=["embedding"],
                lists=100,
                opclasses=["vector_cosine_ops"],
            ),
        ]
