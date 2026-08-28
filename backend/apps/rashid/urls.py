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
    get_config,
    execute_tool_endpoint,
    list_tools
)

app_name = "rashid"

# Router for ViewSets
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversations')
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'stories', StoryBankViewSet, basename='star-stories')

urlpatterns = [
    # Profile endpoint without pk (uses current user)
    path('my-profile/', ProfileViewSet.as_view({
        'get': 'retrieve',
        'post': 'create',
        'patch': 'partial_update',
        'put': 'update',
    }), name='profile-detail'),

    # ViewSet routes
    path('', include(router.urls)),

    # Additional endpoints
    path('usage/', get_usage_stats, name='usage-detail'),
    path('usage/history/', get_usage_stats, name='usage-history'),
    path('config/', get_config, name='config-detail'),

    # Tool endpoints
    path('tools/', list_tools, name='rashid-tools'),
    path('tools/execute/', execute_tool_endpoint, name='rashid-tool-execute'),

    # Job analysis (test-expected)
    path('analyze-job/<slug:job_slug>/', execute_tool_endpoint, name='analyze-job'),
]
