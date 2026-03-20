from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from apps.users.models import SavedJob, Alert, Notification


@admin.register(SavedJob)
class SavedJobAdmin(UnfoldModelAdmin):
    list_display = ["user", "job", "saved_at"]
    list_filter = ["saved_at"]
    search_fields = ["user__email", "job__title"]
    ordering = ["-saved_at"]
    readonly_fields = ["saved_at"]
    compressed_fields = True

    def has_add_permission(self, request):
        return False


@admin.register(Alert)
class AlertAdmin(UnfoldModelAdmin):
    list_display = ["user", "keyword", "work_mode", "industry", "frequency", "is_active", "created_at"]
    list_filter = ["frequency", "is_active", "industry"]
    search_fields = ["user__email", "keyword"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    compressed_fields = True
    warn_unsaved_form = True


@admin.register(Notification)
class NotificationAdmin(UnfoldModelAdmin):
    list_display = ["user", "title", "type", "is_read", "created_at"]
    list_filter = ["type", "is_read", "created_at"]
    search_fields = ["user__email", "title"]
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    compressed_fields = True
    warn_unsaved_form = True
