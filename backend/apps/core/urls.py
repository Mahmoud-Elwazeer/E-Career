"""
Core app URLs for Rule Engine, Feature Flags, and GitHub Integration.
"""

from django.urls import path
from .views import (
    get_rules,
    test_rules,
    get_feature_flags,
    check_feature_flag,
    github_connections,
    portfolio_analyses,
    seed_rules,
    export_user_data,
    delete_user_data,
    anonymize_user_data,
    GDPRDataExportViewSet,
    GDPRDataDeletionViewSet,
    GDPRDataAnonymizationViewSet,
)

urlpatterns = [
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

    # GDPR compliance endpoints
    path('gdpr/export/', GDPRDataExportViewSet.as_view(), name='gdpr-export'),
    path('gdpr/delete/', GDPRDataDeletionViewSet.as_view(), name='gdpr-delete'),
    path('gdpr/anonymize/', GDPRDataAnonymizationViewSet.as_view(), name='gdpr-anonymize'),
]
