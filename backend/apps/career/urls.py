"""
Career Intelligence URLs
"""

app_name = "career"

from django.urls import path
from .views import (
    get_talent_scores,
    get_score_breakdown,
    get_score_trends,
    recalculate_scores,
    get_all_scores_with_actions,
    get_profile_completeness,
    recalculate_profile_completeness,
    get_skill_gap_analysis,
    TalentScoreViewSet,
    ScoreBreakdownViewSet,
    ScoreTrendsViewSet,
    CareerBrainView,
)
from .cv_parser_views import cv_status, cv_delete
from .views_onboarding import onboarding_progress
from .views_cover_letter import generate_cover_letter, cover_letter_detail, list_cover_letters
from .views_cv_tailor import cv_tailor_suggestions
from .views_recommendations import get_recommendations
from .goal_api import (
    CareerGoalListCreateView,
    CareerGoalDetailView,
    CareerGoalActionListCreateView,
    CareerGoalActionDetailView,
    CareerGoalMilestoneView,
    CareerGoalCompleteMilestoneView,
    CareerGoalProgressView,
    CareerGoalAnalyticsView,
)

urlpatterns = [
    # Talent score endpoints
    path('talent-score/', TalentScoreViewSet.as_view(), name='talent-score'),
    path('score-breakdown/', ScoreBreakdownViewSet.as_view(), name='score-breakdown'),
    path('score-trends/', ScoreTrendsViewSet.as_view(), name='score-trends'),

    # Scores API endpoints
    path('scores/', get_talent_scores, name='get-scores'),
    path('scores/breakdown/<str:dimension>/', get_score_breakdown, name='get-score-breakdown'),
    path('scores/trends/', get_score_trends, name='get-score-trends'),
    path('scores/recalculate/', recalculate_scores, name='recalculate-scores'),
    path('scores/with-actions/', get_all_scores_with_actions, name='get-scores-with-actions'),

    # Career Brain
    path('career-brain/', CareerBrainView.as_view(), name='career-brain'),

    # Career Goal endpoints (progress/analytics must come before <str:pk> to avoid matching)
    path('goals/', CareerGoalListCreateView.as_view(), name='career-goals-list-create'),
    path('goals/progress/', CareerGoalProgressView.as_view(), name='career-goals-progress'),
    path('goals/analytics/', CareerGoalAnalyticsView.as_view(), name='career-goals-analytics'),
    path('goals/<str:pk>/', CareerGoalDetailView.as_view(), name='career-goals-detail'),
    path('goals/<str:goal_id>/actions/', CareerGoalActionListCreateView.as_view(), name='career-goals-actions-list-create'),
    path('goals/<str:goal_id>/actions/<str:action_id>/', CareerGoalActionDetailView.as_view(), name='career-goals-actions-detail'),
    path('goals/<str:goal_id>/milestones/', CareerGoalMilestoneView.as_view(), name='career-goals-milestones'),
    path('goals/<str:goal_id>/milestones/<str:milestone_id>/complete/', CareerGoalCompleteMilestoneView.as_view(), name='career-goals-milestones-complete'),

    # Profile Completeness endpoints
    path('completeness/', get_profile_completeness, name='profile-completeness'),
    path('completeness/recalculate/', recalculate_profile_completeness, name='profile-completeness-recalculate'),

    # Skill Gap Analysis endpoints
    path('skill-gap/', get_skill_gap_analysis, name='skill-gap-analysis'),
    
    # CV Parser endpoints (upload is via /profile/upload_cv/)
    path('cv/status/', cv_status, name='cv-status'),
    path('cv/delete/', cv_delete, name='cv-delete'),

    # Onboarding endpoints
    path('onboarding/', onboarding_progress, name='onboarding-progress'),

    # Cover Letter endpoints
    path('cover-letters/', list_cover_letters, name='cover-letters-list'),
    path('cover-letter/<uuid:job_id>/', generate_cover_letter, name='cover-letter-generate'),
    path('cover-letter/<uuid:cover_letter_id>/detail/', cover_letter_detail, name='cover-letter-detail'),

    # CV Tailoring
    path('cv-tailor/<uuid:job_id>/', cv_tailor_suggestions, name='cv-tailor'),

    # Recommendations
    path('recommendations/', get_recommendations, name='recommendations'),

    # Test-expected URL name aliases
    path('profile/', get_profile_completeness, name='profile-detail'),
    path('goals-list/', CareerGoalListCreateView.as_view(), name='goals-list'),
    path('goals-detail/<str:pk>/', CareerGoalDetailView.as_view(), name='goals-detail'),
    path('goals/<str:pk>/add-milestone/', CareerGoalMilestoneView.as_view(), name='goals-add-milestone'),
    path('skills/', get_skill_gap_analysis, name='skills-list'),
    path('interview-sessions/', TalentScoreViewSet.as_view(), name='interview-sessions-list'),
    path('interview-sessions/<str:pk>/', TalentScoreViewSet.as_view(), name='interview-sessions-detail'),
]
