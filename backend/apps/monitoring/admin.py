"""
Monitoring & Observability Admin
"""
from django.contrib import admin
from .models import HealthCheck, PerformanceMetric, ErrorLog, UptimeRecord


@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    list_display = ['component', 'status', 'response_time_ms', 'checked_at']
    list_filter = ['component', 'status', 'checked_at']
    search_fields = ['component', 'error_message']
    readonly_fields = ['checked_at']
    date_hierarchy = 'checked_at'


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'recorded_at']
    list_filter = ['metric_type', 'recorded_at']
    search_fields = ['metric_type']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['level', 'message', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['message', 'traceback']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(UptimeRecord)
class UptimeRecordAdmin(admin.ModelAdmin):
    list_display = ['status', 'downtime_minutes', 'recorded_at']
    list_filter = ['status', 'recorded_at']
    search_fields = ['error_message']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'
