"""
Admin configuration for Core app using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.enums import Color

from apps.core.models import FeatureFlag, ActivityLog, Media, PlatformConfig, ProxyPool, PipelineHealth


@admin.register(FeatureFlag)
class FeatureFlagAdmin(ModelAdmin):
    """
    Enhanced FeatureFlag admin with unfold styling.
    """
    list_display = ["key", "label", "status_badge", "updated_at"]
    list_filter = ["is_enabled"]
    search_fields = ["key", "label", "description"]
    ordering = ["key"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    
    @display(
        description="Status",
        label={
            True: Color.GREEN,
            False: Color.RED,
        }
    )
    def status_badge(self, obj):
        return "ON" if obj.is_enabled else "OFF"
    
    @admin.action(description="Enable selected flags")
    def enable_flags(self, request, queryset):
        count = queryset.update(is_enabled=True)
        self.message_user(request, f"{count} flags enabled.")
    
    @admin.action(description="Disable selected flags")
    def disable_flags(self, request, queryset):
        count = queryset.update(is_enabled=False)
        self.message_user(request, f"{count} flags disabled.")
    
    actions = ["enable_flags", "disable_flags"]


@admin.register(ActivityLog)
class ActivityLogAdmin(ModelAdmin):
    """
    Enhanced ActivityLog admin with unfold styling.
    Read-only audit log.
    """
    list_display = ["action", "user", "target_type", "target_id", "created_at"]
    list_filter = ["action", "target_type", "created_at"]
    search_fields = ["action", "target_type", "target_id", "user__email"]
    ordering = ["-created_at"]
    readonly_fields = ["user", "action", "target_type", "target_id", "metadata", "created_at"]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Media)
class MediaAdmin(ModelAdmin):
    """
    Enhanced Media admin with unfold styling.
    """
    list_display = ["filename", "mime_type", "size_display", "uploaded_by", "created_at"]
    list_filter = ["mime_type", "created_at"]
    search_fields = ["filename", "uploaded_by__email"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "size", "mime_type", "uploaded_by", "created_at", "updated_at"]
    
    @display(description="Size")
    def size_display(self, obj):
        if obj.size < 1024:
            return f"{obj.size} B"
        elif obj.size < 1024 * 1024:
            return f"{obj.size / 1024:.1f} KB"
        return f"{obj.size / (1024 * 1024):.1f} MB"


@admin.register(PlatformConfig)
class PlatformConfigAdmin(ModelAdmin):
    """
    Enhanced PlatformConfig admin with unfold styling.
    Singleton configuration.
    """
    list_display = ["__str__", "maintenance_mode", "updated_at"]
    readonly_fields = ["updated_at", "updated_by"]
    
    def has_add_permission(self, request):
        # Only allow one instance
        if PlatformConfig.objects.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProxyPool)
class ProxyPoolAdmin(ModelAdmin):
    """
    Enhanced ProxyPool admin with unfold styling.
    """
    list_display = ["host", "port", "is_active", "fail_count", "last_used"]
    list_filter = ["is_active"]
    search_fields = ["host", "username"]
    ordering = ["-added_at"]


@admin.register(PipelineHealth)
class PipelineHealthAdmin(ModelAdmin):
    """
    Enhanced PipelineHealth admin with unfold styling.
    Read-only health monitoring.
    """
    list_display = ["task_name", "status_badge", "last_run_at", "last_duration", "run_count"]
    list_filter = ["last_status"]
    search_fields = ["task_name"]
    ordering = ["task_name"]
    readonly_fields = ["task_name", "last_run_at", "last_status", "last_duration", "last_error", "run_count", "updated_at"]
    
    @display(
        description="Status",
        label={
            "success": Color.GREEN,
            "warning": Color.YELLOW,
            "error": Color.RED,
        }
    )
    def status_badge(self, obj):
        return obj.last_status or "unknown"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False