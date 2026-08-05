"""
Monitoring & Observability Serializers
"""
from rest_framework import serializers
from .models import HealthCheck, PerformanceMetric, ErrorLog, UptimeRecord


class HealthCheckSerializer(serializers.ModelSerializer):
    """Serializer for HealthCheck model."""
    
    class Meta:
        model = HealthCheck
        fields = ['id', 'component', 'status', 'response_time_ms', 'error_message', 'checked_at']
        read_only_fields = ['id', 'checked_at']


class PerformanceMetricSerializer(serializers.ModelSerializer):
    """Serializer for PerformanceMetric model."""
    
    class Meta:
        model = PerformanceMetric
        fields = ['id', 'metric_type', 'value', 'tags', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']


class ErrorLogSerializer(serializers.ModelSerializer):
    """Serializer for ErrorLog model."""
    
    class Meta:
        model = ErrorLog
        fields = ['id', 'level', 'message', 'traceback', 'extra_data', 'sentry_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class UptimeRecordSerializer(serializers.ModelSerializer):
    """Serializer for UptimeRecord model."""
    
    class Meta:
        model = UptimeRecord
        fields = ['id', 'status', 'downtime_minutes', 'error_message', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']


class HealthSummarySerializer(serializers.Serializer):
    """Serializer for health summary response."""
    
    status = serializers.CharField()
    service = serializers.CharField()
    timestamp = serializers.DateTimeField()
    components = serializers.DictField()