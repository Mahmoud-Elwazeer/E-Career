"""
Notification Preferences Models

This module defines models for notification preferences and user notifications.
"""

import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import UUIDModel, TimeStampedModel

logger = logging.getLogger(__name__)


class NotificationPreference(UUIDModel):
    """
    User's notification preferences.
    
    This model stores user preferences for different notification types.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        db_index=True
    )
    
    # Alert frequency
    FREQUENCY_CHOICES = [
        ('instant', 'Instant'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('never', 'Never'),
    ]
    alert_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='instant',
        help_text="How often to send notifications"
    )
    
    # Email preferences
    email_enabled = models.BooleanField(default=True)
    email_digest_enabled = models.BooleanField(default=True)
    email_digest_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time to send daily/weekly digests"
    )
    
    # In-app notification preferences
    in_app_enabled = models.BooleanField(default=True)
    
    # Push notification preferences
    push_enabled = models.BooleanField(default=True)
    
    # Notification type preferences
    notify_job_matches = models.BooleanField(default=True)
    notify_new_jobs = models.BooleanField(default=True)
    notify_interview_invites = models.BooleanField(default=True)
    notify_interview_reminders = models.BooleanField(default=True)
    notify_profile_views = models.BooleanField(default=True)
    notify_message_responses = models.BooleanField(default=True)
    notify_application_updates = models.BooleanField(default=True)
    notify_skill_badges = models.BooleanField(default=True)
    notify_score_improvements = models.BooleanField(default=True)
    notify_weekly_digest = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time for quiet hours (24-hour format)"
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="End time for quiet hours (24-hour format)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "notification_preference"
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"{self.user.email} - {self.alert_frequency}"


class UserNotification(UUIDModel):
    """
    User notification.
    
    This model stores individual notifications for users.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    
    # Notification type
    TYPE_CHOICES = [
        ('job_match', 'Job Match'),
        ('new_job', 'New Job'),
        ('interview_invite', 'Interview Invite'),
        ('interview_reminder', 'Interview Reminder'),
        ('profile_view', 'Profile View'),
        ('message_response', 'Message Response'),
        ('application_update', 'Application Update'),
        ('skill_badge', 'Skill Badge'),
        ('score_improvement', 'Score Improvement'),
        ('weekly_digest', 'Weekly Digest'),
        ('system', 'System'),
        ('promotional', 'Promotional'),
    ]
    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        db_index=True
    )
    
    # Title and message
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related data
    related_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID of related object (job, interview, etc.)"
    )
    related_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of related object"
    )
    related_url = models.URLField(
        blank=True,
        help_text="URL to related content"
    )
    
    # Status
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unread',
        db_index=True
    )
    
    # Priority
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    
    # Metadata
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification expires"
    )
    
    class Meta:
        db_table = "user_notification"
        ordering = ['-sent_at']
        verbose_name = "User Notification"
        verbose_name_plural = "User Notifications"
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()


class NotificationBatch(UUIDModel):
    """
    Batch of notifications sent together.
    
    This model tracks notification batches for analytics and debugging.
    """
    
    # Batch type
    TYPE_CHOICES = [
        ('digest', 'Digest'),
        ('alert', 'Alert'),
        ('campaign', 'Campaign'),
        ('system', 'System'),
    ]
    batch_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True
    )
    
    # Counters
    total_notifications = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Metadata
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = "notification_batch"
        verbose_name = "Notification Batch"
        verbose_name_plural = "Notification Batches"
    
    def __str__(self):
        return f"{self.batch_type} - {self.status}"