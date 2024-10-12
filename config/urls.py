from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from .views import HomeOld

urlpatterns = [
    re_path(
        r"^favicon\.ico$",
        RedirectView.as_view(url=settings.MEDIA_URL + "favicon.ico"),
    ),
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "privacy/",
        TemplateView.as_view(template_name="pages/privacy.html"),
        name="privacy",
    ),
    path(
        "home_old/",
        HomeOld.as_view(template_name="pages/home_old.html"),
        name="home_old",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("ccs_docker.users.urls", namespace="users")),
    # path('accounts/signup/', signup_view, name = 'account_signup'),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path("graphs/", include("ccs_docker.graphs.urls", namespace="graphs")),
    path(
        "searches/",
        include("ccs_docker.searches.urls", namespace="searches"),
    ),
    path(
        "backend/",
        include("ccs_docker.backend.urls", namespace="backend"),
    ),
    path("maps/", include("ccs_docker.maps.urls", namespace="maps")),
    path("charts/", include("ccs_docker.charts.urls", namespace="charts")),
    path("pdf/", include("ccs_docker.pdf.urls", namespace="pdf")),
    path("ajax/", include("ccs_docker.ajax.urls", namespace="ajax")),
    path(
        "utilities/",
        include("ccs_docker.utilities.urls", namespace="utilities"),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
