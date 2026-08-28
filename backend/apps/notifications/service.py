"""
Notification Delivery Service

Provides helpers to create notifications and dispatch email delivery
respecting user preferences.
"""

import logging
from typing import Optional

from django.contrib.auth import get_user_model

from .models import UserNotification, NotificationPreference

logger = logging.getLogger(__name__)
User = get_user_model()

# Mapping from notification_type to the corresponding NotificationPreference boolean field
NOTIFICATION_TYPE_TO_PREF_FIELD = {
    'job_match': 'notify_job_matches',
    'new_job': 'notify_new_jobs',
    'interview_invite': 'notify_interview_invites',
    'interview_reminder': 'notify_interview_reminders',
    'profile_view': 'notify_profile_views',
    'message_response': 'notify_message_responses',
    'application_update': 'notify_application_updates',
    'skill_badge': 'notify_skill_badges',
    'score_improvement': 'notify_score_improvements',
    'weekly_digest': 'notify_weekly_digest',
    'system': None,  # system notifications always allowed
    'promotional': None,
}


def _get_or_create_preferences(user) -> NotificationPreference:
    """Get or create notification preferences for a user."""
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def should_send_email(prefs: NotificationPreference, notification_type: str) -> bool:
    """
    Determine whether an email should be sent based on user preferences.

    Returns False if:
    - email_enabled is False
    - alert_frequency is 'never'
    - the specific notification type is disabled in preferences
    """
    if not prefs.email_enabled:
        return False

    if prefs.alert_frequency == 'never':
        return False

    # Check type-specific preference
    pref_field = NOTIFICATION_TYPE_TO_PREF_FIELD.get(notification_type)
    if pref_field and not getattr(prefs, pref_field, True):
        return False

    return True


def create_and_deliver_notification(
    user,
    notification_type: str,
    title: str,
    message: str,
    related_id: str = "",
    related_type: str = "",
    related_url: str = "",
    priority: str = "medium",
) -> Optional[UserNotification]:
    """
    Create a UserNotification record and dispatch email delivery if appropriate.

    Args:
        user: User instance to notify.
        notification_type: One of UserNotification.TYPE_CHOICES values.
        title: Notification title.
        message: Notification body text.
        related_id: Optional ID of related object.
        related_type: Optional type label of related object.
        related_url: Optional URL for the related content.
        priority: Notification priority (low/medium/high/urgent).

    Returns:
        The created UserNotification, or None on failure.
    """
    try:
        notification = UserNotification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_id=related_id,
            related_type=related_type,
            related_url=related_url,
            priority=priority,
        )

        # Check preferences to decide on immediate delivery
        prefs = _get_or_create_preferences(user)

        if prefs.alert_frequency == 'instant' and should_send_email(prefs, notification_type):
            # Dispatch async email delivery
            from .tasks import deliver_notification
            deliver_notification.delay(notification.id)

        # For daily/weekly, the digest task will pick these up later

        return notification

    except Exception as exc:
        logger.error(f"Failed to create notification for user {getattr(user, 'id', '?')}: {exc}")
        return None
