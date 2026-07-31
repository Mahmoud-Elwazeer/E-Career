from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
from django.db.utils import OperationalError
import redis
from celery import Celery


class HealthCheckView(APIView):
    """
    GET /health/
    Simple health check that pings the database.
    Returns 200 if healthy, 503 if database is unreachable.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            connection.ensure_connection()
            db_status = "ok"
        except OperationalError:
            db_status = "error"

        healthy = db_status == "ok"
        status_code = 200 if healthy else 503

        return Response(
            {
                "success": healthy,
                "data": {
                    "status": "healthy" if healthy else "unhealthy",
                    "database": db_status,
                },
                "message": "Service is running." if healthy else "Database connection failed.",
                "errors": None,
            },
            status=status_code,
        )


class DetailedHealthCheckView(APIView):
    """
    GET /health/detailed/
    Detailed health check that checks database, Redis, and Celery.
    Returns 200 if all services are healthy, 503 if any service is unhealthy.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        results = {
            "database": {"status": "unknown", "error": None},
            "redis": {"status": "unknown", "error": None},
            "celery": {"status": "unknown", "error": None},
        }
        all_healthy = True

        # Check database
        try:
            connection.ensure_connection()
            results["database"]["status"] = "healthy"
        except OperationalError as e:
            results["database"]["status"] = "unhealthy"
            results["database"]["error"] = str(e)
            all_healthy = False

        # Check Redis
        try:
            redis_host = "redis"
            redis_port = 6379
            r = redis.Redis(host=redis_host, port=redis_port, db=0, socket_timeout=2)
            r.ping()
            results["redis"]["status"] = "healthy"
        except Exception as e:
            results["redis"]["status"] = "unhealthy"
            results["redis"]["error"] = str(e)
            all_healthy = False

        # Check Celery (worker availability)
        try:
            from config.celery import app as celery_app
            inspector = celery_app.control.inspect()
            active_workers = inspector.active()
            if active_workers:
                results["celery"]["status"] = "healthy"
            else:
                results["celery"]["status"] = "unhealthy"
                results["celery"]["error"] = "No active Celery workers found"
                all_healthy = False
        except Exception as e:
            results["celery"]["status"] = "unhealthy"
            results["celery"]["error"] = str(e)
            all_healthy = False

        status_code = 200 if all_healthy else 503

        return Response(
            {
                "success": all_healthy,
                "data": {
                    "status": "healthy" if all_healthy else "unhealthy",
                    "services": results,
                },
                "message": "All services are running." if all_healthy else "Some services are unhealthy.",
                "errors": None,
            },
            status=status_code,
        )
