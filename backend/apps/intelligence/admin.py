"""
Intelligence App Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import PromptVersion, PromptUsage


@admin.register(PromptVersion)
class PromptVersionAdmin(admin.ModelAdmin):
    list_display = ['feature_badge', 'name', 'version', 'model_target', 'is_active', 'is_test', 'created_at', 'created_by']
    list_filter = ['feature', 'model_target', 'is_active', 'is_test', 'created_at']
    search_fields = ['name', 'content', 'notes']
    readonly_fields = ['created_at', 'created_by']

    fieldsets = (
        ('Identification', {
            'fields': ('name', 'feature', 'version', 'is_active', 'is_test')
        }),
        ('Prompt Content', {
            'fields': ('content', 'system_prompt')
        }),
        ('Model Configuration', {
            'fields': ('model_target', 'max_tokens', 'temperature')
        }),
        ('Metadata', {
            'fields': ('notes', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_selected', 'deactivate_selected', 'duplicate_prompt']

    def feature_badge(self, obj):
        colors = {
            'cover_letter': '#10b981',
            'cv_tailor': '#3b82f6',
            'match_explanation': '#8b5cf6',
            'interview_questions': '#f59e0b',
            'interview_evaluation': '#ef4444',
            'skill_extraction': '#06b6d4',
            'rashid_career_advice': '#ec4899',
            'rashid_interview_prep': '#f43f5e',
            'weekly_digest_tip': '#14b8a6',
        }
        color = colors.get(obj.feature, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_feature_display()
        )
    feature_badge.short_description = 'Feature'

    def activate_selected(self, request, queryset):
        from apps.core.models import ActivityLog
        for prompt in queryset:
            PromptVersion.objects.filter(name=prompt.name, is_active=True).update(is_active=False)
            prompt.is_active = True
            prompt.save()
            ActivityLog.objects.create(
                user=request.user,
                action="activate_prompt",
                target_type="PromptVersion",
                target_id=str(prompt.pk),
                metadata={"name": prompt.name, "version": prompt.version},
            )
        self.message_user(request, f"{queryset.count()} prompts activated")
    activate_selected.short_description = "✅ Activate selected prompts"

    def deactivate_selected(self, request, queryset):
        from apps.core.models import ActivityLog
        queryset.update(is_active=False)
        for prompt in queryset:
            ActivityLog.objects.create(
                user=request.user,
                action="deactivate_prompt",
                target_type="PromptVersion",
                target_id=str(prompt.pk),
                metadata={"name": prompt.name, "version": prompt.version},
            )
        self.message_user(request, f"{queryset.count()} prompts deactivated")
    deactivate_selected.short_description = "❌ Deactivate selected prompts"

    def duplicate_prompt(self, request, queryset):
        for prompt in queryset:
            prompt.pk = None
            prompt.id = None
            prompt.is_active = False
            prompt.version += 1
            prompt.notes = f"Duplicated from v{prompt.version - 1}"
            prompt.save()
        self.message_user(request, f"{queryset.count()} prompts duplicated")
    duplicate_prompt.short_description = "📋 Duplicate as new version"

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PromptUsage)
class PromptUsageAdmin(admin.ModelAdmin):
    list_display = ['prompt_version', 'user', 'tokens_used', 'latency_ms', 'cost_usd', 'success', 'created_at']
    list_filter = ['success', 'created_at', 'prompt_version__feature']
    search_fields = ['prompt_version__name', 'user__email', 'error_message']
    readonly_fields = ['prompt_version', 'user', 'tokens_used', 'latency_ms', 'cost_usd', 'success', 'error_message', 'created_at']

    def has_add_permission(self, request):
        return False  # Read-only (created by system)

    def has_change_permission(self, request, obj=None):
        return False  # Read-only
