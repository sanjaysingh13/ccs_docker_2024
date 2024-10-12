# from django.forms import ModelForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django import forms

from ccs_docker.searches.forms import CrimeSearchForm

CRIME_TYPE = [(0, "Property"), (1, "Murder")]


class TransCrimePS(forms.Form):
    police_station_with_distt = forms.CharField(
        required=False,
        label="Police Station",
        max_length=100,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                """
                <div >
                </br>
                <h6> <strong>PSs from where criminals come to commit crime in target PS</strong></h6>
                <p>Select target PS</p>
                </div>""",
            ),
            Div(
                Row(
                    Column(
                        "police_station_with_distt",
                        css_class="form-group col-md-4 mb-0",
                    ),
                ),
                Submit("search", "Get Source PS chart", css_class="button white"),
            ),
        )
        self.helper.form_id = "trans_crime_PS_form"
        self.helper.form_method = "post"

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        if cleaned_data.get("police_station_with_distt", "") == "":
            msg = "Please select target PS "
            messages.append(msg)
        if messages != []:
            raise forms.ValidationError(messages)
        return cleaned_data


class CrimeSearchChartForm(CrimeSearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove the fields not needed for this form
        fields_to_remove = [
            "police_station_with_distt",
            "case_no",
            "case_date",
            "case_year",
            "advanced_search_crime",
        ]
        for field_name in fields_to_remove:
            if field_name in self.fields:
                self.fields.pop(field_name)

        # Adjust the layout to not include the removed fields
        self.helper.layout = Layout(
            # Define the layout here excluding the removed fields
            # For example:
            Div(
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
                css_class="advanced-search-fields",
            ),
        )

    def clean(self):
        cleaned_data = self.cleaned_data
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
        ):
            msg_1 = "You didn't enter any search."
            messages.append(msg_1)
        if messages != []:
            raise forms.ValidationError(messages)

        return cleaned_data
