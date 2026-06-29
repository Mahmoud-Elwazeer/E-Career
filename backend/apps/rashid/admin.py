"""
Admin configuration for Rashid AI Assistant using django-unfold.
Phase 3C: Admin Dashboard Extensions
"""

from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.enums import Color

from .models import (
    RashidConfig,
    RashidProfile,
    RashidConversation,
    RashidMessage,
    RashidStoryBank,
    RashidUsage
)


@admin.register(RashidConfig)
class RashidConfigAdmin(ModelAdmin):
    """
    Admin for Rashid configuration (singleton).
    Enhanced with unfold styling.
    """
    list_display = ['ai_provider', 'bedrock_model_id', 'temperature', 'max_tokens', 'is_active', 'updated_at']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('AI Provider', {
            'fields': ('ai_provider', 'bedrock_region', 'bedrock_model_id', 'anthropic_model')
        }),
        ('Generation Parameters', {
            'fields': ('temperature', 'max_tokens')
        }),
        ('Prompts', {
            'fields': ('system_prompt', 'dialect_config', 'onboarding_questions'),
            'classes': ('collapse',)
        }),
        ('Limits', {
            'fields': ('daily_token_limit', 'max_conversation_len', 'auto_delete_after_days')
        }),
        ('Status', {
            'fields': ('is_active', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one config
        from .models import RashidConfig
        if RashidConfig.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting the config
        return False


@admin.register(RashidProfile)
class RashidProfileAdmin(ModelAdmin):
    """
    Admin for Rashid user profiles.
    Enhanced with unfold styling.
    """
    list_display = ['user', 'experience_level', 'current_role', 'target_role', 'onboarding_complete', 'last_updated']
    list_filter = ['onboarding_complete', 'experience_level']
    search_fields = ['user__email', 'current_role', 'target_role']
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Career Information', {
            'fields': ('experience_level', 'current_role', 'current_situation', 'target_role')
        }),
        ('Skills', {
            'fields': ('skills', 'skill_gaps')
        }),
        ('Constraints', {
            'fields': ('constraints',)
        }),
        ('Generated Plans', {
            'fields': ('career_path', 'action_plan'),
            'classes': ('collapse',)
        }),
        ('Onboarding', {
            'fields': ('onboarding_complete', 'onboarding_step', 'last_updated')
        }),
    )


class RashidMessageInline(TabularInline):
    """
    Inline admin for messages (read-only).
    """
    model = RashidMessage
    extra = 0
    readonly_fields = ['role', 'content_preview', 'tokens_used', 'created_at']
    fields = ['role', 'content_preview', 'tokens_used', 'created_at']
    
    def content_preview(self, obj):
        """Show truncated content (encrypted, so we can't show actual content)"""
        return f"[{obj.role} message - {obj.tokens_used} tokens]"
    content_preview.short_description = 'Content'
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RashidConversation)
class RashidConversationAdmin(ModelAdmin):
    """
    Admin for Rashid conversations.
    Enhanced with unfold styling.
    """
    list_display = ['id', 'user', 'mode', 'title', 'is_active', 'started_at', 'updated_at']
    list_filter = ['mode', 'is_active']
    search_fields = ['user__email', 'title']
    readonly_fields = ['id', 'started_at', 'updated_at']
    inlines = [RashidMessageInline]
    
    fieldsets = (
        ('Conversation Info', {
            'fields': ('id', 'user', 'mode', 'title', 'job')
        }),
        ('Status', {
            'fields': ('is_active', 'started_at', 'updated_at')
        }),
    )


@admin.register(RashidMessage)
class RashidMessageAdmin(ModelAdmin):
    """
    Admin for Rashid messages (limited - content is encrypted).
    Enhanced with unfold styling.
    """
    list_display = ['id', 'conversation', 'role', 'tokens_used', 'created_at']
    list_filter = ['role']
    search_fields = ['conversation__user__email']
    readonly_fields = ['conversation', 'role', 'tokens_used', 'created_at']
    
    # Don't show content in admin (it's encrypted)
    fields = ['conversation', 'role', 'tokens_used', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RashidStoryBank)
class RashidStoryBankAdmin(ModelAdmin):
    """
    Admin for STAR stories.
    Enhanced with unfold styling.
    """
    list_display = ['user', 'situation_preview', 'created_at', 'updated_at']
    search_fields = ['user__email', 'situation', 'task', 'action', 'result']
    readonly_fields = ['created_at', 'updated_at']
    
    def situation_preview(self, obj):
        return obj.situation[:50] + '...' if len(obj.situation) > 50 else obj.situation
    situation_preview.short_description = 'Situation'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('STAR Components', {
            'fields': ('situation', 'task', 'action', 'result', 'reflection')
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(RashidUsage)
class RashidUsageAdmin(ModelAdmin):
    """
    Admin for token usage tracking.
    Enhanced with unfold styling.
    """
    list_display = ['user', 'date', 'tokens_used']
    list_filter = ['date']
    search_fields = ['user__email']
    readonly_fields = ['user', 'date', 'tokens_used']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


def get_active_conversations_count():
    """Badge count for active conversations"""
    return RashidConversation.objects.filter(is_active=True).count()