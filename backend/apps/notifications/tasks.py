"""
Celery tasks for notification email delivery and digest batching.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import UserNotification, NotificationPreference, NotificationBatch
from .service import should_send_email, _get_or_create_preferences

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(ignore_result=True)
def deliver_notification(notification_id: int):
    """
    Send email for a single notification, respecting user preferences.

    Called asynchronously when alert_frequency is 'instant'.
    """
    try:
        notification = UserNotification.objects.select_related('user').get(id=notification_id)
    except UserNotification.DoesNotExist:
        logger.error(f"deliver_notification: notification {notification_id} not found")
        return

    user = notification.user
    prefs = _get_or_create_preferences(user)

    # Double-check preferences (might have changed between creation and delivery)
    if not should_send_email(prefs, notification.notification_type):
        logger.info(
            f"deliver_notification: skipping email for notification {notification_id} "
            f"(user prefs disallow)"
        )
        return

    # Send email via the email service
    from apps.emails.service import email_service

    subject = notification.title
    html_content = _build_notification_html(notification)
    text_content = notification.message

    success, tracking_id = email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        user=user,
    )

    # Update batch counters if a batch exists for today
    _update_batch_counters(success)

    if success:
        logger.info(f"Notification email sent for notification {notification_id} to {user.email}")
    else:
        logger.error(f"Failed to send notification email for {notification_id} to {user.email}")


@shared_task
def send_notification_digest():
    """
    Send batched digest emails for users with daily/weekly frequency.

    Intended to be scheduled:
    - Daily at a configurable time for 'daily' users
    - Weekly (e.g., every Monday) for 'weekly' users
    """
    now = timezone.now()

    # Create a batch record
    batch = NotificationBatch.objects.create(
        batch_type='digest',
        status='processing',
        started_at=now,
    )

    total_sent = 0
    total_failed = 0

    # Process daily digest users
    daily_prefs = NotificationPreference.objects.filter(
        alert_frequency='daily',
        email_enabled=True,
    ).select_related('user')

    for pref in daily_prefs:
        sent = _send_digest_for_user(pref.user, pref, period_hours=24)
        if sent:
            total_sent += 1
        else:
            total_failed += 1

    # Process weekly digest users (only on the configured day or every run)
    # Weekly users get their digest if there are 7+ days of unsent notifications
    weekly_prefs = NotificationPreference.objects.filter(
        alert_frequency='weekly',
        email_enabled=True,
    ).select_related('user')

    for pref in weekly_prefs:
        sent = _send_digest_for_user(pref.user, pref, period_hours=168)
        if sent:
            total_sent += 1
        else:
            total_failed += 1

    # Finalize batch
    batch.total_notifications = total_sent + total_failed
    batch.sent_count = total_sent
    batch.failed_count = total_failed
    batch.status = 'completed'
    batch.completed_at = timezone.now()
    batch.save()

    logger.info(f"Notification digest complete: {total_sent} sent, {total_failed} failed")
    return {'sent': total_sent, 'failed': total_failed}


def _send_digest_for_user(user, prefs: NotificationPreference, period_hours: int) -> bool:
    """
    Gather unread notifications for the period and send a digest email.

    Returns True if email sent successfully, False otherwise.
    """
    cutoff = timezone.now() - timedelta(hours=period_hours)

    notifications = UserNotification.objects.filter(
        user=user,
        sent_at__gte=cutoff,
        status='unread',
    ).order_by('-sent_at')

    if not notifications.exists():
        return False  # Nothing to send

    # Build digest content
    subject = f"Your notification digest ({notifications.count()} updates)"
    html_content = _build_digest_html(user, notifications)
    text_content = _build_digest_text(notifications)

    from apps.emails.service import email_service

    success, _ = email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        user=user,
    )

    return success


def _build_notification_html(notification: UserNotification) -> str:
    """Build HTML email content for a single notification."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">{notification.title}</h2>
        <p style="color: #555; font-size: 16px; line-height: 1.5;">{notification.message}</p>
        {f'<a href="{notification.related_url}" style="display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px;">View Details</a>' if notification.related_url else ''}
        <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">
            You received this because you have instant notifications enabled.
            <a href="/settings/notifications/">Manage preferences</a>
        </p>
    </body>
    </html>
    """


def _build_digest_html(user, notifications) -> str:
    """Build HTML email content for a digest of notifications."""
    items_html = ""
    for n in notifications[:20]:  # Cap at 20 items
        items_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <strong>{n.title}</strong><br>
                <span style="color: #666; font-size: 14px;">{n.message[:100]}</span>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Your Notification Digest</h2>
        <p style="color: #555;">You have {notifications.count()} new notifications:</p>
        <table style="width: 100%; border-collapse: collapse;">
            {items_html}
        </table>
        <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">
            <a href="/settings/notifications/">Manage notification preferences</a>
        </p>
    </body>
    </html>
    """


def _build_digest_text(notifications) -> str:
    """Build plain text content for a digest email."""
    lines = [f"You have {notifications.count()} new notifications:\n"]
    for n in notifications[:20]:
        lines.append(f"- {n.title}: {n.message[:80]}")
    lines.append("\nManage preferences: /settings/notifications/")
    return "\n".join(lines)


def _update_batch_counters(success: bool):
    """Update the most recent active batch's counters."""
    try:
        batch = NotificationBatch.objects.filter(
            batch_type='alert',
            status='processing',
        ).order_by('-started_at').first()

        if not batch:
            # Create or get today's alert batch
            batch, created = NotificationBatch.objects.get_or_create(
                batch_type='alert',
                status='processing',
                defaults={'started_at': timezone.now()},
            )

        if success:
            batch.sent_count += 1
        else:
            batch.failed_count += 1
        batch.total_notifications += 1
        batch.save()
    except Exception as exc:
        logger.warning(f"Failed to update batch counters: {exc}")
