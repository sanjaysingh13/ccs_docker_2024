from crispy_forms.bootstrap import FieldWithButtons
from crispy_forms.bootstrap import StrictButton
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

from ccs_docker.backend.models import Court
from ccs_docker.backend.models import District
from ccs_docker.backend.models import Judge

COURTS = [(court.uuid, court.name) for court in Court.nodes.order_by("name")]
JUDGES = [(judge.uuid, judge.name) for judge in Judge.nodes.order_by("name")]

# Fix for C414: Remove unnecessary tuple and list calls
DISTRICTS = [
    (district.uuid, district.name) for district in District.nodes.order_by("name")
]
DISTRICTS.insert(0, ("Null", "Select a District"))


class CriminalWithInvolvementForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    address_uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    involvement_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    first_name = forms.CharField(required=False, label="First name", max_length=100)
    last_name = forms.CharField(required=False, label="Last name", max_length=100)
    guardian_first_name = forms.CharField(
        required=False,
        label="Guardian name",
        max_length=100,
    )
    aliases = forms.CharField(required=False, label="Aliases", max_length=100)
    address = forms.CharField(required=False)
    address_police_station_with_distt = forms.CharField(
        required=False,
        label="Police Station",
        max_length=100,
        validators=[
            RegexValidator(
                r".*:.*",
                message='Your internet is slow. Police Station name must be of form "PS Name : District name"',
                code="invalid_ps",
            ),
        ],
    )
    fir_named = forms.BooleanField(required=False)
    suspected = forms.BooleanField(required=False)

    arrested = forms.BooleanField(required=False)
    arrest_date = forms.DateField(required=False)
    absconding = forms.BooleanField(required=False)
    bailed = forms.BooleanField(required=False)
    bailed_date = forms.DateField(required=False)
    p_a_done = forms.BooleanField(required=False)
    p_a_date = forms.DateField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("first_name", "") or cleaned_data.get("last_name", ""):
            if not (
                cleaned_data.get("first_name", "")
                and cleaned_data.get("last_name", "")
                and cleaned_data.get("guardian_first_name", "")
            ):
                msg = "First, last and Guardian names required"
                raise forms.ValidationError(msg)
        return cleaned_data


CriminalFormSet = forms.formset_factory(CriminalWithInvolvementForm, can_delete=True)


class CriminalFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.form_method = 'post'
        self.layout = Layout(
            Div(
                Row(
                    Field("uuid", type="hidden"),
                    Column("first_name", css_class="form-group col-md-4 mb-0"),
                    Column("last_name", css_class="form-group col-md-4 mb-0"),
                    Column("guardian_first_name", css_class="form-group col-md-4 mb-0"),
                ),
                Row(
                    Field("address_uuid", type="hidden"),
                    Column("aliases", css_class="form-group col-md-2 mb-0"),
                    Column("address", css_class="form-group col-md-7 mb-0"),
                    Column(
                        "address_police_station_with_distt",
                        css_class="form-group col-md-3 mb-0",
                    ),
                ),
                Row(
                    Field("involvement_id", type="hidden"),
                    Column("fir_named", css_class="form-group col-md-2 mb-0"),
                    Column("suspected", css_class="form-group col-md-2 mb-0"),
                    Column("arrested", css_class="form-group col-md-2 mb-0"),
                    Column("arrest_date", css_class="form-group col-md-2 mb-0"),
                    Column("absconding", css_class="form-group col-md-2 mb-0"),
                ),
                Row(
                    Column("bailed", css_class="form-group col-md-2 mb-0"),
                    Column("bailed_date", css_class="form-group col-md-3 mb-0"),
                    Column("p_a_done", css_class="form-group col-md-2 mb-0"),
                    Column("p_a_date", css_class="form-group col-md-3 mb-0"),
                    HTML(
                        """
                    <div class="input-group-append col-md-2">
                <button class="btn btn-success add-form-row">+</button>
            </div>
            """,
                    ),
                ),
                css_class=" form-row-clone spacer",
            ),
        )

        self.form_tag = False


class CrimeForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    police_station_with_distt = forms.CharField(
        label="Police Station",
        max_length=100,
        validators=[
            RegexValidator(
                r".*:.*",
                message='Your internet is slow. Police Station name must be of form "PS Name : District name"',
                code="invalid_ps",
            ),
        ],
    )
    case_no = forms.CharField(label="Case No.", max_length=5)
    case_date = forms.DateField()
    sections = forms.CharField(label="Sections", max_length=200)
    gist = forms.CharField(label="Gist", max_length=30000, widget=forms.Textarea())
    tags = forms.CharField(widget=forms.TextInput(), required=False, max_length=200)

    def clean(self):
        cleaned_data = super().clean()
        messages = []

        if not (
            cleaned_data.get("case_no", "").isdigit()
            and cleaned_data.get("case_no", "")[0] != "0"
        ):
            msg_ = "Case number has to be just a number (without year)"
            messages.append(msg_)
        if messages != []:
            raise forms.ValidationError(messages)
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Field("uuid", type="hidden"),
                Column(
                    "police_station_with_distt",
                    css_class="form-group col-md-6 mb-0",
                ),
                Column("case_no", css_class="form-group col-md-3 mb-0"),
                Column("case_date", css_class="form-group col-md-3 mb-0"),
            ),
            Row(
                Column("sections", css_class="form-group col-md-6 mb-0"),
                Column("tags", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("gist", css_class="form-group col-md-12 mb-0"),
                style="width: 100%;",
            ),
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False
        # self.helper.add_input(Submit('submit', 'Submit'))

        # uuid = UniqueIdProperty()
        # crimeId = IntegerProperty()
        # case_no = IntegerProperty()
        # case_date = DateProperty()
        # sections = StringProperty()
        # gist = StringProperty()
        # remarks = StringProperty()
        # year = StringProperty()
        # final_form_no = StringProperty()
        # final_form_date = DateProperty()
        # final_form_type = StringProperty()
        # # location         = PointProperty(crs='wgs-84')
        # alamat = StringProperty()
        # pr_no = StringProperty()
        # gr_no = StringProperty()
        # gr_year = StringProperty()
        # st_case_no = StringProperty()
        # commitment_date = DateProperty()
        # charge_framing_date = DateProperty()
        # monitoring = BooleanProperty()
        # conviction = BooleanProperty()
        # cs_receipt_date = DateProperty()
        # pp = StringProperty()
        # comments_of_superiors = StringProperty()
        # cs_transit_delay = StringProperty()
        # commitment_delay = IntegerProperty()
        # charge_framing_delay = IntegerProperty()
        # cims = StringProperty()
        # cims_no = StringProperty()


################################################################
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)


class ImageFieldForm(forms.Form):
    avatar_url = MultipleFileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("avatar_url", css_class="form-group col-md-4 mb-0")),
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False


class AddressForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    name = forms.CharField(required=False, label="Address")
    address_police_station_with_distt = forms.CharField(
        required=False,
        label="Police Station",
        max_length=100,
    )

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        # if cleaned_data.get('address_police_station_with_distt', '') not in  POLICE_STATIONS_NAMES + [""]:
        #         msg = 'Please select Police Station name only from given list.'
        #         messages.append(msg)
        if messages != []:
            raise forms.ValidationError(messages)
        return cleaned_data


AddressFormSet = forms.formset_factory(AddressForm, can_delete=True)


class AddressFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.form_method = 'post'
        self.layout = Layout(
            Div(
                Row(
                    Field("uuid", type="hidden"),
                    Column("name", css_class="form-group col-md-6 mb-0"),
                    Column(
                        "address_police_station_with_distt",
                        css_class="form-group col-md-4 mb-0",
                    ),
                    HTML(
                        """
                    <div class="input-group-append col-md-1">
                <button class="btn btn-success add-form_-row">+</button>
            </div>
            """,
                    ),
                ),
                css_class=" form_-row-clone spacer",
            ),
        )
        self.form_tag = False


class CriminalForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    first_name = forms.CharField(label="First name", max_length=100)
    last_name = forms.CharField(label="Last name", max_length=100)
    aliases = forms.CharField(required=False, label="Aliases", max_length=100)
    guardian_first_name = forms.CharField(label="Guardian name", max_length=100)
    birth_date = forms.DateField(required=False)
    id_mark = forms.CharField(required=False, label="Identification Mark")
    combined_id_mark = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Field("uuid", type="hidden"),
                Column("first_name", css_class="form-group col-md-4 mb-0"),
                Column("last_name", css_class="form-group col-md-4 mb-0"),
                Column("aliases", css_class="form-group col-md-4 mb-0"),
            ),
            Row(
                Column("birth_date", css_class="form-group col-md-3 mb-0"),
                Column("guardian_first_name", css_class="form-group col-md-4 mb-0"),
            ),
            Row(
                Field("combined_id_mark", type="hidden"),
                FieldWithButtons(
                    "id_mark",
                    StrictButton("Add", css_class="btn btn-info", id="id_mark_adder"),
                    placeholder="Add one ID mark at a time and press button",
                    css_class="form-group col-md-4 mb-0",
                ),
                HTML(
                    """
                <div class = 'form-group col-md-8 mb-0'>

                    <p> <strong>ID Marks</strong> </p>
                    <h5 id="combined_id_mark"></h5>
                    </div>
            """,
                ),
            ),
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False


class CrimeWithInvolvementForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    police_station_with_distt = forms.CharField(
        required=False,
        label="Police Station",
        max_length=100,
    )
    case_no = forms.CharField(required=False, label="Case No.", max_length=5)
    case_date = forms.DateField(
        required=False,
    )
    sections = forms.CharField(required=False, label="Sections", max_length=200)
    fir_named = forms.BooleanField(required=False)
    suspected = forms.BooleanField(required=False)

    arrested = forms.BooleanField(required=False)
    arrest_date = forms.DateField(required=False)
    absconding = forms.BooleanField(required=False)
    bailed = forms.BooleanField(required=False)
    bailed_date = forms.DateField(required=False)
    p_a_done = forms.BooleanField(required=False)
    p_a_date = forms.DateField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        messages = []
        if (
            cleaned_data.get("police_station_with_distt", "") == ""
            or cleaned_data.get("case_no", "") == ""
            or not cleaned_data.get("case_date", "")
            or cleaned_data.get("sections", "") == ""
        ) and not (
            cleaned_data.get("police_station_with_distt", "") == ""
            and cleaned_data.get("case_no", "") == ""
            and not cleaned_data.get("case_date", "")
            and cleaned_data.get("sections", "") == ""
        ):
            msg = "PS, case number,case date and sections required "
            messages.append(msg)
        if cleaned_data.get("case_no", "") != "" and (
            not cleaned_data.get("case_no", "").isdigit()
        ):
            msg_ = "Case number has to be just a number (without year)"
            messages.append(msg_)
        if messages != []:
            raise forms.ValidationError(messages)

        return cleaned_data


CrimeFormSet = forms.formset_factory(CrimeWithInvolvementForm, can_delete=True)


class CrimeFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.form_method = 'post'
        self.layout = Layout(
            Div(
                Row(
                    Field("uuid", type="hidden"),
                    Column(
                        "police_station_with_distt",
                        css_class="form-group col-md-6 mb-0",
                        id="crime_police_station_id",
                    ),
                    Column("case_no", css_class="form-group col-md-3 mb-0"),
                    Column("case_date", css_class="form-group col-md-3 mb-0"),
                ),
                Row(Column("sections", css_class="form-group col-md-6 mb-0")),
                Row(
                    Column("fir_named", css_class="form-group col-md-2 mb-0"),
                    Column("suspected", css_class="form-group col-md-2 mb-0"),
                    Column("arrested", css_class="form-group col-md-2 mb-0"),
                    Column("arrest_date", css_class="form-group col-md-2 mb-0"),
                    Column("absconding", css_class="form-group col-md-2 mb-0"),
                ),
                Row(
                    Column("bailed", css_class="form-group col-md-2 mb-0"),
                    Column("bailed_date", css_class="form-group col-md-3 mb-0"),
                    Column("p_a_done", css_class="form-group col-md-2 mb-0"),
                    Column("p_a_date", css_class="form-group col-md-3 mb-0"),
                    HTML(
                        """
                    <div class="input-group-append col-md-2">
                <button class="btn btn-success add-form-row">+</button>
            </div>
            """,
                    ),
                ),
                css_class=" form-row-clone spacer",
            ),
        )

        self.form_tag = False


class CrimeFinalReportForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    final_form_no = forms.CharField(
        required=False,
        label="Final Form No.",
        max_length=10,
    )
    final_form_date = forms.DateField()
    final_form_type = forms.ChoiceField(
        choices=[
            (0, "CS"),
            (1, "FRT"),
            (2, "FRMF"),
            (3, "FRIF"),
            (4, "FRML"),
            (5, "Transfer"),
            (6, "FR Non-cog"),
        ],
        label="Final Form Type",
    )
    alamat = forms.CharField(
        required=False,
        label="Alamat",
        max_length=20000,
        widget=forms.Textarea(),
    )
    pr_no = forms.CharField(required=False, label="Property Reg.  No.", max_length=30)
    court = forms.ChoiceField(choices=COURTS)
    judge = forms.ChoiceField(choices=JUDGES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Field("uuid", type="hidden"),
                Column("final_form_no", css_class="form-group col-md-2 mb-0"),
                Column("final_form_date", css_class="form-group col-md-3 mb-0"),
                Column("final_form_type", css_class="form-group col-md-2 mb-0"),
                Column("court", css_class="form-group col-md-3 mb-0"),
                Column("judge", css_class="form-group col-md-2 mb-0"),
            ),
            Row(
                Column("alamat", css_class="form-group col-md-10 mb-0"),
                Column("pr_no", css_class="form-group col-md-2 mb-0"),
            ),
        )
        self.helper.form_method = "post"
        self.helper.form_tag = False


class CriminalWithFinalFormForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    person = forms.CharField(required=False, disabled=True, label=False)
    chargesheeted = forms.BooleanField(required=False)
    evidence = forms.CharField(required=False, label="Evidence", max_length=200)
    copy_serve_date = forms.DateField(required=False)
    custodial_trial = forms.BooleanField(required=False)


CriminalFinalFormFormSet = forms.formset_factory(CriminalWithFinalFormForm, extra=0)


class CriminalFinalFormFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.form_method = 'post'
        self.layout = Layout(
            Row(
                Field("uuid", type="hidden"),
                Column("person", css_class="form-group col-md-12 mb-0"),
            ),
            Row(
                Column("chargesheeted", css_class="form-group col-md-2 mb-0"),
                Column("copy_serve_date", css_class="form-group col-md-2 mb-0"),
                Column("custodial_trial", css_class="form-group col-md-2 mb-0"),
            ),
            Row(
                Column("evidence", css_class="form-group col-md-12 mb-0"),
            ),
        )

        self.form_tag = False


class CrimeSubjudiceForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    gr_no = forms.CharField(required=False, label="GR No.", max_length=10)
    gr_year = forms.CharField(required=False, label="GR Year.", max_length=5)
    st_case_no = forms.CharField(required=False, label="ST No.", max_length=10)
    commitment_date = forms.DateField(required=False)
    charge_framing_date = forms.DateField(required=False)
    monitoring = forms.BooleanField(required=False)
    cs_receipt_date = forms.DateField(required=False)
    pp = forms.CharField(required=False, label="PP Name", max_length=40)
    comments_of_superiors = forms.CharField(
        required=False,
        label="Comments",
        max_length=100,
    )
    conviction = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Field("uuid", type="hidden"),
                Column("cs_receipt_date", css_class="form-group col-md-3 mb-0"),
                Column("gr_no", css_class="form-group col-md-2 mb-0"),
                Column("gr_year", css_class="form-group col-md-2 mb-0"),
                Column("st_case_no", css_class="form-group col-md-2 mb-0"),
                Column("commitment_date", css_class="form-group col-md-3 mb-0"),
            ),
            Row(
                Column("charge_framing_date", css_class="form-group col-md-2 mb-0"),
                Column("pp", css_class="form-group col-md-3 mb-0"),
                Column("comments_of_superiors", css_class="form-group col-md-3 mb-0"),
                Column("monitoring", css_class="form-group col-md-2 mb-0"),
                Column("conviction", css_class="form-group col-md-2 mb-0"),
            ),
        )
        self.helper.form_method = "post"
        self.helper.form_tag = False


class WitnessForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    particulars = forms.CharField(required=False, label="Particulars", max_length=200)
    # dates_of_examination = forms.CharField(required=False,label='GR No.', max_length=200)
    # gist_of_deposition = forms.CharField(required=False,label='GR No.', max_length=200)
    # favourable = forms.BooleanField(required=False)


WitnessFormSet = forms.formset_factory(WitnessForm, can_delete=True)


class WitnessFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.form_method = 'post'
        self.layout = Layout(
            Div(
                Row(
                    Field("uuid", type="hidden"),
                    Column("particulars", css_class="form-group col-md-10 mb-0"),
                    HTML(
                        """
                    <div class="input-group-append col-md-2">
                <button class="btn btn-success add-form-row">+</button>
            </div>
            """,
                    ),
                ),
                css_class=" form-row-clone spacer",
            ),
        )
        self.form_tag = False


class WitnessForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    particulars = forms.CharField(required=False, label="Particulars", max_length=200)
    dates_of_examination = forms.CharField(
        required=False,
        label="GR No.",
        max_length=200,
    )
    gist_of_deposition = forms.CharField(required=False, label="GR No.", max_length=200)
    favourable = forms.BooleanField(required=False)


WitnessFormSet_ = forms.formset_factory(WitnessForm)


class WitnessFormSetHelperUnderscored(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.form_method = 'post'
        self.layout = Layout(
            Div(
                Row(
                    Field("uuid", type="hidden"),
                    Column("particulars", css_class="form-group col-md-4 mb-0"),
                    Column(
                        "dates_of_examination",
                        css_class="form-group col-md-2 mb-0",
                    ),
                    Column("gist_of_deposition", css_class="form-group col-md-4 mb-0"),
                    Column("favourable", css_class="form-group col-md-1 mb-0"),
                    HTML(
                        """
                    <div class="input-group-append col-md-1">
                <button class="btn btn-success">Edit</button>
            </div>
            """,
                    ),
                ),
            ),
        )
        self.form_tag = False


class CourtDateForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    hearing_date = forms.DateField(required=False)
    comment = forms.CharField(required=False, label="GR No.", max_length=200)
    next_date = forms.DateField(required=False)
    next_date_for_comment = forms.CharField(
        required=False,
        label="GR No.",
        max_length=200,
    )


CourtDateFormSet = forms.formset_factory(CourtDateForm)


class CourtDateFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.form_method = 'post'
        self.layout = Layout(
            Div(
                Row(
                    Field("uuid", type="hidden"),
                    Column("hearing_date", css_class="form-group col-md-2 mb-0"),
                    Column("comment", css_class="form-group col-md-4 mb-0"),
                    Column("next_date", css_class="form-group col-md-2 mb-0"),
                    Column(
                        "next_date_for_comment",
                        css_class="form-group col-md-3 mb-0",
                    ),
                    HTML(
                        """
                    <div class="input-group-append col-md-1">
                <button class="btn btn-success">Edit</button>
            </div>
            """,
                    ),
                ),
            ),
        )
        self.form_tag = False


class CalendarForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    starter_police_station_with_distt = forms.CharField(
        label="Police Station",
        required=False,
        max_length=100,
    )
    starter_districts = forms.ChoiceField(
        choices=DISTRICTS,
        required=False,
        label="District",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Field("uuid", type="hidden"),
                Column(
                    "starter_police_station_with_distt",
                    css_class="form-group col-md-6 mb-0",
                ),
                Column("starter_districts", css_class="form-group  col-md-6 mb-0"),
            ),
        )
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))


class DailyReportForm(forms.Form):
    uuid = forms.CharField(required=False, widget=forms.HiddenInput())
    dr_police_station_with_distt = forms.CharField(
        label="Police Station",
        required=False,
        max_length=100,
    )
    dr_districts = forms.ChoiceField(
        choices=DISTRICTS,
        required=False,
        label="District",
    )
    dr_date = forms.DateField(label="Daily Report for Date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Field("uuid", type="hidden"),
                Column(
                    "dr_police_station_with_distt",
                    css_class="form-group col-md-4 mb-0",
                ),
                Column("dr_districts", css_class="form-group  col-md-4 mb-0"),
                Column("dr_date", css_class="form-group  col-md-4 mb-0"),
            ),
        )
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))


class VehicleSearchForm(forms.Form):
    registration_no = forms.CharField(required=False, max_length=10)
    engine_no = forms.CharField(required=False, max_length=10)
    chassis_no = forms.CharField(required=False, max_length=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("registration_no", css_class="form-group col-md-4 mb-0"),
                Column("engine_no", css_class="form-group  col-md-4 mb-0"),
                Column("chassis_no", css_class="form-group  col-md-4 mb-0"),
            ),
        )
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))


##########################
class ImageSearchForm(forms.Form):
    avatar_url = forms.FileField(
        label="Photos ",
        required=False,
        widget=forms.ClearableFileInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("avatar_url", css_class="form-group col-md-4 mb-0")),
        )

        self.helper.form_method = "post"
        self.helper.form_tag = False


#########################
class StfForm(forms.Form):
    avatar_url = forms.FileField(
        label="Photos ",
        required=False,
        widget=forms.ClearableFileInput(),
    )
    sharing_details = forms.CharField(required=False, max_length=500)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("avatar_url", css_class="form-group col-md-4 mb-0")),
            Row(Column("sharing_details", css_class="form-group  mb-0")),
        )

        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit"))
