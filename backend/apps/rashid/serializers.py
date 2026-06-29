"""
Serializers for Rashid API
"""

from rest_framework import serializers
from .models import (
    RashidConfig,
    RashidProfile,
    RashidConversation,
    RashidMessage,
    RashidStoryBank
)


class RashidMessageSerializer(serializers.ModelSerializer):
    """Serializer for Rashid messages"""

    class Meta:
        model = RashidMessage
        fields = ['id', 'role', 'content', 'tokens_used', 'created_at']
        read_only_fields = ['id', 'tokens_used', 'created_at']


class RashidConversationSerializer(serializers.ModelSerializer):
    """Serializer for Rashid conversations"""
    messages = RashidMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = RashidConversation
        fields = [
            'id', 'mode', 'title', 'job', 'is_active',
            'started_at', 'updated_at', 'messages',
            'message_count', 'last_message'
        ]
        read_only_fields = ['id', 'started_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'role': last_msg.role,
                'preview': last_msg.content[:100] if last_msg.content else '',
                'timestamp': last_msg.created_at
            }
        return None


class RashidConversationListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing conversations"""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = RashidConversation
        fields = [
            'id', 'mode', 'title', 'is_active',
            'started_at', 'updated_at',
            'message_count', 'last_message'
        ]
        read_only_fields = ['id', 'started_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'role': last_msg.role,
                'preview': last_msg.content[:100] if last_msg.content else '',
                'timestamp': last_msg.created_at
            }
        return None


class RashidProfileSerializer(serializers.ModelSerializer):
    """Serializer for Rashid user profile"""

    class Meta:
        model = RashidProfile
        fields = [
            'id', 'experience_level', 'current_role', 'current_situation',
            'target_role', 'skills', 'skill_gaps', 'constraints',
            'career_path', 'action_plan', 'onboarding_complete',
            'onboarding_step', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']


class RashidProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Rashid profile"""

    class Meta:
        model = RashidProfile
        fields = [
            'experience_level', 'current_role', 'current_situation',
            'target_role', 'skills', 'skill_gaps', 'constraints'
        ]


class RashidStoryBankSerializer(serializers.ModelSerializer):
    """Serializer for STAR stories"""

    class Meta:
        model = RashidStoryBank
        fields = [
            'id', 'situation', 'task', 'action', 'result',
            'reflection', 'tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StartConversationSerializer(serializers.Serializer):
    """Serializer for starting a new conversation"""
    mode = serializers.ChoiceField(
        choices=RashidConversation.MODES,
        default='general'
    )
    job_id = serializers.UUIDField(required=False, allow_null=True)


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message via REST API"""
    message = serializers.CharField(max_length=4000)


class RashidConfigSerializer(serializers.ModelSerializer):
    """Serializer for Rashid configuration (admin use)"""

    class Meta:
        model = RashidConfig
        fields = [
            'id', 'ai_provider', 'bedrock_region', 'bedrock_model_id',
            'anthropic_model', 'temperature', 'max_tokens',
            'system_prompt', 'dialect_config', 'onboarding_questions',
            'daily_token_limit', 'max_conversation_len',
            'auto_delete_after_days', 'is_active', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']