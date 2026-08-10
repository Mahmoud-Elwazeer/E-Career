"""
Onboarding Serializers
"""
from rest_framework import serializers
from .models import OnboardingProgress


class OnboardingProgressSerializer(serializers.ModelSerializer):
    """Serializer for onboarding progress."""

    is_complete = serializers.ReadOnlyField()

    class Meta:
        model = OnboardingProgress
        fields = [
            'id',
            'steps_completed',
            'career_stage',
            'primary_interest',
            'completed_at',
            'is_complete',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']


class OnboardingStepSerializer(serializers.Serializer):
    """Serializer for marking a step complete."""

    step_id = serializers.ChoiceField(
        choices=['role', 'basic_info', 'career_stage', 'cv_upload', 'preferences', 'goals']
    )

    # Optional data for specific steps
    career_stage = serializers.ChoiceField(
        choices=['student', 'junior', 'mid', 'senior', 'exec', 'career_change'],
        required=False,
        allow_blank=True
    )
    primary_interest = serializers.ChoiceField(
        choices=['find_job', 'explore', 'improve_skills', 'prepare_interviews'],
        required=False,
        allow_blank=True
    )
