"""
Interviews URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InterviewViewSet, get_interview_stats,
    generate_coding_problem, execute_coding_solution, evaluate_coding_solution,
)

app_name = "interviews"

router = DefaultRouter()
router.register(r'sessions', InterviewViewSet, basename='interview-sessions')

urlpatterns = [
    path('', include(router.urls)),
    # Direct routes matching frontend URLs (/api/v1/interviews/start/, etc.)
    path('start/', InterviewViewSet.as_view({'post': 'start'}), name='interview-start'),
    path('<int:pk>/answer/', InterviewViewSet.as_view({'post': 'answer'}), name='interview-answer'),
    path('<int:pk>/complete/', InterviewViewSet.as_view({'post': 'complete'}), name='interview-complete'),
    path('<int:pk>/voice-answer/', InterviewViewSet.as_view({'post': 'voice_answer'}), name='interview-voice-answer'),
    path('<int:pk>/question-audio/<int:question_index>/', InterviewViewSet.as_view({'get': 'question_audio'}), name='interview-question-audio'),
    path('history/', InterviewViewSet.as_view({'get': 'history'}), name='interview-history'),
    path('stats/', get_interview_stats, name='interview-stats'),
    # Coding interview endpoints
    path('coding-problem/', generate_coding_problem, name='coding-problem'),
    path('coding-solution/', execute_coding_solution, name='coding-solution'),
    path('coding-evaluate/', evaluate_coding_solution, name='coding-evaluate'),
]