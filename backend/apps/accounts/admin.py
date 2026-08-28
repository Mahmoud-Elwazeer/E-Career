"""
Admin configuration for User model using django-unfold.
Phase 3C: Admin Dashboard Extensions
Phase G4: GDPR Compliance Models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from apps.accounts.models import User
from apps.accounts.models_gdpr import DataExportRequest, AccountDeletionRequest


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    """
    Enhanced User admin with unfold styling.
    """
    list_display = [
        "email", "full_name", "role_badge", "status_badge",
        "is_active", "is_deleted", "date_joined"
    ]
    list_filter = ["role", "status", "is_active", "is_deleted", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    readonly_fields = ["uuid", "created_at", "updated_at", "last_login", "deleted_at"]
    
    fieldsets = (
        ("Identity", {
            "fields": ("uuid", "email", "first_name", "last_name", "avatar")
        }),
        ("Role & Status", {
            "fields": ("role", "status", "is_active", "is_staff", "is_superuser")
        }),
        ("Soft Delete", {
            "fields": ("is_deleted", "deleted_at")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "last_login")
        }),
        ("Permissions", {
            "fields": ("groups", "user_permissions")
        }),
    )
    
    add_fieldsets = (
        (None, {
            "fields": ("email", "first_name", "last_name", "password1", "password2", "role")
        }),
    )
    
    @display(description="Name")
    def full_name(self, obj):
        return obj.get_full_name()
    
    @display(
        description="Role",
        label={
            "admin": "purple",
            "employer": "blue",
            "job_seeker": "green",
        }
    )
    def role_badge(self, obj):
        return obj.get_role_display()
    
    @display(
        description="Status",
        label={
            "active": "success",
            "inactive": "warning",
            "banned": "danger",
        }
    )
    def status_badge(self, obj):
        return obj.get_status_display()
    
    @admin.action(description="Promote to admin role")
    def make_admin(self, request, queryset):
        count = queryset.update(role="admin")
        self.message_user(request, f"{count} users promoted to admin.")
    
    @admin.action(description="Ban selected users")
    def ban_users(self, request, queryset):
        from apps.core.models import ActivityLog
        count = queryset.update(status="banned", is_active=False)
        for user in queryset:
            ActivityLog.objects.create(
                user=request.user,
                action="ban_user",
                target_type="User",
                target_id=str(user.pk),
                metadata={"email": user.email},
            )
        self.message_user(request, f"{count} users banned.")

    @admin.action(description="Restore selected users")
    def restore_users(self, request, queryset):
        from apps.core.models import ActivityLog
        count = queryset.update(status="active", is_active=True, is_deleted=False, deleted_at=None)
        for user in queryset:
            ActivityLog.objects.create(
                user=request.user,
                action="restore_user",
                target_type="User",
                target_id=str(user.pk),
                metadata={"email": user.email},
            )
        self.message_user(request, f"{count} users restored.")
    
    actions = ["make_admin", "ban_users", "restore_users"]


# ============================================================================
# GDPR Compliance Admin (Phase G4)
# ============================================================================


@admin.register(DataExportRequest)
class DataExportRequestAdmin(ModelAdmin):
    """
    Admin interface for GDPR data export requests.
    Article 15 - Right to Access
    """
    list_display = [
        "user_email",
        "status_badge",
        "file_size_mb",
        "requested_at",
        "completed_at",
        "expires_at",
    ]
    list_filter = ["status", "requested_at", "completed_at"]
    search_fields = ["user__email", "ip_address"]
    readonly_fields = [
        "id", "user", "file_path", "file_size_bytes",
        "requested_at", "completed_at", "expires_at", "ip_address"
    ]

    fieldsets = (
        ("Request Info", {
            "fields": ("id", "user", "status", "ip_address")
        }),
        ("Export File", {
            "fields": ("file_path", "file_size_bytes", "expires_at")
        }),
        ("Timestamps", {
            "fields": ("requested_at", "completed_at")
        }),
        ("Error Details", {
            "fields": ("error_message",),
            "classes": ("collapse",)
        }),
    )

    @display(description="User", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email

    @display(
        description="Status",
        label={
            "pending": "gray",
            "processing": "blue",
            "completed": "green",
            "failed": "red",
            "expired": "gray",
        }
    )
    def status_badge(self, obj):
        return obj.get_status_display()

    @display(description="File Size")
    def file_size_mb(self, obj):
        if obj.file_size_bytes > 0:
            return f"{obj.file_size_bytes / 1024 / 1024:.2f} MB"
        return "-"

    def has_add_permission(self, request):
        """Prevent manual creation - only via API"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of expired exports"""
        return True


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(ModelAdmin):
    """
    Admin interface for GDPR account deletion requests.
    Article 17 - Right to Erasure
    """
    list_display = [
        "user_email",
        "status_badge",
        "requested_at",
        "scheduled_for",
        "days_remaining",
        "completed_at",
    ]
    list_filter = ["status", "requested_at", "scheduled_for"]
    search_fields = ["user__email", "reason", "ip_address"]
    readonly_fields = [
        "id", "user", "requested_at", "scheduled_for",
        "completed_at", "ip_address"
    ]

    fieldsets = (
        ("Request Info", {
            "fields": ("id", "user", "status", "reason", "ip_address")
        }),
        ("Schedule", {
            "fields": ("requested_at", "scheduled_for", "completed_at")
        }),
        ("Error Details", {
            "fields": ("error_message",),
            "classes": ("collapse",)
        }),
    )

    @display(description="User", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email

    @display(
        description="Status",
        label={
            "pending": "yellow",
            "cancelled": "gray",
            "processing": "blue",
            "completed": "green",
            "failed": "red",
        }
    )
    def status_badge(self, obj):
        return obj.get_status_display()

    @display(description="Days Until Deletion")
    def days_remaining(self, obj):
        if obj.status == "pending":
            from django.utils import timezone
            delta = obj.scheduled_for - timezone.now()
            days = delta.days
            if days > 0:
                return f"{days} days"
            else:
                return "Due now"
        return "-"

    def has_add_permission(self, request):
        """Prevent manual creation - only via API"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - audit trail required"""
        return False