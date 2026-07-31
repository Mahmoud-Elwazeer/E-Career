from __future__ import annotations

import structlog
from celery import shared_task
from typing import Any

logger = structlog.get_logger()


@shared_task(ignore_result=True)
def write_event(
    event_type: str,
    category: str,
    user_id: int | None,
    target_type: str,
    target_id: str,
    data: dict[str, Any],
    session_id: str = "",
    ip_address: str | None = None,
    user_agent: str = "",
):
    """Write an event to the event log table."""
    from apps.events.models import EventLog

    EventLog.objects.create(
        event_type=event_type,
        category=category,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        data=data,
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@shared_task
def aggregate_daily_analytics():
    """Consume events and update daily analytics summaries."""
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count
    from apps.events.models import EventLog

    yesterday = timezone.now().date() - timedelta(days=1)
    start = timezone.make_aware(
        timezone.datetime.combine(yesterday, timezone.datetime.min.time())
    )
    end = start + timedelta(days=1)

    events = EventLog.objects.filter(created_at__gte=start, created_at__lt=end)

    summary = (
        events.values("event_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    logger.info(
        "daily_analytics_aggregated",
        date=str(yesterday),
        event_types=len(summary),
        total_events=events.count(),
    )
