"""
Career Intelligence Serializers

This module defines DRF serializers for career profile, skills, learning,
and talent intelligence features.
"""

from rest_framework import serializers
from django.conf import settings
from apps.skills.models import Skill
from .models import (
    CareerProfile,
    CareerUserSkill,
    CareerLearning,
    TalentScore,
    InterviewSession,
    CareerBrain,
    CareerGoal,
    CareerGoalAction,
    LearningResource,
)


class CareerUserSkillSerializer(serializers.ModelSerializer):
    """Serializer for CareerUserSkill model."""
    
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_id = serializers.CharField(source='skill.id', read_only=True)
    
    class Meta:
        model = CareerUserSkill
        fields = [
            'id',
            'skill_id',
            'skill_name',
            'proficiency',
            'years_experience',
            'last_used_at',
            'verified',
            'verification_source',
            'source',
            'confidence',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class CareerUserSkillCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating CareerUserSkill."""
    
    skill_id = serializers.UUIDField()
    
    class Meta:
        model = CareerUserSkill
        fields = [
            'skill_id',
            'proficiency',
            'years_experience',
            'last_used_at',
            'verified',
            'verification_source',
            'source',
            'confidence',
        ]


class CareerProfileSerializer(serializers.ModelSerializer):
    """Serializer for CareerProfile model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    user_skills = CareerUserSkillSerializer(
        source='user.career_userskills', many=True, read_only=True
    )

    class Meta:
        model = CareerProfile
        fields = [
            'id',
            'user_id',
            'user_email',
            'cv_file',
            'cv_parsed_data',
            'cv_parse_status',
            'cv_parsed_at',
            'experience_years',
            'current_role',
            'current_company',
            'target_roles',
            'target_locations',
            'target_salary_min',
            'target_salary_currency',
            'open_to_remote',
            'github_username',
            'github_data',
            'portfolio_url',
            'portfolio_analysis',
            'linkedin_data',
            'alert_frequency',
            'min_match_score',
            'completeness_score',
            'last_active_at',
            'skills',
            'user_skills',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'cv_parse_status',
            'cv_parsed_at',
            'completeness_score',
            'last_active_at',
            'created_at',
            'updated_at',
        ]


class CareerProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating CareerProfile."""
    
    class Meta:
        model = CareerProfile
        fields = [
            'experience_years',
            'current_role',
            'current_company',
            'target_roles',
            'target_locations',
            'target_salary_min',
            'target_salary_currency',
            'open_to_remote',
            'github_username',
            'portfolio_url',
            'alert_frequency',
            'min_match_score',
        ]


class CareerLearningSerializer(serializers.ModelSerializer):
    """Serializer for CareerLearning model."""
    
    class Meta:
        model = CareerLearning
        fields = [
            'id',
            'title',
            'platform',
            'skills_gained',
            'completed_at',
            'certificate_url',
            'course_id',
            'duration_hours',
            'difficulty_level',
            'created_at',
        ]
        read_only_fields = ['created_at']


class TalentScoreSerializer(serializers.ModelSerializer):
    """Serializer for TalentScore model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    dimension_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = TalentScore
        fields = [
            'id',
            'user_email',
            'overall_score',
            'skill_score',
            'experience_score',
            'education_score',
            'portfolio_score',
            'interview_score',
            'growth_score',
            'communication_score',
            'ai_confidence',
            'explanations',
            'score_history',
            'last_calculated_at',
            'dimension_breakdown',
        ]
        read_only_fields = ['last_calculated_at']
    
    def get_dimension_breakdown(self, obj):
        return obj.get_dimension_breakdown()


class InterviewSessionSerializer(serializers.ModelSerializer):
    """Serializer for InterviewSession model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = InterviewSession
        fields = [
            'id',
            'user_email',
            'interview_type',
            'target_role',
            'target_company',
            'mode',
            'difficulty',
            'questions',
            'overall_score',
            'dimension_scores',
            'recording_url',
            'transcript',
            'started_at',
            'completed_at',
            'duration_seconds',
            'created_at',
        ]
        read_only_fields = ['created_at']


class InterviewSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating InterviewSession."""
    
    class Meta:
        model = InterviewSession
        fields = [
            'interview_type',
            'target_role',
            'target_company',
            'mode',
            'difficulty',
        ]


class ProfileCompletenessSerializer(serializers.Serializer):
    """Serializer for profile completeness response."""
    
    score = serializers.FloatField()
    missing_fields = serializers.ListField(child=serializers.CharField())
    total_fields = serializers.IntegerField()
    completed_fields = serializers.IntegerField()


class SkillGapSerializer(serializers.Serializer):
    """Serializer for skill gap analysis response."""
    
    target_role = serializers.CharField()
    missing_skills = serializers.ListField(
        child=serializers.DictField()
    )
    skill_importance = serializers.DictField()
    learning_resources = serializers.ListField(
        child=serializers.DictField()
    )


class ScoreBreakdownSerializer(serializers.Serializer):
    """Serializer for score breakdown response."""
    
    value = serializers.FloatField()
    confidence = serializers.FloatField()
    grade = serializers.CharField()
    trend = serializers.CharField()
    evidence = serializers.ListField(child=serializers.DictField())
    explanation = serializers.CharField()
    actions = serializers.ListField(child=serializers.DictField())
    breakdown = serializers.DictField()


class ScoreTrendSerializer(serializers.Serializer):
    """Serializer for score trend response."""
    
    dimension = serializers.CharField()
    current_value = serializers.FloatField()
    previous_value = serializers.FloatField()
    change = serializers.FloatField()
    direction = serializers.CharField()


class ScoreActionsSerializer(serializers.Serializer):
    """Serializer for score actions response."""
    
    overall_score = serializers.FloatField()
    overall_grade = serializers.CharField()
    dimensions = serializers.DictField()
    explanations = serializers.DictField()
    actions = serializers.ListField(child=serializers.DictField())
    confidence = serializers.FloatField()


class CareerBrainSerializer(serializers.ModelSerializer):
    """Serializer for CareerBrain model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = CareerBrain
        fields = [
            'id',
            'user_email',
            'identity',
            'skills',
            'goals',
            'preferences',
            'learning',
            'history_summary',
            'ai_observations',
            'confidence_score',
            'last_updated_at',
        ]
        read_only_fields = ['last_updated_at', 'user_email']


# ============================================================================
# Career Goal Serializers
# ============================================================================


class CareerGoalSerializer(serializers.ModelSerializer):
    """Serializer for CareerGoal model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = CareerGoal
        fields = [
            'id',
            'user_email',
            'title',
            'description',
            'goal_type',
            'target_role',
            'target_skill',
            'target_salary_min',
            'target_company',
            'target_certification',
            'target_date',
            'status',
            'priority',
            'progress',
            'milestones',
            'completed_at',
            'archived_at',
            'created_at',
        ]
        read_only_fields = ['created_at', 'completed_at', 'archived_at', 'user_email']


class CareerGoalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CareerGoal."""
    
    class Meta:
        model = CareerGoal
        fields = [
            'title',
            'description',
            'goal_type',
            'target_role',
            'target_skill',
            'target_salary_min',
            'target_company',
            'target_certification',
            'target_date',
            'priority',
        ]
    
    def create(self, validated_data):
        user = self.context.get('user')
        return CareerGoal.objects.create(user=user, **validated_data)


class CareerGoalActionSerializer(serializers.ModelSerializer):
    """Serializer for CareerGoalAction model."""
    
    goal_title = serializers.CharField(source='goal.title', read_only=True)
    
    class Meta:
        model = CareerGoalAction
        fields = [
            'id',
            'goal',
            'goal_title',
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'completed_at',
            'category',
            'created_at',
        ]
        read_only_fields = ['created_at', 'completed_at', 'goal']


class CareerGoalActionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CareerGoalAction."""
    
    class Meta:
        model = CareerGoalAction
        fields = [
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'category',
        ]
    
    def create(self, validated_data):
        user = self.context.get('user')
        goal = self.context.get('goal')
        return CareerGoalAction.objects.create(goal=goal, **validated_data)


class LearningResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningResource
        fields = [
            'id', 'title', 'url', 'platform', 'skill_tags',
            'difficulty_level', 'duration_hours', 'is_free',
            'rating', 'description', 'is_active', 'created_at',
        ]
        read_only_fields = ['created_at']
