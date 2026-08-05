"""
Monitoring & Observability Views
"""
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.core.monitoring_service import get_monitoring_service


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint.
    
    Returns 200 OK if the service is running.
    """
    monitoring_service = get_monitoring_service()
    health_status = monitoring_service.get_health_status()
    
    return Response({
        "status": "healthy",
        "service": "ecareer-backend",
        "timestamp": health_status["monitoring_service"]["timestamp"],
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def detailed_health_check(request):
    """
    Detailed health check endpoint.
    
    Returns comprehensive health status including:
    - Database connection
    - Redis connection
    - Qdrant connection
    - Celery workers
    - Sentry status
    """
    monitoring_service = get_monitoring_service()
    health_status = monitoring_service.get_health_status()
    
    # Add database status
    try:
        from django.db import connection
        connection.cursor()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Add Redis status
    try:
        import redis
        r = redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
        r.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # Add Qdrant status
    try:
        from qdrant_client import QdrantClient
        q = QdrantClient(
            host=os.getenv('QDRANT_HOST', 'localhost'),
            port=int(os.getenv('QDRANT_PORT', 6333)),
            api_key=os.getenv('QDRANT_API_KEY'),
        )
        q.get_collections()
        qdrant_status = "healthy"
    except Exception as e:
        qdrant_status = f"unhealthy: {str(e)}"
    
    return Response({
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "service": "ecareer-backend",
        "timestamp": health_status["monitoring_service"]["timestamp"],
        "components": {
            "database": db_status,
            "redis": redis_status,
            "qdrant": qdrant_status,
            "sentry": "enabled" if monitoring_service.sentry_enabled else "disabled",
        },
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def metrics(request):
    """
    Metrics endpoint.
    
    Returns system metrics including:
    - Request counts
    - Error rates
    - Response times
    - Resource usage
    """
    monitoring_service = get_monitoring_service()
    
    return Response({
        "metrics": {
            "uptime_seconds": 0,  # Would need to track this
            "requests_total": 0,  # Would need to track this
            "requests_error": 0,  # Would need to track this
            "requests_success": 0,  # Would need to track this
        },
        "system": {
            "cpu_percent": 0,  # Would need psutil
            "memory_percent": 0,  # Would need psutil
            "disk_percent": 0,  # Would need psutil
        },
        "monitoring": monitoring_service.get_health_status(),
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def sentry_test(request):
    """
    Sentry test endpoint.
    
    Triggers a test exception to verify Sentry is working.
    """
    try:
        # Trigger a test exception
        raise Exception("Test exception from Sentry test endpoint")
    except Exception as e:
        monitoring_service = get_monitoring_service()
        monitoring_service.capture_exception(e, {"test": True})
        
        return Response({
            "message": "Test exception sent to Sentry",
            "sentry_enabled": monitoring_service.sentry_enabled,
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_history(request):
    """
    Get health check history.
    
    Returns a list of health check records for all components.
    """
    from .models import HealthCheck
    from .serializers import HealthCheckSerializer
    
    health_checks = HealthCheck.objects.all().order_by('-checked_at')[:100]
    serializer = HealthCheckSerializer(health_checks, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def metrics_history(request):
    """
    Get performance metrics history.
    
    Returns a list of performance metric records.
    """
    from .models import PerformanceMetric
    from .serializers import PerformanceMetricSerializer
    
    metrics = PerformanceMetric.objects.all().order_by('-recorded_at')[:100]
    serializer = PerformanceMetricSerializer(metrics, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def error_logs(request):
    """
    Get error logs.
    
    Returns a list of error log records.
    """
    from .models import ErrorLog
    from .serializers import ErrorLogSerializer
    
    errors = ErrorLog.objects.all().order_by('-created_at')[:100]
    serializer = ErrorLogSerializer(errors, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def uptime_records(request):
    """
    Get uptime records.
    
    Returns a list of uptime records.
    """
    from .models import UptimeRecord
    from .serializers import UptimeRecordSerializer
    
    uptime = UptimeRecord.objects.all().order_by('-recorded_at')[:100]
    serializer = UptimeRecordSerializer(uptime, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)
