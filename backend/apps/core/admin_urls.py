from django.urls import path
from apps.core.admin_views import (
    FeatureFlagListView,
    FeatureFlagDetailView,
    ActivityLogListView,
    MediaListView,
    MediaDetailView,
    PlatformConfigView,
)
from apps.core.admin_api_views import (
    SystemHealthView,
    ScraperDashboardView,
    AICostDashboardView,
    VerificationResultView,
    VerificationOverrideView,
    SourceControlView,
    AdminCompanyListView,
    AdminCompanyDetailView,
    TalentPoolAdminView,
    UserTimelineView,
    CompanyTimelineView,
    RecommendationDiagnosticsView,
    GDPRAdminDashboardView,
    GDPRExportActionView,
    GDPRDeleteActionView,
    DecisionSupportAlertsView,
    CeleryBeatListView,
    CeleryBeatToggleView,
    AdminSearchView,
    SubscriptionPlanListView,
    SubscriptionPlanDetailView,
    CompanySubscriptionListView,
    CompanySubscriptionDetailView,
    AdminCopilotChatView,
)
from apps.jobs.template_views import JobTemplateDownloadView

urlpatterns = [
    # Existing routes
    path("feature-flags/", FeatureFlagListView.as_view(), name="feature-flags-list"),
    path("feature-flags/<uuid:uuid>/", FeatureFlagDetailView.as_view(), name="feature-flags-detail"),
    path("activity-logs/", ActivityLogListView.as_view(), name="activity-logs-list"),
    path("media/", MediaListView.as_view(), name="media-list"),
    path("media/<uuid:uuid>/", MediaDetailView.as_view(), name="media-detail"),
    path("jobs/template/", JobTemplateDownloadView.as_view(), name="job-template-download"),
    path("platform-config/", PlatformConfigView.as_view(), name="platform-config"),

    # Phase 7a: New admin API endpoints
    path("system-health/", SystemHealthView.as_view(), name="system-health"),
    path("scraper-dashboard/", ScraperDashboardView.as_view(), name="scraper-dashboard-api"),
    path("ai-costs/", AICostDashboardView.as_view(), name="ai-costs-api"),
    path("verification/<uuid:job_uuid>/", VerificationResultView.as_view(), name="verification-result"),
    path("verification/<uuid:job_uuid>/override/", VerificationOverrideView.as_view(), name="verification-override"),
    path("sources/<uuid:source_uuid>/control/", SourceControlView.as_view(), name="source-control"),
    path("companies/", AdminCompanyListView.as_view(), name="admin-companies-list"),
    path("companies/<uuid:uuid>/", AdminCompanyDetailView.as_view(), name="admin-companies-detail"),
    path("talent-pools/", TalentPoolAdminView.as_view(), name="admin-talent-pools"),
    path("users/<int:user_id>/timeline/", UserTimelineView.as_view(), name="user-timeline"),
    path("companies/<uuid:company_uuid>/timeline/", CompanyTimelineView.as_view(), name="company-timeline"),
    path("recommendations/diagnostics/", RecommendationDiagnosticsView.as_view(), name="recommendation-diagnostics"),
    path("gdpr/dashboard/", GDPRAdminDashboardView.as_view(), name="gdpr-dashboard"),
    path("gdpr/export/", GDPRExportActionView.as_view(), name="gdpr-export-action"),
    path("gdpr/delete/", GDPRDeleteActionView.as_view(), name="gdpr-delete-action"),

    # Final pass: decision-support alerts
    path("alerts/", DecisionSupportAlertsView.as_view(), name="decision-support-alerts"),

    # Phase 7b: New admin API endpoints
    path("celery-beat/", CeleryBeatListView.as_view(), name="celery-beat-list"),
    path("celery-beat/<int:task_id>/toggle/", CeleryBeatToggleView.as_view(), name="celery-beat-toggle"),
    path("search/", AdminSearchView.as_view(), name="admin-search"),
    path("plans/", SubscriptionPlanListView.as_view(), name="subscription-plans-list"),
    path("plans/<uuid:uuid>/", SubscriptionPlanDetailView.as_view(), name="subscription-plans-detail"),
    path("subscriptions/", CompanySubscriptionListView.as_view(), name="company-subscriptions-list"),
    path("subscriptions/<uuid:uuid>/", CompanySubscriptionDetailView.as_view(), name="company-subscriptions-detail"),
    path("copilot/chat/", AdminCopilotChatView.as_view(), name="admin-copilot-chat"),
]
