"""
Notification Preferences App Configuration

This module defines the Django app configuration for the notification preferences.
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration for the notifications app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notification Preferences'