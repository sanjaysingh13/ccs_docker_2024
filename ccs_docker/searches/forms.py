# from django.forms import ModelForm
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django import forms
from django.core.validators import RegexValidator

from ccs_docker.backend.models import District

DISTRICTS = [
    (district.uuid, district.name) for district in District.nodes.order_by("name")
]
DISTRICTS.insert(0, ("Null", "Select a District"))

YEARS = [
    (str(n).rjust(2, "0"), str(n).rjust(2, "0"))
    for n in range(datetime.now(ZoneInfo("Asia/Kolkata")).year - 1999)
]
YEARS.insert(0, ("", "Select a year"))

FULL_TEXT_SEARCH_TYPE = [
    (
        0,
        "Strict - fastest (when you are sure of the exact spelling of word e.g. Kolkata)",
    ),
    (
        1,
        "Partial word - slow (when you are searching for words "
        "within words e.g. gold will also return results for golden, "
        "marigold etc. )",
    ),
    (
        2,
        "Fuzzy - slowest (Will return all approximate matches e.g. Manappuram will also return for Mannapuram)",
    ),
]


class CrimeSearchForm(forms.Form):
    police_station_with_distt = forms.CharField(
        required=False,
        label="Police Station",
        max_length=100,
    )
    case_no = forms.CharField(
        label="Case Number",
        widget=forms.TextInput(),
        required=False,
    )
    case_date = forms.DateField(required=False)
    case_year = forms.ChoiceField(choices=YEARS, required=False)
    advanced_search_crime = forms.BooleanField(label="Advanced Search", required=False)
    districts = forms.ChoiceField(choices=DISTRICTS, required=False)
    keywords = forms.CharField(
        label="keywords",
        widget=forms.TextInput(attrs={"placeholder": "Muthoot"}),
        required=False,
        max_length=100,
        validators=[
            RegexValidator("^((?!AND).)*$", message="Cannot contain 'AND' "),
            RegexValidator("^((?!NOT).)*$", message="Cannot contain 'NOT'"),
        ],
    )
    full_text_search_type = forms.IntegerField(
        label="Keyword Search Type",
        widget=forms.RadioSelect(choices=FULL_TEXT_SEARCH_TYPE),
    )

    tags = forms.CharField(
        label="Tags",
        widget=forms.TextInput(attrs={"placeholder": "2-wheeler,theft"}),
        required=False,
        max_length=50,
    )
    search_any_tags = forms.BooleanField(required=False)
    min_date = forms.DateField(required=False)
    max_date = forms.DateField(required=False)
    ps_list = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(
                    "police_station_with_distt",
                    css_class="form-group col-md-5 mb-0",
                ),
                Column("case_no", css_class="form-group col-md-3 mb-0"),
                Column("case_date", css_class="form-group col-md-3 mb-0"),
                Column("case_year", css_class="form-group col-md-1 mb-0"),
                css_class="basic-search-fields",
            ),
            Field(
                "advanced_search_crime",
                wrapper_class="custom-switch custom-control",
                show_all_fields="show_all_fields",
            ),
            HTML(
                """
                <div class="ui-widget advanced-search-fields">
                <h4> Select Police Stations.  </h4>
                <select class="form-select" aria-label="Default select example", id="police_station_id">
                <option value=""></option>
                </select>
                <div class="panel panel-default">
                <div class="panel-heading">
                <h3 class="panel-title">Selected PSs appear here</h3>
                </div>
                <div class="panel-body">
                <p id ="psquery"></p>
                </div>
                </div>
                </div>""",
            ),
            Div(
                Row(
                    Column("districts", css_class="form-group col-md-3 mb-0"),
                    Column("keywords", css_class="form-group col-md-4 mb-0"),
                    Column(
                        "full_text_search_type",
                        css_class="form-group col-md-5 mb-0",
                    ),
                    Field("ps_list", type="hidden"),
                ),
                Row(
                    Column("tags", css_class="form-group col-md-4 mb-0"),
                    Column("search_any_tags", css_class="form-group col-md-2 mb-0"),
                    Column("min_date", css_class="form-group col-md-3 mb-0"),
                    Column("max_date", css_class="form-group col-md-3 mb-0"),
                ),
                css_class="advanced-search-fields ",
            ),
        )
        self.helper.form_id = "id-exampleForm"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        if not cleaned_data.get("advanced_search_crime"):
            if (
                cleaned_data.get("police_station_with_distt", "") == ""
                or cleaned_data.get("case_no", "") == ""
                or (
                    not cleaned_data.get("case_date", "")
                    and cleaned_data.get("case_year", "") == ""
                )
            ):
                msg = "PS, case number,case date or case year required "
                messages.append(msg)
            if cleaned_data.get("case_no", "") != "" and (
                not cleaned_data.get("case_no", "").isdigit()
            ):
                msg_ = "Case number has to be just a number (without year)"
                messages.append(msg_)
        elif (
            (cleaned_data.get("keywords", "") == "")
            and (cleaned_data.get("tags", "") == "")
            and (cleaned_data.get("districts", "") == "Null")
            and (cleaned_data.get("keywords", "") == "")
            and (cleaned_data.get("tags", "") == "")
            and (cleaned_data.get("min_date", "") is None)
            and (cleaned_data.get("max_date", "") is None)
            and (cleaned_data.get("ps_list", "") == "")
        ):
            msg_1 = "You didn't enter any search."
            messages.append(msg_1)
        if messages != []:
            raise forms.ValidationError(messages)

        return cleaned_data


