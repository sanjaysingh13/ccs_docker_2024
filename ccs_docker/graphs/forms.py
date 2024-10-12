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

CRIME_TYPE = [(0, "Property"), (1, "Murder")]


class CrimeCategoriesForm(forms.Form):
    tags = forms.CharField(
        label="Tags",
        widget=forms.TextInput(attrs={"placeholder": "2-wheeler,theft"}),
        required=False,
    )
    network_criminals = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                """
                <div >
                <h5>Select the crime Tags which should be included in network linkages (leave blank for  all cases)</h5>
                </div>""",
            ),
            Div(
                Row(Column("tags", css_class="form-group col-md-10 mb-0")),
                Submit("search", "Get Network", css_class="button white get_network"),
                Row(
                    Column("network_criminals", css_class="form-group col-md-5 mb-0"),
                ),
            ),
            Div(id="criminal_network"),
        )
        self.helper.form_id = "criminal-network-form"
        self.helper.form_class = "blueForms"
        self.helper.form_method = "post"
        # self.helper.add_input(Submit('submit', 'Get Network'))


class CriminalsConnectionForm(forms.Form):
    first_criminal = forms.CharField(label="First Criminal", max_length=100)
    second_criminal = forms.CharField(label="Second Criminal", max_length=100)
    first_criminal_name = forms.CharField(
        label="First Criminal name",
        max_length=100,
        widget=forms.HiddenInput(),
    )
    second_criminal_name = forms.CharField(
        label="Second Criminal name",
        max_length=100,
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                """
                <div >
                </br>
                <h6> Path from one criminal to another</h6>
                <p>You can see if two criminals are connected through intervening crimes and other criminals.</p>
                <p> Copy and paste the IDs of two criminals from their profile pages. </p>
                </div>""",
            ),
            Div(
                Row(
                    Field("first_criminal_name", type="hidden"),
                    Field("second_criminal_name", type="hidden"),
                    Column("first_criminal", css_class="form-group col-md-6 mb-0"),
                    Column("second_criminal", css_class="form-group col-md-6 mb-0"),
                ),
                Submit(
                    "search",
                    "Get Connection",
                    css_class="button white get_connection",
                ),
            ),
            Div(id="criminals_path"),
        )
        self.helper.form_id = "criminals-connection-form"
        self.helper.form_method = "post"


class CriminalPSConnectionForm(forms.Form):
    first_criminal = forms.CharField(label="Criminal", max_length=100)
    police_station_with_distt = forms.CharField(
        required=False,
        label="Police Station",
        max_length=100,
    )
    criminal_name = forms.CharField(
        label="First Criminal name",
        max_length=100,
        widget=forms.HiddenInput(),
    )
    network_criminals_ps = forms.ChoiceField(required=False)
    crime_type = forms.IntegerField(
        label="Crime Type",
        widget=forms.RadioSelect(choices=CRIME_TYPE),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                """
                <div >
                </br>
                <h6> <strong>Likely associates of  a criminal in a PS</strong></h6>
                <h6>(Upto 5 levels, i.e. <strong>(Criminal 1)</strong><--><strong>(Criminal 2)</strong><--><strong>(Criminal 3)</strong><--><strong>(Criminal 4)</strong><--><strong>(Criminal 5)</strong>)

                <p> Copy and paste the ID of the criminal from his profile page. </p>
                </div>""",
            ),
            Div(
                Row(
                    Field("criminal_name", type="hidden"),
                    Column("first_criminal", css_class="form-group col-md-5 mb-0"),
                    Column(
                        "police_station_with_distt",
                        css_class="form-group col-md-4 mb-0",
                    ),
                    Column("crime_type", css_class="form-group col-md-3 mb-0"),
                ),
                Submit(
                    "search",
                    "Get PS Network",
                    css_class="button white get_ps_network",
                ),
                Row(
                    Column(
                        "network_criminals_ps",
                        css_class="form-group col-md-5 mb-0",
                    ),
                ),
            ),
            Div(id="criminals_path"),
        )
        self.helper.form_id = "criminals-connection-form"
        self.helper.form_method = "post"
