import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from apps.core.permissions import IsAdminRole

logger = logging.getLogger(__name__)


@extend_schema(tags=["Analytics"])
class AdminStatsView(APIView):
    """GET /api/v1/analytics/stats/ — High-level admin dashboard stats."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.jobs.models import Job, Source
        from apps.accounts.models import User
        from apps.events.models import EventLog
        from apps.users.models import SavedJob

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        stats = {
            "total_jobs": Job.objects.filter(status="active").count(),
            "pending_review": Job.objects.filter(status="pending").count(),
            "active_sources": Source.objects.filter(is_active=True).count(),
            "total_saves": SavedJob.objects.count(),
            "total_clicks": EventLog.objects.filter(event_type="job_applied").count(),
            "total_views": EventLog.objects.filter(event_type="job_viewed").count(),
            "total_users": User.objects.filter(is_deleted=False).count(),
            "jobs_this_week": Job.objects.filter(created_at__gte=week_ago).count(),
        }

        return Response({
            "success": True,
            "data": stats,
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Analytics"])
class AdminChartsView(APIView):
    """GET /api/v1/analytics/charts/ — Jobs by industry and source breakdowns."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.jobs.models import Job

        industry_qs = list(
            Job.objects.filter(status="active")
            .values("industry")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        jobs_by_industry = [
            {"name": item["industry"], "count": item["count"]}
            for item in industry_qs
        ]

        source_qs = list(
            Job.objects.filter(status="active")
            .values("source__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        jobs_by_source = [
            {"name": item["source__name"] or "Unknown", "count": item["count"]}
            for item in source_qs
        ]

        return Response({
            "success": True,
            "data": {
                "jobs_by_industry": jobs_by_industry,
                "jobs_by_source": jobs_by_source,
                "recent_activity": [],
            },
            "message": "",
            "errors": None,
        })


@extend_schema(
    tags=["Analytics"],
    parameters=[
        OpenApiParameter("days", OpenApiTypes.INT, description="Number of days to look back (default 30)"),
    ],
)
class ClickAnalyticsView(APIView):
    """GET /api/v1/analytics/clicks/ — Apply-click analytics (reads from EventLog)."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.events.models import EventLog

        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        qs = EventLog.objects.filter(event_type="job_applied", created_at__gte=since)
        total = qs.count()

        by_job = list(
            qs.values("target_id")
            .annotate(count=Count("id"))
            .order_by("-count")[:20]
        )

        return Response({
            "success": True,
            "data": {"total": total, "by_job": by_job, "by_source": []},
            "message": "",
            "errors": None,
        })


@extend_schema(
    tags=["Analytics"],
    parameters=[
        OpenApiParameter("days", OpenApiTypes.INT, description="Number of days to look back (default 30)"),
    ],
)
class SearchAnalyticsView(APIView):
    """GET /api/v1/analytics/searches/ — Search query analytics (reads from EventLog)."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.events.models import EventLog

        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        qs = EventLog.objects.filter(event_type="search_performed", created_at__gte=since)
        total_searches = qs.count()

        top_queries = list(
            qs.exclude(data__query="")
            .values("data__query")
            .annotate(count=Count("id"))
            .order_by("-count")[:20]
        )
        for item in top_queries:
            item["query"] = item.pop("data__query", "")

        zero_result_queries = list(
            qs.filter(data__results_count=0)
            .exclude(data__query="")
            .values_list("data__query", flat=True)
            .distinct()[:20]
        )

        return Response({
            "success": True,
            "data": {
                "total_searches": total_searches,
                "top_queries": top_queries,
                "zero_result_queries": list(zero_result_queries),
            },
            "message": "",
            "errors": None,
        })


@extend_schema(
    tags=["Analytics"],
    parameters=[
        OpenApiParameter("days", OpenApiTypes.INT, description="Number of days to look back (default 30)"),
    ],
)
class ConversionAnalyticsView(APIView):
    """GET /api/v1/analytics/conversion/ — View-to-click conversion stats."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.events.models import EventLog

        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        total_views = EventLog.objects.filter(event_type="job_viewed", created_at__gte=since).count()
        total_clicks = EventLog.objects.filter(event_type="job_applied", created_at__gte=since).count()
        conversion_rate = (
            f"{(total_clicks / total_views * 100):.1f}%"
            if total_views > 0
            else "0%"
        )

        per_job = list(
            EventLog.objects.filter(event_type="job_applied", created_at__gte=since)
            .values("target_id")
            .annotate(clicks=Count("id"))
            .order_by("-clicks")[:10]
        )

        return Response({
            "success": True,
            "data": {
                "total_views": total_views,
                "total_clicks": total_clicks,
                "conversion_rate": conversion_rate,
                "per_job": per_job,
                "period_days": days,
            },
            "message": "",
            "errors": None,
        })


from apps.core.admin_views import ActivityLogListView  # noqa: F401
