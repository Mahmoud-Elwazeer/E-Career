"""
Talent-pool discoverability control (individual consent).

`CareerProfile.is_discoverable` is the opt-in that lets employers find and add a
job seeker to talent pools. It defaults to False and, until now, had no way for
the individual to toggle it — so no one could ever be discovered. This endpoint
gives the owner (and only the owner) read + update control over their own flag.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CareerProfile


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def discoverability(request):
    """GET/PATCH the caller's own talent-pool discoverability consent."""
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)

    if request.method == "PATCH":
        value = request.data.get("is_discoverable")
        if not isinstance(value, bool):
            return Response(
                {"success": False, "message": "is_discoverable must be a boolean."},
                status=400,
            )
        profile.is_discoverable = value
        profile.save(update_fields=["is_discoverable"])

    return Response({
        "success": True,
        "data": {"is_discoverable": profile.is_discoverable},
        "message": "",
        "errors": None,
    })
