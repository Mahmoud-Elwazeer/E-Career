"""
Employer Portal URLs
Phase 3A: Employer self-service portal
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployerRegistrationView,
    EmployerProfileViewSet,
    JobPostingViewSet,
    JobApplicationViewSet,
    CandidateRankingViewSet,
    TalentDiscoveryViewSet,
    TalentPoolViewSet,
    company_search,
    ats_gap_analysis,
    EmployerTeamViewSet,
)

# Create router
router = DefaultRouter()
router.register(r'profile', EmployerProfileViewSet, basename='employer-profile')
router.register(r'jobs', JobPostingViewSet, basename='employer-jobs')
router.register(r'applications', JobApplicationViewSet, basename='employer-applications')
# KnockoutQuestion API removed — deprecated in favor of dynamic-form knockout
router.register(r'rankings', CandidateRankingViewSet, basename='employer-rankings')
router.register(r'talent-discoveries', TalentDiscoveryViewSet, basename='employer-talent-discoveries')
router.register(r'talent-pools', TalentPoolViewSet, basename='employer-talent-pools')
router.register(r'team', EmployerTeamViewSet, basename='employer-team')

urlpatterns = [
    # Registration
    path('register/', EmployerRegistrationView.as_view(), name='employer-register'),
    
    # Company search (for registration)
    path('companies/search/', company_search, name='company-search'),
    
    # ATS gap analysis
    path('postings/<uuid:posting_id>/ats-analysis/', ats_gap_analysis, name='ats-gap-analysis'),

    # Router URLs
    path('', include(router.urls)),
]