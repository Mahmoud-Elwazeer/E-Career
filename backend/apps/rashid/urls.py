"""
URL configuration for Rashid AI Assistant
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet,
    ProfileViewSet,
    StoryBankViewSet,
    get_usage_stats,
    get_config
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'stories', StoryBankViewSet, basename='story')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),

    # Additional endpoints
    path('usage/', get_usage_stats, name='rashid-usage'),
    path('config/', get_config, name='rashid-config'),
]