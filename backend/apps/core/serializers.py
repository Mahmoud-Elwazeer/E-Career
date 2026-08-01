"""
Core app serializers for Rule Engine, Feature Flags, and GitHub Integration.
"""

from rest_framework import serializers
from .models import Rule, FeatureFlag, GitHubConnection, PortfolioAnalysis, ActivityLog, Media


class RuleSerializer(serializers.ModelSerializer):
    """Serializer for Rule model."""
    
    class Meta:
        model = Rule
        fields = [
            'id',
            'uuid',
            'name',
            'description',
            'category',
            'conditions',
            'action_type',
            'action_params',
            'is_active',
            'priority',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class RuleTestSerializer(serializers.Serializer):
    """Serializer for testing rules against context."""
    
    context = serializers.JSONField(
        help_text="Context data to test rules against"
    )
    stop_on_first = serializers.BooleanField(
        default=False,
        help_text="Stop after first matching rule"
    )


class FeatureFlagSerializer(serializers.ModelSerializer):
    """Serializer for FeatureFlag model."""
    
    is_enabled_for_user = serializers.SerializerMethodField()
    
    class Meta:
        model = FeatureFlag
        fields = [
            'id',
            'uuid',
            'key',
            'label',
            'description',
            'is_enabled',
            'enabled_for_users',
            'enabled_percentage',
            'regions',
            'employer_only',
            'expires_at',
            'category',
            'metadata',
            'is_enabled_for_user',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'is_enabled_for_user']
    
    def get_is_enabled_for_user(self, obj) -> bool:
        """Check if feature is enabled for current user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.is_available_for_user(request.user)
        return False


class GitHubConnectionSerializer(serializers.ModelSerializer):
    """Serializer for GitHubConnection model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = GitHubConnection
        fields = [
            'id',
            'uuid',
            'user_email',
            'github_id',
            'username',
            'avatar_url',
            'profile_url',
            'email',
            'name',
            'company',
            'location',
            'last_synced_at',
            'last_sync_status',
            'last_sync_error',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'uuid', 'user_email', 'github_id', 'username',
            'last_synced_at', 'last_sync_status', 'last_sync_error',
            'created_at', 'updated_at'
        ]


class PortfolioAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for PortfolioAnalysis model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = PortfolioAnalysis
        fields = [
            'id',
            'uuid',
            'user_email',
            'url',
            'domain',
            'technologies',
            'projects',
            'quality_score',
            'completeness_score',
            'tech_stack',
            'project_count',
            'star_count',
            'contribution_count',
            'observations',
            'status',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'uuid', 'user_email', 'domain', 'status', 'error_message',
            'created_at', 'updated_at'
        ]


class GitHubConnectSerializer(serializers.Serializer):
    """Serializer for GitHub OAuth connection request."""
    
    code = serializers.CharField(
        help_text="OAuth code from GitHub"
    )
    state = serializers.CharField(
        help_text="OAuth state parameter"
    )


class PortfolioAnalyzeSerializer(serializers.Serializer):
    """Serializer for portfolio URL analysis request."""

    url = serializers.URLField(
        help_text="Portfolio URL to analyze"
    )


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivityLog model."""

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'action', 'target_type', 'target_id', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


class MediaSerializer(serializers.ModelSerializer):
    """Serializer for Media model."""

    class Meta:
        model = Media
        fields = ['uuid', 'filename', 'file', 'size', 'mime_type', 'uploaded_by', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'created_at', 'updated_at']