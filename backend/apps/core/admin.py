from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from apps.core.models import FeatureFlag, ActivityLog, Media


@admin.register(FeatureFlag)
class FeatureFlagAdmin(UnfoldModelAdmin):
    list_display = ["key", "label", "status_badge", "updated_at"]
    list_filter = ["is_enabled"]
    search_fields = ["key", "label", "description"]
    ordering = ["key"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    compressed_fields = True
    warn_unsaved_form = True

    def status_badge(self, obj):
        if obj.is_enabled:
            return format_html('<span style="color:green;font-weight:bold">● ON</span>')
        return format_html('<span style="color:red;">● OFF</span>')

    status_badge.short_description = "Status"

    @admin.action(description="Enable selected flags")
    def enable_flags(self, request, queryset):
        queryset.update(is_enabled=True)
        self.message_user(request, f"{queryset.count()} flags enabled.")

    @admin.action(description="Disable selected flags")
    def disable_flags(self, request, queryset):
        queryset.update(is_enabled=False)
        self.message_user(request, f"{queryset.count()} flags disabled.")

    actions = ["enable_flags", "disable_flags"]


@admin.register(ActivityLog)
class ActivityLogAdmin(UnfoldModelAdmin):
    list_display = ["action", "user", "target_type", "target_id", "created_at"]
    list_filter = ["action", "target_type", "created_at"]
    search_fields = ["action", "target_type", "target_id", "user__email"]
    ordering = ["-created_at"]
    readonly_fields = ["user", "action", "target_type", "target_id", "metadata", "created_at"]
    compressed_fields = True

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Media)
class MediaAdmin(UnfoldModelAdmin):
    list_display = ["filename", "mime_type", "size_display", "uploaded_by", "created_at"]
    list_filter = ["mime_type", "created_at"]
    search_fields = ["filename", "uploaded_by__email"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "size", "mime_type", "uploaded_by", "created_at", "updated_at"]
    compressed_fields = True
    warn_unsaved_form = True

    def size_display(self, obj):
        if obj.size < 1024:
            return f"{obj.size} B"
        elif obj.size < 1024 * 1024:
            return f"{obj.size / 1024:.1f} KB"
        return f"{obj.size / (1024 * 1024):.1f} MB"

    size_display.short_description = "Size"
