"""
Resume Builder Serializers

This module contains Django REST Framework serializers for resume models.
"""

import logging
from rest_framework import serializers
from .models import (
    ResumeTemplate,
    Resume,
    ResumeExport,
    ProfileSection,
    SkillVerification,
)

logger = logging.getLogger(__name__)


class ResumeTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ResumeTemplate model."""
    
    class Meta:
        model = ResumeTemplate
        fields = [
            'id',
            'title',
            'description',
            'category',
            'preview_image',
            'is_premium',
            'is_active',
            'used_count',
            'rating',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['used_count', 'rating', 'created_at', 'updated_at']


class ResumeSerializer(serializers.ModelSerializer):
    """Serializer for Resume model."""
    
    template = ResumeTemplateSerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Resume
        fields = [
            'id',
            'template',
            'template_id',
            'title',
            'personal_info',
            'summary',
            'experience',
            'education',
            'skills',
            'projects',
            'certifications',
            'languages',
            'interests',
            'is_public',
            'is_active',
            'privacy_settings',
            'created_at',
            'updated_at',
            'last_viewed_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_viewed_at']


class ResumeExportSerializer(serializers.ModelSerializer):
    """Serializer for ResumeExport model."""
    
    resume = ResumeSerializer(read_only=True)
    
    class Meta:
        model = ResumeExport
        fields = [
            'id',
            'resume',
            'format',
            'file_url',
            'file_size',
            'status',
            'error_message',
            'created_at',
            'completed_at',
        ]
        read_only_fields = [
            'resume',
            'file_url',
            'file_size',
            'status',
            'error_message',
            'created_at',
            'completed_at',
        ]


class ProfileSectionSerializer(serializers.ModelSerializer):
    """Serializer for ProfileSection model."""
    
    class Meta:
        model = ProfileSection
        fields = [
            'id',
            'user',
            'section_type',
            'title',
            'content',
            'order',
            'is_visible',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class SkillVerificationSerializer(serializers.ModelSerializer):
    """Serializer for SkillVerification model."""
    
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = SkillVerification
        fields = [
            'id',
            'user',
            'skill_name',
            'skill_category',
            'verification_method',
            'evidence_url',
            'evidence_text',
            'score',
            'level',
            'expires_at',
            'verified_at',
            'verified_by',
        ]
        read_only_fields = ['user', 'verified_at', 'verified_by']


class ResumeCreateSerializer(serializers.Serializer):
    """Serializer for creating a new resume."""
    
    template_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=200, required=False, default="My Resume")
    personal_info = serializers.JSONField(required=False, default=dict)
    summary = serializers.CharField(required=False, default="")
    experience = serializers.JSONField(required=False, default=list)
    education = serializers.JSONField(required=False, default=list)
    skills = serializers.JSONField(required=False, default=list)
    projects = serializers.JSONField(required=False, default=list)
    certifications = serializers.JSONField(required=False, default=list)
    languages = serializers.JSONField(required=False, default=list)
    interests = serializers.JSONField(required=False, default=list)
    is_public = serializers.BooleanField(required=False, default=False)
    privacy_settings = serializers.JSONField(required=False, default=dict)


class ResumeUpdateSerializer(serializers.Serializer):
    """Serializer for updating a resume."""
    
    title = serializers.CharField(max_length=200, required=False)
    personal_info = serializers.JSONField(required=False)
    summary = serializers.CharField(required=False)
    experience = serializers.JSONField(required=False)
    education = serializers.JSONField(required=False)
    skills = serializers.JSONField(required=False)
    projects = serializers.JSONField(required=False)
    certifications = serializers.JSONField(required=False)
    languages = serializers.JSONField(required=False)
    interests = serializers.JSONField(required=False)
    is_public = serializers.BooleanField(required=False)
    privacy_settings = serializers.JSONField(required=False)


class ResumeExportRequestSerializer(serializers.Serializer):
    """Serializer for requesting a resume export."""
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('html', 'HTML'),
        ('json', 'JSON'),
    ]
    
    format = serializers.ChoiceField(choices=FORMAT_CHOICES)
    include_private = serializers.BooleanField(required=False, default=False)