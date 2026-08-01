"""
Admin configuration for emails app using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
try:
    from unfold.enums import Color
except ImportError:
    class Color:
        GREEN = "green"
        GRAY = "gray"
        RED = "red"
        YELLOW = "yellow"
        BLUE = "blue"

from .models import EmailAccount, EmailTemplate, EmailLog


@admin.register(EmailAccount)
class EmailAccountAdmin(ModelAdmin):
    """
    Admin for email accounts with usage stats.
    Enhanced with unfold styling.
    """
    
    list_display = [
        'name', 'email', 'rotation_order', 'daily_status',
        'total_sent', 'is_active', 'last_used_at'
    ]
    list_filter = ['is_active']
    list_editable = ['rotation_order', 'is_active']
    search_fields = ['name', 'email']
    ordering = ['rotation_order']
    
    readonly_fields = ['today_sent', 'total_sent', 'last_used_at', 'last_reset']
    
    fieldsets = (
        ('Account Info', {
            'fields': ('name', 'email', 'is_active', 'rotation_order')
        }),
        ('SMTP Settings', {
            'fields': ('smtp_host', 'smtp_port', 'username_enc', 'password_enc')
        }),
        ('Rate Limiting', {
            'fields': ('daily_limit', 'today_sent', 'last_reset')
        }),
        ('Statistics', {
            'fields': ('total_sent', 'last_used_at', 'tracking_enabled')
        }),
    )
    
    @display(description='Daily Usage')
    def daily_status(self, obj):
        """Show daily usage as progress bar."""
        percentage = min(100, (obj.today_sent / obj.daily_limit) * 100) if obj.daily_limit > 0 else 0
        color = 'green' if percentage < 50 else 'orange' if percentage < 80 else 'red'
        return format_html(
            '<div style="width: 100px; background: #eee; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px;"></div>'
            '</div>'
            '<span style="font-size: 11px;">{}/{} emails</span>',
            percentage, color, obj.today_sent, obj.daily_limit
        )


@admin.register(EmailTemplate)
class EmailTemplateAdmin(ModelAdmin):
    """
    Admin for email templates with preview.
    Enhanced with unfold styling.
    """
    
    list_display = ['name', 'template_type', 'is_active', 'total_sent', 'last_sent_at', 'preview_link']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Content', {
            'fields': ('subject', 'html_body', 'text_body')
        }),
        ('Statistics', {
            'fields': ('total_sent', 'last_sent_at')
        }),
    )
    
    readonly_fields = ['total_sent', 'last_sent_at']
    
    @display(description='Preview')
    def preview_link(self, obj):
        """Link to preview the template."""
        return format_html(
            '<a href="/emails/preview/{}/" target="_blank">Preview</a>',
            obj.id
        )


@admin.register(EmailLog)
class EmailLogAdmin(ModelAdmin):
    """
    Admin for email logs with tracking info.
    Enhanced with unfold styling.
    """
    
    list_display = [
        'recipient', 'subject', 'template', 'sent_at',
        'opened_status', 'clicked_status', 'failed_status'
    ]
    list_filter = ['template', 'opened', 'clicked', 'failed', 'sent_at']
    search_fields = ['recipient', 'subject']
    readonly_fields = [
        'user', 'account', 'template', 'recipient', 'subject',
        'sent_at', 'tracking_id', 'opened', 'opened_at',
        'clicked', 'clicked_at', 'failed', 'error_message'
    ]
    date_hierarchy = 'sent_at'
    
    @display(
        description='Opened',
        label={
            True: Color.GREEN,
            False: Color.GRAY,
        }
    )
    def opened_status(self, obj):
        """Show open status with icon."""
        if obj.opened:
            return f"Opened {obj.opened_at.strftime('%Y-%m-%d %H:%M') if obj.opened_at else ''}"
        return "Not opened"
    
    @display(
        description='Clicked',
        label={
            True: Color.GREEN,
            False: Color.GRAY,
        }
    )
    def clicked_status(self, obj):
        """Show click status with icon."""
        if obj.clicked:
            return f"Clicked {obj.clicked_at.strftime('%Y-%m-%d %H:%M') if obj.clicked_at else ''}"
        return "Not clicked"
    
    @display(
        description='Status',
        label={
            'sent': Color.GREEN,
            'failed': Color.RED,
        }
    )
    def failed_status(self, obj):
        """Show failed status."""
        if obj.failed:
            return f"Failed: {obj.error_message[:50] if obj.error_message else ''}"
        return "Sent"
    
    def has_add_permission(self, request):
        """Disable manual log creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable log editing."""
        return False