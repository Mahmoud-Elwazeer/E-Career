from django.urls import path
from apps.core.admin_views import (
    FeatureFlagListView,
    FeatureFlagDetailView,
    ActivityLogListView,
    MediaListView,
    MediaDetailView,
)
from apps.jobs.template_views import JobTemplateDownloadView

urlpatterns = [
    path("feature-flags/", FeatureFlagListView.as_view(), name="feature-flags-list"),
    path("feature-flags/<uuid:uuid>/", FeatureFlagDetailView.as_view(), name="feature-flags-detail"),
    path("activity-logs/", ActivityLogListView.as_view(), name="activity-logs-list"),
    path("media/", MediaListView.as_view(), name="media-list"),
    path("media/<uuid:uuid>/", MediaDetailView.as_view(), name="media-detail"),
    path("jobs/template/", JobTemplateDownloadView.as_view(), name="job-template-download"),
]
