from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
from django.db.utils import OperationalError


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
