# Create your views here.
from django.urls import path

from . import views
from .views import CriminalDetailView

app_name = "graphs"
urlpatterns = [
    path("criminals/<uuid:uuid>", CriminalDetailView.as_view(), name="criminal-detail"),
    path(
        "network_of_criminal/<uuid:unique_id>",
        views.network_of_criminal,
        name="network_of_criminal",
    ),
    path(
        "connection_of_criminals/",
        views.connection_of_criminals,
        name="connection_of_criminals",
    ),
    path(
        "criminal_associates_in_ps/",
        views.connection_of_criminal_to_ps,
        name="criminal_associates_in_ps",
    ),
    # re_path(r'ajax/tasks/(?P<task_id>.*)/$', views.check_ajax_task, name='check_ajax_task'),
]
