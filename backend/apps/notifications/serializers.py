"""
Notification Preferences Serializers

This module contains Django REST Framework serializers for notification models.
"""

import logging
from rest_framework import serializers
from .models import (
    NotificationPreference,
    UserNotification,
    NotificationBatch,
)

logger = logging.getLogger(__name__)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'user',
            'alert_frequency',
            'email_enabled',
            'email_digest_enabled',
            'email_digest_time',
            'in_app_enabled',
            'push_enabled',
            'notify_job_matches',
            'notify_new_jobs',
            'notify_interview_invites',
            'notify_interview_reminders',
            'notify_profile_views',
            'notify_message_responses',
            'notify_application_updates',
            'notify_skill_badges',
            'notify_score_improvements',
            'notify_weekly_digest',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class UserNotificationSerializer(serializers.ModelSerializer):
    """Serializer for UserNotification model."""
    
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UserNotification
        fields = [
            'id',
            'user',
            'notification_type',
            'title',
            'message',
            'related_id',
            'related_type',
            'related_url',
            'status',
            'priority',
            'sent_at',
            'read_at',
            'expires_at',
        ]
        read_only_fields = ['user', 'sent_at', 'read_at']


class NotificationBatchSerializer(serializers.ModelSerializer):
    """Serializer for NotificationBatch model."""
    
    class Meta:
        model = NotificationBatch
        fields = [
            'id',
            'batch_type',
            'total_notifications',
            'sent_count',
            'failed_count',
            'status',
            'started_at',
            'completed_at',
            'error_message',
        ]
        read_only_fields = [
            'total_notifications',
            'sent_count',
            'failed_count',
            'status',
            'started_at',
            'completed_at',
            'error_message',
        ]


class NotificationUpdateSerializer(serializers.Serializer):
    """Serializer for updating notification status."""
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    status = serializers.ChoiceField(choices=STATUS_CHOICES)


class NotificationBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk notification updates."""
    
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
    status = serializers.ChoiceField(choices=UserNotificationSerializer.Meta.fields[11])


class DigestSettingsSerializer(serializers.Serializer):
    """Serializer for digest settings."""
    
    email_digest_enabled = serializers.BooleanField(required=False)
    email_digest_time = serializers.TimeField(
        required=False,
        format='%H:%M',
        input_formats=['%H:%M', '%H:%M:%S']
    )
    alert_frequency = serializers.ChoiceField(
        choices=NotificationPreference.FREQUENCY_CHOICES,
        required=False
    )