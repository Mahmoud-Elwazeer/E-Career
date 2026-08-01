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
    get_talent_scores,
    get_score_breakdown,
    get_score_trends,
    recalculate_scores,
    get_all_scores_with_actions,
    CareerBrainView,
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
    
    # New Scores API endpoints (Week 9)
    # GET /api/v1/scores/ - Get all scores with breakdowns
    path('scores/', get_talent_scores, name='get-scores'),
    
    # GET /api/v1/scores/breakdown/<dimension>/ - Get detailed breakdown for a dimension
    path('scores/breakdown/<str:dimension>/', get_score_breakdown, name='get-score-breakdown'),
    
    # GET /api/v1/scores/trends/ - Get score trends over time
    path('scores/trends/', get_score_trends, name='get-score-trends'),
    
    # POST /api/v1/scores/recalculate/ - Trigger score recalculation
    path('scores/recalculate/', recalculate_scores, name='recalculate-scores'),
    
    # GET /api/v1/scores/with-actions/ - Get all scores with recommended actions
    path('scores/with-actions/', get_all_scores_with_actions, name='get-scores-with-actions'),
    
    # Career Brain endpoints (Week 10)
    path('career-brain/', CareerBrainView.as_view(), name='career-brain'),
]
