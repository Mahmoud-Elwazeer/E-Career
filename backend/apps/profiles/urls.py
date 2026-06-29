"""
Profile URL configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet, JobMatchViewSet

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'matches', JobMatchViewSet, basename='job-match')

urlpatterns = [
    path('', include(router.urls)),
]