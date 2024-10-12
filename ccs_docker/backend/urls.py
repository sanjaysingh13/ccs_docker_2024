from django.urls import path

from ccs_docker.backend import views
from ccs_docker.backend.views import CrimeDetailView

app_name = "backend"

urlpatterns = [
    path("start/", views.starter, name="start"),
    path("crimes/<uuid:uuid>", CrimeDetailView.as_view(), name="crime-detail"),
    path("crimes/add", views.create_crime_with_criminals, name="crime-create"),
    path(
        "crimes/<uuid:unique_id>/edit",
        views.edit_crime_with_criminals,
        name="crime-edit",
    ),
    path(
        "crimes/<uuid:unique_id>/final_form",
        views.edit_crime_final_form,
        name="crime-final_form",
    ),
    path(
        "crimes/<uuid:unique_id>/subjudice",
        views.create_subjudice,
        name="crime-subjudice",
    ),
    path(
        "crimes/<uuid:unique_id>/trial_monitoring",
        views.trial_monitoring,
        name="crime-trial-monitoring",
    ),
    path("criminals/add", views.create_criminal_with_crimes, name="criminal-create"),
    path(
        "criminals/<uuid:unique_id>/edit",
        views.edit_criminal_with_crimes,
        name="criminal-edit",
    ),
    path(
        "calendar/<uuid:unique_id>/",
        views.court_date_calendar,
        name="court-date-calendar",
    ),
    path(
        "calendar/<uuid:unique_id>/<int:year>/<int:month>",
        views.court_date_calendar,
        name="court-date-calendar-nav",
    ),
    path("daily_report/", views.daily_report, name="daily_report"),
    path("vehicle_search/", views.vehicle_search, name="vehicle_search"),
    # path(
    #     "upload_criminal_for_face_match/",
    #     views.upload_criminal_for_face_match,
    #     name="upload_criminal_for_face_match",
    # ),
    path(
        "criminal_matches/<str:matches>",
        views.criminal_matches,
        name="criminal-matches",
    ),
    # path(
    #     "return_matches_to_missing_found/>",
    #     views.return_matches_to_missing_found,
    #     name="return_matches_to_missing_found",
    # ),
    path("add_stf/<uuid:uuid>", views.add_stf, name="add_stf"),
]
