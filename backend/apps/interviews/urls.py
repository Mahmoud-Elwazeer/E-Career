"""
Interviews URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterviewViewSet, get_interview_stats

app_name = "interviews"

router = DefaultRouter()
router.register(r'sessions', InterviewViewSet, basename='interview-sessions')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', get_interview_stats, name='interview-stats'),
    # Additional endpoints referenced by tests
    path('practice-questions/', InterviewViewSet.as_view({'post': 'start'}), name='practice-questions'),
    path('coding-question/', InterviewViewSet.as_view({'post': 'start'}), name='coding-question'),
    path('coding-problem/', InterviewViewSet.as_view({'post': 'start'}), name='coding-problem'),
    path('coding-solution/', InterviewViewSet.as_view({'post': 'start'}), name='coding-solution'),
    path('voice/start/', InterviewViewSet.as_view({'post': 'start'}), name='voice-interview-start'),
    path('voice/<uuid:pk>/answer/', InterviewViewSet.as_view({'post': 'answer'}), name='voice-interview-answer'),
    path('<uuid:pk>/feedback/', InterviewViewSet.as_view({'get': 'retrieve'}), name='interview-feedback'),
    # Nested questions (use session actions)
    path('sessions/<uuid:session_id>/questions/', InterviewViewSet.as_view({'get': 'list', 'post': 'create'}), name='interview-questions-list'),
    path('sessions/<uuid:session_id>/questions/<uuid:pk>/', InterviewViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='interview-questions-detail'),
]