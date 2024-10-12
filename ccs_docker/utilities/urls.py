# Create your views here.
from django.urls import path

from . import views

app_name = "utilities"
urlpatterns = [
    path("duplicate_criminals", views.duplicate_criminals, name="duplicate_criminals"),
    path(
        "duplicate_criminals_from_list",
        views.duplicate_criminals_from_list,
        name="duplicate_criminals_from_list",
    ),
    path("tag_management", views.tag_management, name="tag_management"),
    path("reset_ps_cache", views.reset_ps_cache, name="reset_ps_cache"),
    path("reset_tag_cache", views.reset_tag_cache, name="reset_tag_cache"),
]
