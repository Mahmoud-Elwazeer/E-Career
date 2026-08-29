from django.urls import path
from apps.analytics.views import (
    AdminStatsView,
    AdminChartsView,
    ClickAnalyticsView,
    SearchAnalyticsView,
    ConversionAnalyticsView,
    ActivityLogListView,
)
from apps.analytics.views_dashboard import AnalyticsDashboardView, UserJourneyView

urlpatterns = [
    path("stats/", AdminStatsView.as_view(), name="analytics-stats"),
    path("charts/", AdminChartsView.as_view(), name="analytics-charts"),
    path("clicks/", ClickAnalyticsView.as_view(), name="analytics-clicks"),
    path("searches/", SearchAnalyticsView.as_view(), name="analytics-searches"),
    path("conversion/", ConversionAnalyticsView.as_view(), name="analytics-conversion"),
    path("activity-logs/", ActivityLogListView.as_view(), name="analytics-activity-logs"),
    path("dashboard/", AnalyticsDashboardView.as_view(), name="analytics-dashboard"),
    path("user/<int:user_id>/", UserJourneyView.as_view(), name="analytics-user-journey"),
]
