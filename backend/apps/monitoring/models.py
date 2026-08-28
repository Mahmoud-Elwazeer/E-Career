"""
Monitoring & Observability Models

This module defines models for tracking system health, performance metrics,
and monitoring data for the E-Career platform.
"""

from django.db import models
from django.utils import timezone


class HealthCheck(models.Model):
    """
    Health check record for system components.
    
    Tracks the health status of various system components
    including database, Redis, and Celery workers.
    """
    
    COMPONENT_CHOICES = [
        ('database', 'Database'),
        ('redis', 'Redis'),
        ('celery', 'Celery'),
        ('sentry', 'Sentry'),
        ('api', 'API'),
    ]
    
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('unhealthy', 'Unhealthy'),
    ]
    
    component = models.CharField(
        max_length=50,
        choices=COMPONENT_CHOICES,
        help_text="The system component being checked"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="The health status"
    )
    
    response_time_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="Response time in milliseconds"
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if unhealthy"
    )
    
    checked_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the health check was performed"
    )
    
    class Meta:
        verbose_name = "Health Check"
        verbose_name_plural = "Health Checks"
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['component', 'status']),
            models.Index(fields=['-checked_at']),
        ]
    
    def __str__(self):
        return f"{self.component}: {self.status}"


class PerformanceMetric(models.Model):
    """
    Performance metric record.
    
    Tracks system performance metrics over time for
    monitoring and analysis.
    """
    
    METRIC_TYPE_CHOICES = [
        ('cpu_percent', 'CPU Usage (%)'),
        ('memory_percent', 'Memory Usage (%)'),
        ('disk_percent', 'Disk Usage (%)'),
        ('request_count', 'Request Count'),
        ('error_count', 'Error Count'),
        ('response_time_avg', 'Average Response Time (ms)'),
        ('response_time_p95', '95th Percentile Response Time (ms)'),
        ('response_time_p99', '99th Percentile Response Time (ms)'),
        ('active_users', 'Active Users'),
        ('jobs_scraped', 'Jobs Scraped'),
        ('api_calls', 'API Calls'),
    ]
    
    metric_type = models.CharField(
        max_length=50,
        choices=METRIC_TYPE_CHOICES,
        help_text="The type of metric"
    )
    
    value = models.FloatField(
        help_text="The metric value"
    )
    
    tags = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional tags for filtering (e.g., {'endpoint': '/api/v1/jobs'})"
    )
    
    recorded_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the metric was recorded"
    )
    
    class Meta:
        verbose_name = "Performance Metric"
        verbose_name_plural = "Performance Metrics"
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', 'recorded_at']),
            models.Index(fields=['recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.metric_type}: {self.value}"


class ErrorLog(models.Model):
    """
    Error log record.
    
    Stores error information for monitoring and debugging.
    """
    
    LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        help_text="The log level"
    )
    
    message = models.TextField(
        help_text="The error message"
    )
    
    traceback = models.TextField(
        null=True,
        blank=True,
        help_text="Full traceback if available"
    )
    
    extra_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional data (user_id, request_id, etc.)"
    )
    
    sentry_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Sentry event ID if sent"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the error was logged"
    )
    
    class Meta:
        verbose_name = "Error Log"
        verbose_name_plural = "Error Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.level}: {self.message[:100]}"


class UptimeRecord(models.Model):
    """
    Uptime record for monitoring service availability.
    
    Tracks whether the service was up or down at specific times.
    """
    
    STATUS_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('degraded', 'Degraded'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="The service status"
    )
    
    downtime_minutes = models.FloatField(
        null=True,
        blank=True,
        help_text="Downtime duration in minutes if down"
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if down"
    )
    
    recorded_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the uptime record was created"
    )
    
    class Meta:
        verbose_name = "Uptime Record"
        verbose_name_plural = "Uptime Records"
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['status', 'recorded_at']),
            models.Index(fields=['-recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.status} at {self.recorded_at}"