"""
Interviews URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterviewViewSet, get_interview_stats

router = DefaultRouter()
router.register(r'interviews', InterviewViewSet, basename='interview')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', get_interview_stats, name='interview-stats'),
]