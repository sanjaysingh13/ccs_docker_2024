from django.urls import path

from ccs_docker.ajax import views

app_name = "ajax"


urlpatterns = [
    # Backend
    path("crimes/", views.get_ajax_gist, name="get_ajax_gist"),
    path("witnesses/", views.update_witness, name="update_witness"),
    path(
        "court_dates/",
        views.update_or_create_court_date,
        name="update_or_create_court_date",
    ),
    path("get_criminal_name/", views.get_criminal_name, name="get_criminal_name"),
    path("get_daily_report/", views.get_daily_report, name="get_daily_report"),
    # Graphs
    path("nodes_single_path/", views.nodes_single_path, name="nodes_single_path"),
    path("tasks/", views.check_ajax_task, name="check_ajax_task"),
    path(
        "get_network_of_criminal/",
        views.get_network_of_criminal,
        name="get_network_of_criminal",
    ),
    path("nodes_paths/", views.nodes_paths, name="nodes_paths"),
    path(
        "get_connected_criminals_of_ps_task_id/",
        views.get_connected_criminals_of_ps_task_id,
        name="get_connected_criminals_of_ps_task_id",
    ),
    path(
        "get_connected_criminals_of_ps/",
        views.get_connected_criminals_of_ps,
        name="get_connected_criminals_of_ps",
    ),
    path(
        "merge_duplicate_criminals/",
        views.merge_duplicate_criminals,
        name="merge_duplicate_criminals",
    ),
    path("manage_tags/", views.manage_tags, name="manage_tags"),
    path(
        "merge_matched_criminal/",
        views.merge_matched_criminal,
        name="merge_matched_criminal",
    ),
]
