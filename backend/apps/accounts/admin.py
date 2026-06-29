"""
Admin configuration for User model using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.enums import Color

from apps.accounts.models import User


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
            "admin": Color.PURPLE,
            "employer": Color.BLUE,
            "job_seeker": Color.GREEN,
        }
    )
    def role_badge(self, obj):
        return obj.get_role_display()
    
    @display(
        description="Status",
        label={
            "active": Color.GREEN,
            "inactive": Color.GRAY,
            "banned": Color.RED,
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
        count = queryset.update(status="banned", is_active=False)
        self.message_user(request, f"{count} users banned.")
    
    @admin.action(description="Restore selected users")
    def restore_users(self, request, queryset):
        count = queryset.update(status="active", is_active=True, is_deleted=False, deleted_at=None)
        self.message_user(request, f"{count} users restored.")
    
    actions = ["make_admin", "ban_users", "restore_users"]