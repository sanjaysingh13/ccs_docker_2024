from django.urls import path

from . import views

app_name = "charts"
urlpatterns = [
    path("crime_search/", views.crime_search, name="crime_search"),
    path(
        "crime_search_chart/<int:pk>",
        views.crime_search_chart,
        name="crime_search_chart",
    ),
    path("trans_ps_activity/", views.trans_ps_activity, name="trans_ps_activity"),
    path(
        "trans_ps_activity_in_ps/",
        views.trans_ps_activity_in_ps,
        name="trans_ps_activity_in_ps",
    ),
    # path('criminal_search_chart/<int:pk>', views.criminal_search_chart, name='criminal_search_chart'),
]
