"""
Event emission system.

Usage:
    from apps.events.emitter import emit

    emit(
        event_type="job_viewed",
        category="job",
        user=request.user,
        target_type="job",
        target_id=str(job.id),
        data={"source": "search_results"},
        request=request,
    )
"""
from __future__ import annotations

import structlog
from typing import Any

from django.contrib.auth import get_user_model

logger = structlog.get_logger()

User = get_user_model()


def emit(
    event_type: str,
    category: str = "user",
    user=None,
    target_type: str = "",
    target_id: str = "",
    data: dict[str, Any] | None = None,
    request=None,
):
    """
    Emit an event. Non-blocking — writes to DB via Celery task.

    For high-frequency events in hot paths, use emit_async() instead.
    """
    from apps.events.tasks import write_event

    session_id = ""
    ip_address = None
    user_agent = ""

    if request:
        session_id = request.session.session_key or ""
        ip_address = _get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

    user_id = None
    if user and hasattr(user, "id") and user.is_authenticated:
        user_id = user.id

    write_event.delay(
        event_type=event_type,
        category=category,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        data=data or {},
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.debug(
        "event_emitted",
        event_type=event_type,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
    )


def emit_sync(
    event_type: str,
    category: str = "user",
    user=None,
    target_type: str = "",
    target_id: str = "",
    data: dict[str, Any] | None = None,
    request=None,
):
    """Emit an event synchronously (for critical events that must not be lost)."""
    from apps.events.models import EventLog

    session_id = ""
    ip_address = None
    user_agent = ""

    if request:
        session_id = request.session.session_key or ""
        ip_address = _get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

    user_id = None
    if user and hasattr(user, "id") and user.is_authenticated:
        user_id = user.id

    EventLog.objects.create(
        event_type=event_type,
        category=category,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        data=data or {},
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def _get_client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
