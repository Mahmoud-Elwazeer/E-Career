from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from apps.accounts.models import User


@admin.register(User)
class UserAdmin(UnfoldModelAdmin, BaseUserAdmin):  # ← Add BaseUserAdmin here
    list_display = [
        "email", "full_name", "role_badge", "status_badge",
        "is_active", "is_deleted", "date_joined"
    ]
    list_filter = ["role", "status", "is_active", "is_deleted", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    readonly_fields = ["uuid", "created_at", "updated_at", "last_login", "deleted_at"]
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        ("Identity", {
            "fields": ("uuid", "email", "first_name", "last_name", "avatar"),
        }),
        ("Role & Status", {
            "fields": ("role", "status", "is_active", "is_staff", "is_superuser"),
        }),
        ("Soft Delete", {
            "fields": ("is_deleted", "deleted_at"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "last_login"),
        }),
        ("Permissions", {
            "fields": ("groups", "user_permissions"),
        }),
    )

    add_fieldsets = (
        (None, {
            "fields": ("email", "first_name", "last_name", "password1", "password2", "role"),
        }),
    )

    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = "Name"

    def role_badge(self, obj):
        color = "purple" if obj.role == "admin" else "blue"
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color,
            obj.get_role_display(),
        )
    role_badge.short_description = "Role"

    def status_badge(self, obj):
        colors = {"active": "green", "inactive": "gray", "banned": "red"}
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color:{};">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"

    @admin.action(description="Promote to admin role")
    def make_admin(self, request, queryset):
        queryset.update(role="admin")
        self.message_user(request, f"{queryset.count()} users promoted to admin.")

    @admin.action(description="Ban selected users")
    def ban_users(self, request, queryset):
        queryset.update(status="banned", is_active=False)
        self.message_user(request, f"{queryset.count()} users banned.")

    @admin.action(description="Restore selected users")
    def restore_users(self, request, queryset):
        queryset.update(status="active", is_active=True, is_deleted=False, deleted_at=None)
        self.message_user(request, f"{queryset.count()} users restored.")

    actions = ["make_admin", "ban_users", "restore_users"]
    actions_submit_line = []