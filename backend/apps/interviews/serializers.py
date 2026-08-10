"""
Interviews Serializers
"""
from rest_framework import serializers
from .models import InterviewSession, InterviewQuestion


class InterviewSessionSerializer(serializers.ModelSerializer):
    """Serializer for InterviewSession model."""
    
    class Meta:
        model = InterviewSession
        fields = [
            'id', 'user', 'interview_type', 'target_role', 
            'difficulty', 'mode', 'status', 'overall_score',
            'score_breakdown', 'feedback_summary', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'user', 'started_at', 'completed_at']


class StartInterviewSerializer(serializers.Serializer):
    """Serializer for starting a new interview session."""

    interview_type = serializers.ChoiceField(
        choices=['technical', 'behavioral', 'coding', 'system_design', 'case_study']
    )
    target_role = serializers.CharField(max_length=200)
    difficulty = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        default='medium'
    )
    mode = serializers.ChoiceField(
        choices=['text', 'voice'],
        default='text'
    )
    job_id = serializers.UUIDField(required=False, allow_null=True)


class AnswerQuestionSerializer(serializers.Serializer):
    """Serializer for answering a question."""
    
    answer = serializers.CharField(style={'base_template': 'textarea.html'})


class CompleteInterviewSerializer(serializers.Serializer):
    """Serializer for completing an interview session."""
    
    pass


class InterviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for InterviewQuestion model."""
    
    class Meta:
        model = InterviewQuestion
        fields = [
            'id', 'session', 'question_index', 'question_text',
            'answer_text', 'score', 'feedback', 'score_details',
            'answered_at'
        ]
        read_only_fields = ['id', 'session', 'question_index', 'answered_at']


class InterviewHistorySerializer(serializers.ModelSerializer):
    """Serializer for interview history list."""
    
    class Meta:
        model = InterviewSession
        fields = [
            'id', 'interview_type', 'target_role', 'difficulty',
            'overall_score', 'status', 'started_at'
        ]