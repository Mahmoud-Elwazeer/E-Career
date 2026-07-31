"""
Event consumers for processing emitted events.

This module contains consumers that process events from the event log:
- AnalyticsAggregator: Aggregates events for analytics dashboards
- AuditTrailWriter: Writes events to audit trail for compliance
"""
from __future__ import annotations

import structlog
from datetime import datetime, timedelta
from typing import Any

from django.db.models import Count, Avg, Sum
from django.utils import timezone

logger = structlog.get_logger()


class AnalyticsAggregator:
    """
    Aggregate events for analytics dashboards.
    
    Processes events and creates aggregated metrics for:
    - Daily active users
    - Job engagement metrics
    - Search analytics
    - CV parsing success rates
    - AI usage patterns
    """
    
    def __init__(self):
        self._processed_events: set[str] = set()
    
    def aggregate_daily_metrics(self, date: datetime | None = None) -> dict[str, Any]:
        """
        Aggregate daily metrics from events.
        
        Args:
            date: Date to aggregate (defaults to yesterday)
            
        Returns:
            Dictionary of aggregated metrics
        """
        if date is None:
            date = timezone.now().date() - timedelta(days=1)
        
        start = timezone.make_aware(
            datetime.combine(date, datetime.min.time())
        )
        end = start + timedelta(days=1)
        
        from apps.events.models import EventLog
        
        events = EventLog.objects.filter(
            created_at__gte=start,
            created_at__lt=end
        )
        
        metrics = {
            "date": str(date),
            "generated_at": timezone.now().isoformat(),
            "total_events": events.count(),
            "by_category": {},
            "by_event_type": {},
            "by_user": {},
        }
        
        # Aggregate by category
        category_counts = events.values("category").annotate(
            count=Count("id")
        )
        metrics["by_category"] = {
            item["category"]: item["count"] for item in category_counts
        }
        
        # Aggregate by event type
        type_counts = events.values("event_type").annotate(
            count=Count("id")
        )
        metrics["by_event_type"] = {
            item["event_type"]: item["count"] for item in type_counts
        }
        
        # Aggregate by user (top 100)
        user_counts = events.filter(user__isnull=False).values(
            "user_id"
        ).annotate(
            count=Count("id")
        ).order_by("-count")[:100]
        metrics["by_user"] = {
            str(item["user_id"]): item["count"] for item in user_counts
        }
        
        # Specific metrics
        metrics["daily_active_users"] = events.filter(
            user__isnull=False
        ).values("user_id").distinct().count()
        
        metrics["job_views"] = events.filter(
            event_type="job_viewed"
        ).count()
        
        metrics["job_saves"] = events.filter(
            event_type="job_saved"
        ).count()
        
        metrics["job_applied"] = events.filter(
            event_type="job_applied"
        ).count()
        
        metrics["searches"] = events.filter(
            event_type="search_performed"
        ).count()
        
        metrics["cv_uploads"] = events.filter(
            event_type="cv_uploaded"
        ).count()
        
        metrics["cv_parsed"] = events.filter(
            event_type="cv_parsed"
        ).count()
        
        metrics["ai_calls"] = events.filter(
            event_type="ai_model_called"
        ).count()
        
        # Cost tracking
        ai_events = events.filter(event_type="ai_model_called")
        if ai_events.exists():
            total_cost = sum(
                e.data.get("cost_usd", 0) for e in ai_events
            )
            metrics["ai_total_cost_usd"] = round(total_cost, 4)
        
        logger.info(
            "daily_analytics_aggregated",
            date=str(date),
            total_events=metrics["total_events"],
            dau=metrics["daily_active_users"],
        )
        
        return metrics
    
    def aggregate_user_metrics(self, user_id: int, days: int = 30) -> dict[str, Any]:
        """
        Aggregate metrics for a specific user.
        
        Args:
            user_id: User ID to aggregate
            days: Number of days to look back
            
        Returns:
            Dictionary of user metrics
        """
        from apps.events.models import EventLog
        
        cutoff = timezone.now() - timedelta(days=days)
        
        events = EventLog.objects.filter(
            user_id=user_id,
            created_at__gte=cutoff
        )
        
        metrics = {
            "user_id": user_id,
            "period_days": days,
            "generated_at": timezone.now().isoformat(),
            "total_events": events.count(),
            "by_category": {},
            "by_event_type": {},
        }
        
        # Aggregate by category
        category_counts = events.values("category").annotate(
            count=Count("id")
        )
        metrics["by_category"] = {
            item["category"]: item["count"] for item in category_counts
        }
        
        # Aggregate by event type
        type_counts = events.values("event_type").annotate(
            count=Count("id")
        )
        metrics["by_event_type"] = {
            item["event_type"]: item["count"] for item in type_counts
        }
        
        # Last activity
        last_event = events.order_by("-created_at").first()
        if last_event:
            metrics["last_activity"] = last_event.created_at.isoformat()
        
        return metrics


class AuditTrailWriter:
    """
    Write events to audit trail for compliance.
    
    Ensures all significant events are logged for:
    - Security auditing
    - Regulatory compliance
    - User activity tracking
    - Data provenance
    """
    
    def __init__(self):
        self._batch_size = 100
        self._batch: list[dict[str, Any]] = []
    
    def write_event(self, event: dict[str, Any]) -> None:
        """
        Write an event to the audit trail.
        
        Args:
            event: Event data dictionary
        """
        self._batch.append({
            "event_type": event.get("event_type"),
            "category": event.get("category"),
            "user_id": event.get("user_id"),
            "target_type": event.get("target_type"),
            "target_id": event.get("target_id"),
            "data": event.get("data", {}),
            "ip_address": event.get("ip_address"),
            "user_agent": event.get("user_agent"),
            "created_at": event.get("created_at"),
        })
        
        if len(self._batch) >= self._batch_size:
            self._flush()
    
    def _flush(self) -> None:
        """Flush the batch to the database."""
        if not self._batch:
            return
        
        from apps.events.models import EventLog
        
        try:
            EventLog.objects.bulk_create([
                EventLog(**event) for event in self._batch
            ])
            logger.info(
                "audit_trail_batch_written",
                count=len(self._batch),
            )
            self._batch = []
        except Exception as e:
            logger.error(
                "audit_trail_batch_failed",
                error=str(e),
                count=len(self._batch),
            )
    
    def flush(self) -> None:
        """Force flush any pending events."""
        self._flush()


# Singleton instances
analytics_aggregator = AnalyticsAggregator()
audit_trail_writer = AuditTrailWriter()