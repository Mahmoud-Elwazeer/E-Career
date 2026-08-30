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
    ats_score,
    match_breakdown,
    job_tailor,
    TalentScoreViewSet,
    ScoreBreakdownViewSet,
    ScoreTrendsViewSet,
    CareerBrainView,
)
from .views_api import (
    CareerProfileDetailView,
    ProfileCompletenessView,
    UserSkillListView,
    LearningListView,
    TalentScoreDetailView,
    TalentScoreBreakdownView,
    InterviewSessionListCreateView,
    InterviewSessionDetailView,
    WrappedGoalListCreateView,
    WrappedGoalDetailView,
    GoalAddMilestoneView,
    GoalCompleteMilestoneView,
    CareerBrainDetailView,
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

    # Career Goal endpoints (progress/analytics must come before <str:pk>)
    path('goals/', CareerGoalListCreateView.as_view(), name='career-goals-list-create'),
    path('goals/progress/', CareerGoalProgressView.as_view(), name='career-goals-progress'),
    path('goals/analytics/', CareerGoalAnalyticsView.as_view(), name='career-goals-analytics'),
    path('goals/<str:pk>/', CareerGoalDetailView.as_view(), name='career-goals-detail'),
    path('goals/<str:goal_id>/actions/', CareerGoalActionListCreateView.as_view(), name='career-goals-actions-list-create'),
    path('goals/<str:goal_id>/actions/<str:action_id>/', CareerGoalActionDetailView.as_view(), name='career-goals-actions-detail'),
    path('goals/<str:goal_id>/milestones/', CareerGoalMilestoneView.as_view(), name='career-goals-milestones'),
    path('goals/<str:goal_id>/milestones/<str:milestone_id>/complete/', CareerGoalCompleteMilestoneView.as_view(), name='career-goals-milestones-complete'),

    # Profile Completeness endpoints
    path('completeness/', ProfileCompletenessView.as_view(), name='profile-completeness'),
    path('completeness/recalculate/', recalculate_profile_completeness, name='profile-completeness-recalculate'),

    # Skill Gap Analysis endpoints
    path('skill-gap/', get_skill_gap_analysis, name='skill-gap-analysis'),

    # CV Parser endpoints
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

    # ATS Compatibility Scoring
    path('ats-score/', ats_score, name='ats-score'),

    # Match Score Breakdown (5.1)
    path('jobs/<int:job_id>/match-breakdown/', match_breakdown, name='match-breakdown'),

    # Job-Specific Resume Tailoring (5.2)
    path('jobs/<int:job_id>/tailor/', job_tailor, name='job-tailor'),

    # Recommendations
    path('recommendations/', get_recommendations, name='recommendations'),

    # ── Test-expected URL aliases (envelope-wrapped views) ──────────────────
    path('profile/', CareerProfileDetailView.as_view(), name='profile-detail'),
    path('skills/', UserSkillListView.as_view(), name='skills-list'),
    path('learning/', LearningListView.as_view(), name='learning-list'),
    path('talent-score/detail/', TalentScoreDetailView.as_view(), name='talent-score-detail'),
    path('talent-score/breakdown/', TalentScoreBreakdownView.as_view(), name='talent-score-breakdown'),
    path('interview-sessions/', InterviewSessionListCreateView.as_view(), name='interview-sessions-list'),
    path('interview-sessions/<str:pk>/', InterviewSessionDetailView.as_view(), name='interview-sessions-detail'),
    path('goals-list/', WrappedGoalListCreateView.as_view(), name='goals-list'),
    path('goals-detail/<str:pk>/', WrappedGoalDetailView.as_view(), name='goals-detail'),
    path('goals/<str:pk>/add-milestone/', GoalAddMilestoneView.as_view(), name='goals-add-milestone'),
    path('goals/<str:pk>/complete-milestone/', GoalCompleteMilestoneView.as_view(), name='goals-complete-milestone'),
    path('career-brain/detail/', CareerBrainDetailView.as_view(), name='career-brain-detail'),
]
