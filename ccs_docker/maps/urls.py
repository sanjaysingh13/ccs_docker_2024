from django.urls import path

from . import views

app_name = "maps"
urlpatterns = [
    path("police_stations/", views.police_stations, name="police_stations"),
]
