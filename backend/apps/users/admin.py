"""
Admin configuration for Users app using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.enums import Color

from apps.users.models import SavedJob, Alert, Notification, UserProfile, JobMatchScore


@admin.register(SavedJob)
class SavedJobAdmin(ModelAdmin):
    """
    Enhanced SavedJob admin with unfold styling.
    """
    list_display = ["user", "job", "saved_at"]
    list_filter = ["saved_at"]
    search_fields = ["user__email", "job__title"]
    ordering = ["-saved_at"]
    readonly_fields = ["saved_at"]
    
    def has_add_permission(self, request):
        return False


@admin.register(Alert)
class AlertAdmin(ModelAdmin):
    """
    Enhanced Alert admin with unfold styling.
    """
    list_display = ["user", "keyword", "work_mode", "industry", "frequency", "is_active_badge", "created_at"]
    list_filter = ["frequency", "is_active", "industry"]
    search_fields = ["user__email", "keyword"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    
    @display(
        description="Active",
        label={
            True: Color.GREEN,
            False: Color.GRAY,
        }
    )
    def is_active_badge(self, obj):
        return "Active" if obj.is_active else "Inactive"


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    """
    Enhanced Notification admin with unfold styling.
    """
    list_display = ["user", "title", "type", "is_read_badge", "created_at"]
    list_filter = ["type", "is_read", "created_at"]
    search_fields = ["user__email", "title"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    
    @display(
        description="Read",
        label={
            True: Color.GRAY,
            False: Color.BLUE,
        }
    )
    def is_read_badge(self, obj):
        return "Read" if obj.is_read else "Unread"


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    """
    Enhanced UserProfile admin with unfold styling.
    """
    list_display = ["user", "cv_parse_status_badge", "experience_years", "open_to_remote", "created_at"]
    list_filter = ["cv_parse_status", "open_to_remote", "email_alerts"]
    search_fields = ["user__email", "current_role"]
    ordering = ["-created_at"]
    readonly_fields = ["cv_uploaded_at", "cv_parsed_at", "created_at", "updated_at"]
    
    @display(
        description="CV Status",
        label={
            "pending": Color.YELLOW,
            "parsed": Color.GREEN,
            "failed": Color.RED,
        }
    )
    def cv_parse_status_badge(self, obj):
        return obj.get_cv_parse_status_display()


@admin.register(JobMatchScore)
class JobMatchScoreAdmin(ModelAdmin):
    """
    Enhanced JobMatchScore admin with unfold styling.
    """
    list_display = ["user", "job", "score_display", "calculated_at"]
    list_filter = ["calculated_at"]
    search_fields = ["user__email", "job__title"]
    ordering = ["-calculated_at"]
    readonly_fields = ["calculated_at"]
    
    @display(description="Score")
    def score_display(self, obj):
        return f"{obj.score:.1f}%"