from allauth.account.forms import LoginForm
from allauth.account.forms import ResetPasswordForm
from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField

from ccs_docker.users.models import District
from ccs_docker.users.models import PoliceStation


def get_police_stations():
    try:
        stations = [
            (ps.id, ps.ps_with_distt)
            for ps in PoliceStation.objects.all().order_by("ps_with_distt")
        ]
        return [(None, "---")] + stations
    except Exception as e:
        print(f"Error fetching police stations: {e!s}")
        return [("foo", "foo")]


def get_districts():
    try:
        districts = [
            (distt.id, distt.name) for distt in District.objects.all().order_by("name")
        ]
        return [(None, "---")] + districts
    except Exception as e:
        print(f"Error fetching districts: {e!s}")
        return [("bar", "bar")]


User = get_user_model()


class UserChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserCreationForm(admin_forms.UserCreationForm):
    class Meta(admin_forms.UserCreationForm.Meta):
        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class CustomSignupForm(SignupForm):
    name = forms.CharField(max_length=100)
    rank = forms.CharField(max_length=50, label="Rank")
    telephone = forms.CharField(
        max_length=10,
        label="Telephone",
        validators=[
            RegexValidator(
                r"\d{10}",
                message="Telephone number must be 10-digit",
                code="invalid_telephone",
            ),
        ],
    )
    police_station = forms.ChoiceField(
        required=False,
        choices=[],
        label="Police Station",
    )
    district = forms.ChoiceField(required=False, choices=[], label="District")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["police_station"].choices = get_police_stations()
        self.fields["district"].choices = get_districts()

    # def signup(self, request, user):
    #     user.name = self.cleaned_data['name']
    #     user.rank = self.cleaned_data['rank']
    #     user.telephone = self.cleaned_data['telephone']
    #     if self.cleaned_data['police_station']:
    #         user.police_station_id = self.cleaned_data['police_station']
    #     if self.cleaned_data['district']:
    #         user.district_id = self.cleaned_data['district']
    #     user.save()
    #     return user
    def save(self, request):
        user = super().save(request)
        user.name = self.cleaned_data["name"]
        user.rank = self.cleaned_data["rank"]
        user.telephone = self.cleaned_data["telephone"]
        if self.cleaned_data["district"]:
            user.district_id = self.cleaned_data["district"]
        if self.cleaned_data["police_station"]:
            user.police_station_id = self.cleaned_data["police_station"]
            user.district_id = PoliceStation.objects.get(
                id=self.cleaned_data["police_station"],
            ).district_id
        user.save()
        return user


class CustomLoginForm(LoginForm):
    captcha = ReCaptchaField()


class CustomResetPasswordForm(ResetPasswordForm):
    captcha = ReCaptchaField()
