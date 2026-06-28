from django.contrib import admin
from apps.users.models import SavedJob, Alert, Notification, UserProfile, JobMatchScore


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "saved_at"]
    list_filter = ["saved_at"]
    search_fields = ["user__email", "job__title"]
    ordering = ["-saved_at"]
    readonly_fields = ["saved_at"]

    def has_add_permission(self, request):
        return False


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["user", "keyword", "work_mode", "industry", "frequency", "is_active", "created_at"]
    list_filter = ["frequency", "is_active", "industry"]
    search_fields = ["user__email", "keyword"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_at", "updated_at"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "type", "is_read", "created_at"]
    list_filter = ["type", "is_read", "created_at"]
    search_fields = ["user__email", "title"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_at", "updated_at"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "cv_parse_status", "experience_years", "open_to_remote", "created_at"]
    list_filter = ["cv_parse_status", "open_to_remote", "email_alerts"]
    search_fields = ["user__email", "current_role"]
    ordering = ["-created_at"]
    readonly_fields = ["cv_uploaded_at", "cv_parsed_at", "created_at", "updated_at"]


@admin.register(JobMatchScore)
class JobMatchScoreAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "score", "calculated_at"]
    list_filter = ["calculated_at"]
    search_fields = ["user__email", "job__title"]
    ordering = ["-calculated_at"]
    readonly_fields = ["calculated_at"]