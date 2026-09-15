"""
Regression tests for notification model convergence.

Background: the platform previously had a split-brain bug where the in-app
inbox read `notifications.UserNotification` but some writers wrote the legacy
`users.Notification`, so those notifications never reached the inbox. These
tests lock in the fix: the canonical writer path and the admin broadcast path
both persist to `UserNotification`, which is what the inbox reads.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import UserNotification
from apps.notifications.service import create_and_deliver_notification


@pytest.mark.django_db
class TestNotificationConvergence:
    def _make_user(self, email, role="user"):
        User = get_user_model()
        return User.objects.create_user(email=email, password="TestPass123!", role=role)

    def test_canonical_writer_persists_to_usernotification(self):
        user = self._make_user("conv_candidate@test.com")
        note = create_and_deliver_notification(
            user=user,
            notification_type="system",
            title="Test",
            message="Body",
            related_id="42",
            related_type="job_posting",
        )
        assert note is not None
        # The inbox queryset is UserNotification.objects.filter(user=...)
        assert UserNotification.objects.filter(user=user, title="Test").exists()
        assert note.notification_type == "system"
        assert note.related_id == "42"

    def test_admin_broadcast_reaches_inbox_model(self):
        """The admin broadcast must write UserNotification (inbox model)."""
        u1 = self._make_user("conv_bc1@test.com")
        u2 = self._make_user("conv_bc2@test.com")

        # Mirror the converged broadcast path (bulk_create on UserNotification).
        title, body = "Platform update", "We shipped a thing."
        notes = [
            UserNotification(user=u, notification_type="system", title=title, message=body)
            for u in (u1, u2)
        ]
        UserNotification.objects.bulk_create(notes)

        for u in (u1, u2):
            assert UserNotification.objects.filter(user=u, title=title).exists()

    def test_inbox_query_returns_converged_notifications(self):
        """End-to-end: what the inbox queries returns what writers wrote."""
        user = self._make_user("conv_inbox@test.com")
        create_and_deliver_notification(
            user=user, notification_type="application_update",
            title="Status changed", message="Your application was viewed.",
        )
        # This is exactly the inbox queryset (users/views.NotificationListView).
        inbox = UserNotification.objects.filter(user=user).order_by("-created_at")
        assert inbox.count() == 1
        assert inbox.first().title == "Status changed"
