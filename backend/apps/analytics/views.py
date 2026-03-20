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
        from apps.analytics.models import JobView, JobClick
        from apps.users.models import SavedJob

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        stats = {
            "total_jobs": Job.objects.filter(status="active").count(),
            "pending_review": Job.objects.filter(status="pending").count(),
            "active_sources": Source.objects.filter(is_active=True).count(),
            "total_saves": SavedJob.objects.count(),
            "total_clicks": JobClick.objects.count(),
            "total_views": JobView.objects.count(),
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
    """GET /api/v1/analytics/clicks/ — Apply-click analytics."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.analytics.models import JobClick

        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        total = JobClick.objects.filter(clicked_at__gte=since).count()

        by_job = list(
            JobClick.objects.filter(clicked_at__gte=since)
            .values("job__slug", "job__title")
            .annotate(count=Count("id"))
            .order_by("-count")[:20]
        )
        for item in by_job:
            item["slug"] = item.pop("job__slug")
            item["title"] = item.pop("job__title")

        by_source = list(
            JobClick.objects.filter(clicked_at__gte=since)
            .values("source__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        for item in by_source:
            item["name"] = item.pop("source__name") or "Unknown"

        return Response({
            "success": True,
            "data": {"total": total, "by_job": by_job, "by_source": by_source},
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
    """GET /api/v1/analytics/searches/ — Search query analytics."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.analytics.models import SearchLog

        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        total_searches = SearchLog.objects.filter(searched_at__gte=since).count()

        top_queries = list(
            SearchLog.objects.filter(searched_at__gte=since, query__gt="")
            .values("query")
            .annotate(count=Count("id"))
            .order_by("-count")[:20]
        )

        zero_result_queries = list(
            SearchLog.objects.filter(searched_at__gte=since, results_count=0, query__gt="")
            .values_list("query", flat=True)
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
        from apps.analytics.models import JobView, JobClick

        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        total_views = JobView.objects.filter(viewed_at__gte=since).count()
        total_clicks = JobClick.objects.filter(clicked_at__gte=since).count()
        conversion_rate = (
            f"{(total_clicks / total_views * 100):.1f}%"
            if total_views > 0
            else "0%"
        )

        per_job = list(
            JobClick.objects.filter(clicked_at__gte=since)
            .values("job__slug", "job__title")
            .annotate(clicks=Count("id"))
            .order_by("-clicks")[:10]
        )
        for item in per_job:
            item["slug"] = item.pop("job__slug")
            item["title"] = item.pop("job__title")

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


@extend_schema(tags=["Analytics"])
class ActivityLogListView(APIView):
    """GET /api/v1/analytics/activity-logs/ — Admin activity log."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        from apps.core.models import ActivityLog
        from apps.core.serializers import ActivityLogSerializer
        from apps.core.pagination import StandardPagination

        qs = ActivityLog.objects.select_related("user").order_by("-created_at")

        action_filter = request.query_params.get("action")
        if action_filter:
            qs = qs.filter(action=action_filter)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = ActivityLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
