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
    TalentScoreViewSet,
    ScoreBreakdownViewSet,
    ScoreTrendsViewSet,
    CareerBrainView,
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
]
