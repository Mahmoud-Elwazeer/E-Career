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
    company_search,
)

# Create router
router = DefaultRouter()
router.register(r'profile', EmployerProfileViewSet, basename='employer-profile')
router.register(r'jobs', JobPostingViewSet, basename='employer-jobs')
router.register(r'applications', JobApplicationViewSet, basename='employer-applications')

urlpatterns = [
    # Registration
    path('register/', EmployerRegistrationView.as_view(), name='employer-register'),
    
    # Company search (for registration)
    path('companies/search/', company_search, name='company-search'),
    
    # Router URLs
    path('', include(router.urls)),
]