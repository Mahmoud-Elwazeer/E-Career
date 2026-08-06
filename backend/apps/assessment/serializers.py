"""
Assessment Platform Serializers

This module defines DRF serializers for assessments, questions, and results.
"""

from rest_framework import serializers
from django.conf import settings
from .models import (
    Assessment,
    AssessmentQuestion,
    AssessmentAttempt,
    SkillBadge,
    AssessmentTemplate,
    AssessmentResult,
)


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    """Serializer for AssessmentQuestion model."""
    
    class Meta:
        model = AssessmentQuestion
        fields = [
            'id',
            'assessment',
            'question_type',
            'title',
            'description',
            'starter_code',
            'test_cases',
            'options',
            'correct_answer',
            'points',
            'order',
        ]
        read_only_fields = ['order']


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model."""
    
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    questions = AssessmentQuestionSerializer(many=True, read_only=True)
    skills = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Assessment
        fields = [
            'id',
            'created_by',
            'created_by_email',
            'assessment_type',
            'title',
            'description',
            'skills',
            'difficulty',
            'time_limit_minutes',
            'max_attempts',
            'passing_score',
            'total_points',
            'status',
            'questions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.skills.models import Skill
        self.fields['skills'].queryset = Skill.objects.all()


class AssessmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Assessment."""
    
    class Meta:
        model = Assessment
        fields = [
            'assessment_type',
            'title',
            'description',
            'skills',
            'difficulty',
            'time_limit_minutes',
            'max_attempts',
            'passing_score',
            'total_points',
            'status',
        ]


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    """Serializer for AssessmentAttempt model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    
    class Meta:
        model = AssessmentAttempt
        fields = [
            'id',
            'user',
            'user_email',
            'assessment',
            'assessment_title',
            'attempt_number',
            'status',
            'started_at',
            'submitted_at',
            'time_spent_minutes',
            'score',
            'passed',
            'answers',
            'feedback',
        ]
        read_only_fields = ['created_at']


class AssessmentAttemptCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AssessmentAttempt."""
    
    class Meta:
        model = AssessmentAttempt
        fields = [
            'assessment',
        ]


class SkillBadgeSerializer(serializers.ModelSerializer):
    """Serializer for SkillBadge model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    
    class Meta:
        model = SkillBadge
        fields = [
            'id',
            'user',
            'user_email',
            'skill',
            'skill_name',
            'level',
            'verification_method',
            'score',
            'expires_at',
            'earned_at',
            'verified_at',
        ]
        read_only_fields = ['earned_at', 'verified_at']


class AssessmentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for AssessmentTemplate model."""
    
    class Meta:
        model = AssessmentTemplate
        fields = [
            'id',
            'title',
            'description',
            'target_role',
            'time_limit_minutes',
            'max_attempts',
            'passing_score',
            'difficulty',
            'assessment_type',
            'status',
            'used_count',
        ]


class AssessmentResultSerializer(serializers.ModelSerializer):
    """Serializer for AssessmentResult model."""
    
    attempt_details = serializers.SerializerMethodField()
    
    class Meta:
        model = AssessmentResult
        fields = [
            'id',
            'attempt',
            'attempt_details',
            'total_score',
            'max_score',
            'question_scores',
            'time_per_question',
            'ai_analysis',
            'strengths',
            'weaknesses',
            'recommendations',
        ]
        read_only_fields = ['created_at']
    
    def get_attempt_details(self, obj):
        return {
            'user_email': obj.attempt.user.email,
            'assessment_title': obj.attempt.assessment.title,
            'score': obj.attempt.score,
            'passed': obj.attempt.passed,
        }


class AssessmentSubmitSerializer(serializers.Serializer):
    """Serializer for submitting assessment answers."""
    
    answers = serializers.JSONField()
    time_spent_minutes = serializers.IntegerField(required=False)


class SkillBadgeRequestSerializer(serializers.Serializer):
    """Serializer for skill badge request."""
    
    skill_id = serializers.UUIDField()
    level = serializers.CharField(required=False)