"""
Analytics Dashboard Views

Admin dashboard for business intelligence and insights.
Converted from Django template views to DRF JSON API for the React admin SPA.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from apps.core.permissions import IsAdminRole
from .tracking import analytics_tracker

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Analytics"],
    parameters=[
        OpenApiParameter("days", OpenApiTypes.INT, description="Lookback window in days (default 30)"),
    ],
)
class AnalyticsDashboardView(APIView):
    """GET /api/v1/analytics/dashboard/ — Main analytics dashboard data."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        days = int(request.query_params.get('days', 30))

        data = {
            'days': days,
            'funnel': analytics_tracker.get_conversion_funnel(days=days),
            'features': analytics_tracker.get_feature_usage_stats(days=days),
            'retention': analytics_tracker.get_retention_cohorts(),
            'market_insights': analytics_tracker.get_job_market_insights(days=days),
        }

        return Response({
            "success": True,
            "data": data,
            "message": "",
            "errors": None,
        })


@extend_schema(
    tags=["Analytics"],
    parameters=[
        OpenApiParameter("days", OpenApiTypes.INT, description="Lookback window in days (default 30)"),
    ],
)
class UserJourneyView(APIView):
    """GET /api/v1/analytics/user/<user_id>/ — Individual user journey data."""

    permission_classes = [IsAdminRole]

    def get(self, request, user_id):
        days = int(request.query_params.get('days', 30))

        data = {
            'user_id': user_id,
            'journey': analytics_tracker.get_user_journey(user_id, days=days),
            'days': days,
        }

        return Response({
            "success": True,
            "data": data,
            "message": "",
            "errors": None,
        })
