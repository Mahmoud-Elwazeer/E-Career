"""
Notification Preferences Admin

This module defines Django admin configurations for notification models.
"""

from django.contrib import admin
from .models import (
    NotificationPreference,
    UserNotification,
    NotificationBatch,
)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin for NotificationPreference model."""
    
    list_display = ['user', 'alert_frequency', 'email_enabled', 'push_enabled', 'created_at']
    list_filter = ['alert_frequency', 'email_enabled', 'push_enabled', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    """Admin for UserNotification model."""
    
    list_display = ['title', 'user', 'notification_type', 'status', 'priority', 'sent_at']
    list_filter = ['notification_type', 'status', 'priority', 'sent_at']
    search_fields = ['title', 'message', 'user__email']
    readonly_fields = ['sent_at', 'read_at']


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    """Admin for NotificationBatch model."""
    
    list_display = ['batch_type', 'status', 'total_notifications', 'sent_count', 'failed_count', 'started_at']
    list_filter = ['batch_type', 'status', 'started_at']
    search_fields = ['error_message']
    readonly_fields = ['started_at', 'completed_at']