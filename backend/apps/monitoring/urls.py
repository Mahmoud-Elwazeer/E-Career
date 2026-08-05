"""
Monitoring & Observability URLs
"""
from django.urls import path
from apps.monitoring import views

app_name = 'monitoring'

urlpatterns = [
    # Health check endpoints
    path('health/', views.health_check, name='health-check'),
    path('health/detailed/', views.detailed_health_check, name='health-check-detailed'),
    
    # Metrics endpoint
    path('metrics/', views.metrics, name='metrics'),
    
    # Sentry test endpoint
    path('sentry-test/', views.sentry_test, name='sentry-test'),
    
    # Health check history
    path('health-history/', views.health_history, name='health-history'),
    
    # Performance metrics
    path('metrics/history/', views.metrics_history, name='metrics-history'),
    
    # Error logs
    path('errors/', views.error_logs, name='error-logs'),
    
    # Uptime records
    path('uptime/', views.uptime_records, name='uptime-records'),
]
