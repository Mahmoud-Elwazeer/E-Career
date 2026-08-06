"""
Assessment Platform URLs

This module defines the URL patterns for the assessment platform functionality.
"""

from django.urls import path
from .views import (
    get_user_assessments,
    get_assessment_attempts,
    start_assessment,
    submit_assessment,
    get_skill_badges,
    create_skill_badge,
    get_assessment_templates,
    AssessmentViewSet,
    AssessmentQuestionViewSet,
    AssessmentAttemptViewSet,
    SkillBadgeViewSet,
    AssessmentTemplateViewSet,
)

urlpatterns = [
    # Assessment endpoints
    path('assessments/', get_user_assessments, name='get-user-assessments'),
    path('assessments/start/', start_assessment, name='start-assessment'),
    path('assessments/<str:attempt_id>/submit/', submit_assessment, name='submit-assessment'),
    
    # Assessment attempts
    path('attempts/', get_assessment_attempts, name='get-assessment-attempts'),
    
    # Skill badges
    path('badges/', get_skill_badges, name='get-skill-badges'),
    path('badges/create/', create_skill_badge, name='create-skill-badge'),
    
    # Assessment templates
    path('templates/', get_assessment_templates, name='get-assessment-templates'),
]
