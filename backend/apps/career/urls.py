"""
Career Intelligence URLs

This module defines URL patterns for career intelligence API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CareerProfileViewSet,
    JobMatchingView,
    GoalSettingView,
    SkillGapAnalysisView,
    ProfileCompletenessView,
    TalentScoreView,
    InterviewSessionViewSet,
)

router = DefaultRouter()
router.register(r'profiles', CareerProfileViewSet, basename='career-profile')
router.register(r'interviews', InterviewSessionViewSet, basename='career-interview')

urlpatterns = [
    path('', include(router.urls)),
    
    # Semantic job matching endpoint
    path('jobs/matching/', JobMatchingView.as_view(), name='job-matching'),
    
    # Goal setting endpoint
    path('goals/', GoalSettingView.as_view(), name='goal-setting'),
    
    # Skill gap analysis endpoint
    path('skill-gap/', SkillGapAnalysisView.as_view(), name='skill-gap'),
    
    # Profile completeness endpoint
    path('completeness/', ProfileCompletenessView.as_view(), name='completeness'),
    
    # Talent score endpoint
    path('talent-score/', TalentScoreView.as_view(), name='talent-score'),
]