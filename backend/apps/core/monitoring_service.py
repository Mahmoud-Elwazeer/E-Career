"""
Monitoring & Observability Service

This module provides comprehensive monitoring, logging, and observability
for the E-Career platform. It includes:

1. Sentry integration for error tracking
2. Structured logging with structlog
3. Health check monitoring
4. Performance metrics collection
5. Uptime monitoring integration
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

import structlog
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

logger = structlog.get_logger(__name__)


class MonitoringService:
    """
    Centralized monitoring service for E-Career platform.
    
    Provides:
    - Error tracking with Sentry
    - Structured logging
    - Health check monitoring
    - Performance metrics
    - Uptime monitoring
    """
    
    def __init__(self):
        self.sentry_enabled = os.getenv('SENTRY_DSN', '').strip() != ''
        self.environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        self.release = os.getenv('RELEASE_VERSION', 'unknown')
        
        # Initialize Sentry if configured
        if self.sentry_enabled:
            self._init_sentry()
        
        # Initialize structured logging
        self._init_structured_logging()
    
    def _init_sentry(self):
        """Initialize Sentry error tracking."""
        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            environment=self.environment,
            release=self.release,
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            # Set traces sample rate for performance monitoring
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            # Set profiles sample rate for profiling
            profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
            # Send default PII (personally identifiable information)
            send_default_pii=False,
            # Include breadcrumbs
            attach_stacktrace=True,
            # Capture log messages
            max_breadcrumbs=50,
        )
        
        logger.info("sentry_initialized", sentry_dsn_set=True)
    
    def _init_structured_logging(self):
        """Initialize structured logging with structlog."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Configure log format based on environment
        if self.environment == 'production':
            # JSON format for production (easy to parse)
            formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer()
            )
        else:
            # Human-readable format for development
            formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=True)
            )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Add handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        
        logger.info("structured_logging_initialized", environment=self.environment)
    
    def capture_exception(self, exception: Exception, extra_data: Optional[Dict[str, Any]] = None):
        """
        Capture an exception and send to Sentry.
        
        Args:
            exception: The exception to capture
            extra_data: Optional dictionary of additional data to include
        """
        if self.sentry_enabled:
            with sentry_sdk.push_scope() as scope:
                if extra_data:
                    for key, value in extra_data.items():
                        scope.set_extra(key, value)
                sentry_sdk.capture_exception(exception)
        
        logger.error("exception_captured", exception=str(exception), extra_data=extra_data)
    
    def capture_message(self, message: str, level: str = "info", extra_data: Optional[Dict[str, Any]] = None):
        """
        Capture a message and send to Sentry.
        
        Args:
            message: The message to capture
            level: Log level (debug, info, warning, error, critical)
            extra_data: Optional dictionary of additional data to include
        """
        if self.sentry_enabled:
            sentry_sdk.capture_message(message, level=level)
        
        log_method = getattr(logger, level, logger.info)
        log_method("message_captured", message=message, extra_data=extra_data)
    
    def capture_job_scrape_event(self, job_id: str, platform: str, status: str, duration: float):
        """
        Capture a job scraping event.
        
        Args:
            job_id: The job ID
            platform: The ATS platform (e.g., 'greenhouse', 'lever')
            status: The scrape status ('success', 'failed', 'partial')
            duration: Duration in seconds
        """
        self.capture_message(
            f"Job scrape completed: {job_id} on {platform}",
            level="info",
            extra_data={
                "job_id": job_id,
                "platform": platform,
                "status": status,
                "duration_seconds": duration,
            }
        )
    
    def capture_user_event(self, user_id: str, event_type: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Capture a user event.
        
        Args:
            user_id: The user ID
            event_type: The event type (e.g., 'login', 'signup', 'job_view')
            metadata: Optional metadata about the event
        """
        self.capture_message(
            f"User event: {event_type} for user {user_id}",
            level="info",
            extra_data={
                "user_id": user_id,
                "event_type": event_type,
                "metadata": metadata,
            }
        )
    
    def capture_performance_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Capture a performance metric.
        
        Args:
            metric_name: The name of the metric
            value: The metric value
            tags: Optional tags for filtering
        """
        self.capture_message(
            f"Performance metric: {metric_name} = {value}",
            level="debug",
            extra_data={
                "metric_name": metric_name,
                "metric_value": value,
                "tags": tags or {},
            }
        )
    
    def capture_health_check(self, service: str, status: str, details: Optional[Dict[str, Any]] = None):
        """
        Capture a health check result.
        
        Args:
            service: The service name
            status: The health status ('healthy', 'degraded', 'unhealthy')
            details: Optional details about the health check
        """
        level = "info" if status == "healthy" else "warning" if status == "degraded" else "error"
        
        self.capture_message(
            f"Health check: {service} is {status}",
            level=level,
            extra_data={
                "service": service,
                "status": status,
                "details": details or {},
            }
        )
    
    def capture_celery_task(self, task_name: str, task_id: str, status: str, duration: float):
        """
        Capture a Celery task event.
        
        Args:
            task_name: The task name
            task_id: The task ID
            status: The task status ('success', 'failed', 'retrying')
            duration: Duration in seconds
        """
        self.capture_message(
            f"Celery task completed: {task_name} ({task_id})",
            level="info",
            extra_data={
                "task_name": task_name,
                "task_id": task_id,
                "status": status,
                "duration_seconds": duration,
            }
        )
    
    def capture_api_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """
        Capture an API request event.
        
        Args:
            endpoint: The API endpoint
            method: The HTTP method
            status_code: The HTTP status code
            duration: Duration in seconds
        """
        level = "info" if status_code < 400 else "warning" if status_code < 500 else "error"
        
        self.capture_message(
            f"API request: {method} {endpoint} = {status_code}",
            level=level,
            extra_data={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_seconds": duration,
            }
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the current health status of the monitoring service.
        
        Returns:
            Dictionary with health status information
        """
        return {
            "monitoring_service": {
                "status": "healthy",
                "sentry_enabled": self.sentry_enabled,
                "environment": self.environment,
                "release": self.release,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }


# Global monitoring service instance
monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    return monitoring_service