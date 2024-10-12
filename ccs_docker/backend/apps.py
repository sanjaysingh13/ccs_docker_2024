# pylint: disable=unused-import
from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ccs_docker.backend"

    def ready(self):
        import ccs_docker.backend.signals  # noqa: F401
