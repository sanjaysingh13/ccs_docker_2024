from django.urls import path

from ccs_docker.users.views import user_detail_view
from ccs_docker.users.views import user_redirect_view
from ccs_docker.users.views import user_update_view

from . import views

app_name = "users"
urlpatterns = [
    path("district_admins/", views.district_admins, name="district_admins"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
