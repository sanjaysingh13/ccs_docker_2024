from contextlib import suppress

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "ccs_docker.users"
    verbose_name = _("Users")

    def ready(self):
        with suppress(ImportError):
            import ccs_docker.users.signals  # noqa: F401
