"""
Admin interface for Rule Engine, Feature Flags, and GitHub Integration.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Rule, FeatureFlag, GitHubConnection, PortfolioAnalysis


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    """Admin for Rule model."""
    
    list_display = [
        'name',
        'category',
        'action_type',
        'is_active',
        'priority',
        'created_at',
    ]
    
    list_filter = [
        'category',
        'action_type',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'description',
    ]
    
    readonly_fields = [
        'uuid',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'category')
        }),
        ('Conditions', {
            'fields': ('conditions',),
            'description': 'Define conditions using JSON format. Example: {"operator": "ALL", "conditions": [{"field": "job.trust_score", "operator": "lt", "value": 0.4}]}'
        }),
        ('Action', {
            'fields': ('action_type', 'action_params')
        }),
        ('Settings', {
            'fields': ('is_active', 'priority', 'uuid', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['activate_rules', 'deactivate_rules']
    
    def activate_rules(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Activated {queryset.count()} rules")
    activate_rules.short_description = "Activate selected rules"
    
    def deactivate_rules(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} rules")
    deactivate_rules.short_description = "Deactivate selected rules"


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    """Admin for FeatureFlag model."""
    
    list_display = [
        'key',
        'label',
        'is_enabled',
        'enabled_percentage',
        'employer_only',
        'expires_at',
        'category',
    ]
    
    list_filter = [
        'is_enabled',
        'employer_only',
        'category',
        'expires_at',
    ]
    
    search_fields = [
        'key',
        'label',
        'description',
    ]
    
    readonly_fields = [
        'uuid',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('key', 'label', 'description', 'category')
        }),
        ('Status', {
            'fields': ('is_enabled',)
        }),
        ('Targeting', {
            'fields': ('enabled_for_users', 'enabled_percentage', 'regions', 'employer_only')
        }),
        ('Timing', {
            'fields': ('expires_at',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'uuid', 'created_at', 'updated_at')
        }),
    )


@admin.register(GitHubConnection)
class GitHubConnectionAdmin(admin.ModelAdmin):
    """Admin for GitHubConnection model."""
    
    list_display = [
        'username',
        'user_email',
        'last_sync_status',
        'last_synced_at',
        'created_at',
    ]
    
    list_filter = [
        'last_sync_status',
        'created_at',
    ]
    
    search_fields = [
        'username',
        'user__email',
        'github_id',
    ]
    
    readonly_fields = [
        'uuid',
        'github_id',
        'username',
        'last_synced_at',
        'last_sync_status',
        'last_sync_error',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Connection', {
            'fields': ('user', 'github_id', 'username', 'access_token', 'refresh_token', 'expires_at')
        }),
        ('Profile', {
            'fields': ('avatar_url', 'profile_url', 'email', 'name', 'company', 'location')
        }),
        ('Sync Status', {
            'fields': ('last_synced_at', 'last_sync_status', 'last_sync_error')
        }),
        ('Metadata', {
            'fields': ('uuid', 'created_at', 'updated_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


@admin.register(PortfolioAnalysis)
class PortfolioAnalysisAdmin(admin.ModelAdmin):
    """Admin for PortfolioAnalysis model."""
    
    list_display = [
        'url',
        'user_email',
        'status',
        'quality_score',
        'completeness_score',
        'project_count',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'created_at',
    ]
    
    search_fields = [
        'url',
        'user__email',
    ]
    
    readonly_fields = [
        'uuid',
        'domain',
        'status',
        'error_message',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Portfolio', {
            'fields': ('user', 'url', 'domain')
        }),
        ('Analysis Results', {
            'fields': (
                'technologies', 'projects', 'quality_score', 'completeness_score',
                'tech_stack', 'project_count', 'star_count', 'contribution_count'
            )
        }),
        ('AI Observations', {
            'fields': ('observations',)
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Metadata', {
            'fields': ('uuid', 'created_at', 'updated_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    actions = ['resync_analyses']
    
    def resync_analyses(self, request, queryset):
        # Trigger resync for selected analyses
        for analysis in queryset.filter(status='completed'):
            analysis.status = 'analyzing'
            analysis.save()
        self.message_user(request, f"Resynced {queryset.count()} analyses")
    resync_analyses.short_description = "Resync selected analyses"