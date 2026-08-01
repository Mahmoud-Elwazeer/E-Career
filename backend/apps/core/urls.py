"""
Core app URLs for Rule Engine, Feature Flags, and GitHub Integration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    get_rules,
    test_rules,
    get_feature_flags,
    check_feature_flag,
    github_connections,
    portfolio_analyses,
    seed_rules,
    RuleViewSet,
    FeatureFlagViewSet,
    GitHubConnectionViewSet,
    PortfolioAnalysisViewSet,
)

router = DefaultRouter()
router.register(r'rules', RuleViewSet, basename='core-rules')
router.register(r'feature-flags', FeatureFlagViewSet, basename='core-feature-flags')
router.register(r'github', GitHubConnectionViewSet, basename='core-github')
router.register(r'portfolio', PortfolioAnalysisViewSet, basename='core-portfolio')

urlpatterns = [
    path('', include(router.urls)),
    
    # Rules endpoints
    path('rules/', get_rules, name='get-rules'),
    path('rules/test/', test_rules, name='test-rules'),
    path('rules/seed/', seed_rules, name='seed-rules'),
    
    # Feature flags endpoints
    path('feature-flags/', get_feature_flags, name='get-feature-flags'),
    path('feature-flags/<str:key>/', check_feature_flag, name='check-feature-flag'),
    
    # GitHub endpoints
    path('github/', github_connections, name='github-connections'),
    
    # Portfolio analysis endpoints
    path('portfolio/', portfolio_analyses, name='portfolio-analyses'),
]