from django.conf import settings
from django.core.cache import cache

from ccs_docker.backend.models import PoliceStation
from ccs_docker.backend.models import Tag


def settings_context(_request):
    """Settings available by default to the templates context."""
    # Note: we intentionally do NOT expose the entire settings
    # to prevent accidental leaking of sensitive information
    ps_list = cache.get("ps_list")
    if not ps_list:
        ps_list = [
            (ps.uuid, ps.ps_with_distt)
            for ps in PoliceStation.nodes.order_by("ps_with_distt")
        ]
        cache.set("ps_list", ps_list, None)

    availableTags = cache.get("availableTags")
    if not availableTags:
        availableTags = [tag.name for tag in Tag.nodes.order_by("name")]
        cache.set("availableTags", availableTags, None)
    return {
        "DEBUG": settings.DEBUG,
        "ps_list": ps_list,
        "availableTags": availableTags,
        "admin_users": ["ADMIN", "CID_ADMIN"],
    }  # explicit