class CriminalSearchForm(forms.Form):
    first_name = forms.CharField(
        label="First name",
        widget=forms.TextInput(),
        required=False,
        max_length=50,
    )
    last_name = forms.CharField(
        label="Last name",
        widget=forms.TextInput(),
        required=False,
        max_length=50,
    )
    guardian_first_name = forms.CharField(
        label="Guardian name",
        widget=forms.TextInput(),
        required=False,
        max_length=50,
    )
    aliases = forms.CharField(
        label="Alias",
        widget=forms.TextInput(),
        required=False,
        max_length=50,
    )
    exact_name_search = forms.BooleanField(
        label="I know the exact name/alias",
        required=False,
    )
    address = forms.CharField(
        label="Address",
        widget=forms.TextInput(),
        required=False,
        max_length=50,
    )
    id_mark = forms.CharField(
        label="Identification Mark",
        widget=forms.TextInput(),
        required=False,
        max_length=50,
    )
    advanced_search = forms.BooleanField(label="Advanced Search", required=False)
    districts = forms.ChoiceField(choices=DISTRICTS, required=False)
    keywords = forms.CharField(
        label="keywords",
        widget=forms.TextInput(attrs={"placeholder": "Muthoot"}),
        required=False,
        max_length=100,
        validators=[
            RegexValidator("^((?!AND).)*$", message="Cannot contain 'AND' "),
            RegexValidator("^((?!NOT).)*$", message="Cannot contain 'NOT'"),
        ],
    )
    full_text_search_type = forms.IntegerField(
        label="Keyword Search Type",
        widget=forms.RadioSelect(choices=FULL_TEXT_SEARCH_TYPE),
    )

    tags = forms.CharField(
        label="Tags",
        widget=forms.TextInput(attrs={"placeholder": "2-wheeler,theft"}),
        required=False,
        max_length=50,
    )
    search_any_tags = forms.BooleanField(required=False)
    min_date = forms.DateField(required=False)
    max_date = forms.DateField(required=False)
    ps_list = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                HTML(
                    """
                <div >
                </br>
                <h6> Basic and Advanced Search for Criminals</h6>

                </div>""",
                ),
                Row(
                    Column("first_name", css_class="form-group col-md-3 mb-0"),
                    Column("last_name", css_class="form-group col-md-3 mb-0"),
                    Column("aliases", css_class="form-group col-md-1 mb-0"),
                    Column("exact_name_search", css_class="form-group col-md-1 mb-0"),
                    Column("guardian_first_name", css_class="form-group col-md-3 mb-0"),
                ),
                Row(
                    Column("address", css_class="form-group col-md-8 mb-0"),
                    Column("id_mark", css_class="form-group col-md-4 mb-0"),
                ),
            ),
            Field(
                "advanced_search",
                wrapper_class="custom-switch custom-control",
                show_all_fields="show_all_fields",
            ),
            HTML(
                """
                <div class="ui-widget advanced-search-fields">
                <h4> Select Police Stations.  </h4>
                <select class="form-select" aria-label="Default select example", id="police_station_id">
                <option value=""></option>
                </select>
                <div class="panel panel-default">
                <div class="panel-heading">
                <h3 class="panel-title">Selected PSs appear here</h3>
                </div>
                <div class="panel-body">
                <p id ="psquery"></p>
                </div>
                </div>
                </div>""",
            ),
            Div(
                Row(
                    Column("districts", css_class="form-group col-md-3 mb-0"),
                    Column("keywords", css_class="form-group col-md-4 mb-0"),
                    Column(
                        "full_text_search_type",
                        css_class="form-group col-md-5 mb-0",
                    ),
                    Field("ps_list", type="hidden"),
                ),
                Row(
                    Column("tags", css_class="form-group col-md-4 mb-0"),
                    Column("search_any_tags", css_class="form-group col-md-2 mb-0"),
                    Column("min_date", css_class="form-group col-md-3 mb-0"),
                    Column("max_date", css_class="form-group col-md-3 mb-0"),
                ),
                css_class="advanced-search-fields ",
            ),
        )
        self.helper.form_class = "blueForms"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        if (
            (cleaned_data.get("keywords", "") == "")
            and (cleaned_data.get("tags", "") == "")
            and (cleaned_data.get("districts", "") == "Null")
            and (cleaned_data.get("keywords", "") == "")
            and (cleaned_data.get("tags", "") == "")
            and (cleaned_data.get("min_date", "") is None)
            and (cleaned_data.get("max_date", "") is None)
            and (cleaned_data.get("ps_list", "") == "")
            and (cleaned_data.get("first_name", "") == "")
            and (cleaned_data.get("last_name", "") == "")
            and (cleaned_data.get("guardian_first_name", "") == "")
            and (cleaned_data.get("aliases", "") == "")
            and (cleaned_data.get("address", "") == "")
            and (cleaned_data.get("id_mark", "") == "")
        ):
            msg_1 = "You didn't enter any search."
            messages.append(msg_1)
            raise forms.ValidationError(messages)

        return cleaned_data
