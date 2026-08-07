"""
Notification Preferences URLs

This module defines URL patterns for the notification preferences app.
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Preferences
    path('preferences/', views.notification_preferences, name='notification-preferences'),
    path('digest-settings/', views.get_digest_settings, name='get-digest-settings'),
    path('digest-settings/', views.update_digest_settings, name='update-digest-settings'),
    
    # Notifications
    path('notifications/', views.user_notifications, name='user-notifications'),
    path('notifications/<uuid:notification_id>/', views.user_notification_detail, name='user-notification-detail'),
    path('notifications/bulk-update/', views.bulk_update_notifications, name='bulk-update-notifications'),
    path('notifications/mark-all-as-read/', views.mark_all_as_read, name='mark-all-as-read'),
    path('notifications/summary/', views.get_notification_summary, name='get-notification-summary'),
    
    # Batches
    path('batches/', views.get_notification_batches, name='get-notification-batches'),
]