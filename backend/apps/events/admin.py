"""
Admin configuration for events app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime
from .models import EventLog


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    """Admin for EventLog model."""
    
    list_display = [
        'event_type',
        'category',
        'user_link',
        'target_type',
        'target_id',
        'created_at',
    ]
    
    list_filter = [
        'event_type',
        'category',
        'created_at',
        'target_type',
    ]
    
    search_fields = [
        'event_type',
        'target_id',
        'user__email',
        'user__username',
    ]
    
    readonly_fields = [
        'event_type',
        'category',
        'user',
        'target_type',
        'target_id',
        'data',
        'session_id',
        'ip_address',
        'user_agent',
        'created_at',
    ]
    
    date_hierarchy = 'created_at'
    
    def user_link(self, obj):
        """Create a link to the user admin page."""
        if obj.user:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.email or obj.user.username
            )
        return '-'
    
    user_link.short_description = 'User'
    
    def has_add_permission(self, request):
        """Disable adding new events."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing events."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting events."""
        return False