from django.urls import path
from apps.accounts.views import MeView, AvatarUploadView, ChangePasswordView
from apps.users.views import (
    SavedJobListView, SavedJobDetailView,
    AlertListView, AlertDetailView,
    NotificationListView, NotificationDetailView, MarkAllNotificationsReadView,
)

urlpatterns = [
    # Profile
    path("me/", MeView.as_view(), name="users-me"),
    path("me/avatar/", AvatarUploadView.as_view(), name="users-avatar"),
    path("me/change-password/", ChangePasswordView.as_view(), name="users-change-password"),
    # Saved Jobs
    path("me/saved-jobs/", SavedJobListView.as_view(), name="saved-jobs-list"),
    path("me/saved-jobs/<int:pk>/", SavedJobDetailView.as_view(), name="saved-jobs-detail"),
    # Alerts
    path("me/alerts/", AlertListView.as_view(), name="alerts-list"),
    path("me/alerts/<uuid:uuid>/", AlertDetailView.as_view(), name="alerts-detail"),
    # Notifications
    path("me/notifications/", NotificationListView.as_view(), name="notifications-list"),
    path("me/notifications/<uuid:uuid>/", NotificationDetailView.as_view(), name="notifications-detail"),
    path("me/notifications/mark-all-read/", MarkAllNotificationsReadView.as_view(), name="notifications-mark-all-read"),
]
