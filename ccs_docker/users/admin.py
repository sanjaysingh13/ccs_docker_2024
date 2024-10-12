from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from ccs_docker.users.forms import UserCreationForm

from .models import District
from .models import PoliceStation

User = get_user_model()


# user_permissions.add(permission, permission, ...) groups.set([group_list])
@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    def has_add_permission(self, request, obj=None):
        return request.user.category == "ADMIN" and request.user.category != "CID_ADMIN"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()  # type: Set[str]

        if not is_superuser:
            disabled_fields |= {
                "is_superuser",
                "user_permissions",
            }
        if not is_superuser and obj is not None and obj == request.user:
            disabled_fields |= {
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            }
        if request.user.category != "ADMIN" or request.user.category == "CID_ADMIN":
            disabled_fields |= {
                "is_staff",
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.category == "DISTRICT_ADMIN":
            if db_field.name == "police_station":
                kwargs["queryset"] = PoliceStation.objects.filter(
                    district=request.user.district,
                ).order_by("name")
            if db_field.name == "district":
                kwargs["queryset"] = District.objects.filter(
                    name=request.user.district.name,
                )
        elif request.user.category in ("CID_ADMIN", "ADMIN"):
            if db_field.name == "police_station":
                kwargs["queryset"] = PoliceStation.objects.all().order_by("name")
            if db_field.name == "district":
                kwargs["queryset"] = District.objects.all().order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["choices"] = (
                ("UNAUTHORIZED", "Unauthorized"),
                ("PS_ADMIN", "PS_Admin"),
                ("VIEWER", "Viewer"),
            )
            if request.user.category == "DISTRICT_ADMIN":
                kwargs["choices"] = kwargs["choices"]
            if request.user.category == "CID_ADMIN":
                kwargs["choices"] += (("DISTRICT_ADMIN", "District_Admin"),)
            if request.user.is_superuser:
                kwargs["choices"] += (
                    ("DISTRICT_ADMIN", "District_Admin"),
                    ("CID_ADMIN", "CID_Admin"),
                    ("ADMIN", "Admin"),
                )
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.category == "CID_ADMIN":
            return qs.exclude(category="ADMIN")
        if request.user.category == "DISTRICT_ADMIN":
            return qs.filter(district=request.user.district)
        return qs.none()  # Return an empty queryset for other user categories

    add_form = UserCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "category",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "user_permissions",
                    "police_station",
                    "is_oc",
                    "district",
                    "is_sp_or_cp",
                    "rank",
                    "telephone",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "name", "email", "district"]
    search_fields = ["username"]


@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):
    fields = (
        "police_stationId",
        "name",
        "latitude",
        "longitude",
        "address",
        "officer_in_charge",
        "office_telephone",
        "telephones",
        "emails",
        "district",
    )
    list_display = ["name", "district"]
    search_fields = ["name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.category == "CID_ADMIN":
            return qs
        if request.user.category == "DISTRICT_ADMIN":
            return qs.filter(district=request.user.district)
        if request.user.category == "PS_ADMIN":
            return qs.filter(id=request.user.police_station.id)
        return qs.none()  # Return an empty queryset for other user categories

    def get_form(self, request, obj=None, **kwargs):
        # form = UserChangeForm
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()  # type: Set[str]

        if not (is_superuser or request.user.category == "CID_ADMIN"):
            disabled_fields |= {
                "police_stationId",
                "name",
            }
        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    fields = ("name",)
