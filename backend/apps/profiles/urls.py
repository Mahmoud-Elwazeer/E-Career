"""
Profile URL configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProfileViewSet, JobMatchViewSet,
    get_job_recommendations, get_job_match_breakdown, get_similar_jobs
)

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'matches', JobMatchViewSet, basename='job-match')

urlpatterns = [
    path('', include(router.urls)),
    
    # Recommendation endpoints
    path('recommendations/', get_job_recommendations, name='job-recommendations'),
    path('jobs/<int:job_id>/match-breakdown/', get_job_match_breakdown, name='job-match-breakdown'),
    path('jobs/<int:job_id>/similar/', get_similar_jobs, name='similar-jobs'),
]
