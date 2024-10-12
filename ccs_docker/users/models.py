from django.contrib.auth.models import AbstractUser
from django.db.models import SET_NULL
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import FloatField
from django.db.models import ForeignKey
from django.db.models import Model
from django.db.models import TextChoices
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(Model):
    created = DateTimeField(auto_now_add=True)
    modified = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class District(TimeStampedModel):
    name = CharField(_("Name of District"), max_length=250)

    def __str__(self):
        return self.name


class PoliceStation(TimeStampedModel):
    police_stationId = CharField(_("Legacy Id"), max_length=50)
    name = CharField(_("Name of PS"), max_length=50)
    ps_with_distt = CharField(
        _("Full Name of PS"),
        blank=True,
        max_length=250,
    )
    latitude = FloatField(_("Latitude of PS"), blank=True, null=True)
    longitude = FloatField(_("Longitude of PS"), blank=True, null=True)
    address = CharField(_("Address of PS"), blank=True, max_length=250)
    officer_in_charge = CharField(_("O/C of PS"), blank=True, max_length=250)
    office_telephone = CharField(
        _("Office Number of PS"),
        blank=True,
        max_length=250,
    )
    telephones = CharField(
        _("Telephone Numbers of PS"),
        blank=True,
        max_length=250,
    )
    emails = CharField(_("Email ID of PS"), blank=True, max_length=250)
    district = ForeignKey(District, blank=True, null=True, on_delete=SET_NULL)

    def __str__(self):
        return self.ps_with_distt

    def save(self, *args, **kwargs):
        if self.district_id:
            self.ps_with_distt = f"{self.name} : {self.district.name}"
        else:
            self.ps_with_distt = self.name
        super().save(*args, **kwargs)


class User(AbstractUser):
    """Default user for Crime Criminal Search."""

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    class Categories(TextChoices):
        UNAUTHORIZED = "UNAUTHORIZED", "Unauthorized"
        VIEWER = "VIEWER", "Viewer"
        PS_ADMIN = "PS_ADMIN", "PS_Admin"
        DISTRICT_ADMIN = "DISTRICT_ADMIN", "District_Admin"
        CID_ADMIN = "CID_ADMIN", "CID_Admin"
        ADMIN = "ADMIN", "Admin"

    base_category = Categories.UNAUTHORIZED
    category = CharField(
        "Category",
        max_length=50,
        choices=Categories.choices,
        default=Categories.UNAUTHORIZED,
    )
    police_station = ForeignKey(
        PoliceStation,
        blank=True,
        null=True,
        on_delete=SET_NULL,
    )
    district = ForeignKey(District, blank=True, null=True, on_delete=SET_NULL)
    is_oc = BooleanField(null=True)
    is_sp_or_cp = BooleanField(null=True)
    # class PoliceStation(TextChoices):
    #     for ps in POLICE_STATIONS:
    #         uuid = ps[0],ps[1]
    # police_station = CharField(
    #     "PoliceStation", max_length=50,
    #     choices=PoliceStation.choices)
    # class District(TextChoices):
    #     UNAUTHORIZED = "UNAUTHORIZED", "Unauthorized"
    #     VIEWER = "VIEWER", "Viewer"
    #     DISTRICT_ADMIN = "DISTRICT_ADMIN", "District_Admin"
    #     CID_ADMIN = "CID_ADMIN","CID_Admin"
    #     ADMIN = "ADMIN","Admin"
    # district = CharField(
    #     "District", max_length=50,
    #     choices=District.choices)
    rank = CharField(_("Rank of User"), blank=True, max_length=50)
    telephone = CharField(_("Cellphone of User"), blank=True, max_length=10)

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    # users = RelationshipFrom('User', 'BELONGS_TO_PS')


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
