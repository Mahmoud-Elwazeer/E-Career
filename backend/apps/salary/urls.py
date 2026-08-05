"""
Salary Intelligence URLs

This module defines the URL patterns for the salary intelligence functionality.
"""

from django.urls import path
from .views import (
    get_salary_benchmark,
    get_market_rates,
    get_salary_insights,
    get_salary_alerts,
    mark_alert_as_read,
    SalaryDataViewSet,
    MarketRateViewSet,
    SalaryBenchmarkViewSet,
    SalaryInsightViewSet,
    SalaryAlertViewSet,
)

urlpatterns = [
    # Salary benchmark endpoint
    path('benchmark/', get_salary_benchmark, name='salary-benchmark'),
    
    # Market rates endpoint
    path('market-rates/', get_market_rates, name='salary-market-rates'),
    
    # Salary insights endpoint
    path('insights/', get_salary_insights, name='salary-insights'),
    
    # Salary alerts endpoints
    path('alerts/', get_salary_alerts, name='salary-alerts'),
    path('alerts/<str:alert_id>/read/', mark_alert_as_read, name='salary-mark-alert-read'),
    
    # ViewSet endpoints
    path('salary-data/', SalaryDataViewSet.as_view(), name='salary-data'),
    path('market-rates/', MarketRateViewSet.as_view(), name='market-rates'),
    path('benchmarks/', SalaryBenchmarkViewSet.as_view(), name='salary-benchmarks'),
    path('insights/', SalaryInsightViewSet.as_view(), name='salary-insights'),
    path('alerts/', SalaryAlertViewSet.as_view(), name='salary-alerts'),
]