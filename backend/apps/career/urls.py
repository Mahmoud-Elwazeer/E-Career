"""
Career Intelligence URLs
"""

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

    # Career Goal endpoints
    path('goals/', CareerGoalListCreateView.as_view(), name='career-goals-list-create'),
    path('goals/<str:pk>/', CareerGoalDetailView.as_view(), name='career-goals-detail'),
    path('goals/<str:goal_id>/actions/', CareerGoalActionListCreateView.as_view(), name='career-goals-actions-list-create'),
    path('goals/<str:goal_id>/actions/<str:action_id>/', CareerGoalActionDetailView.as_view(), name='career-goals-actions-detail'),
    path('goals/<str:goal_id>/milestones/', CareerGoalMilestoneView.as_view(), name='career-goals-milestones'),
    path('goals/<str:goal_id>/milestones/<str:milestone_id>/complete/', CareerGoalCompleteMilestoneView.as_view(), name='career-goals-milestones-complete'),
    path('goals/progress/', CareerGoalProgressView.as_view(), name='career-goals-progress'),
    path('goals/analytics/', CareerGoalAnalyticsView.as_view(), name='career-goals-analytics'),

    # Profile Completeness endpoints
    path('completeness/', get_profile_completeness, name='profile-completeness'),
    path('completeness/recalculate/', recalculate_profile_completeness, name='profile-completeness-recalculate'),

    # Skill Gap Analysis endpoints
    path('skill-gap/', get_skill_gap_analysis, name='skill-gap-analysis'),
]
