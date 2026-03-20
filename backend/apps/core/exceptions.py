import logging
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError, AuthenticationFailed, NotAuthenticated,
    PermissionDenied, NotFound, MethodNotAllowed, Throttled,
)
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler that always returns a consistent JSON envelope:
    {
        "success": false,
        "data": null,
        "message": "Human-readable message",
        "errors": { ... }
    }
    """
    # Convert Django exceptions to DRF equivalents
    if isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied()

    # Call DRF's default handler first
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled server error — log it and return 500
        logger.exception("Unhandled server error", exc_info=exc)
        return Response(
            {
                "success": False,
                "data": None,
                "message": "An unexpected error occurred. Please try again.",
                "errors": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Build a clean error response
    message = _get_message(exc, response)
    errors = _get_errors(response.data)

    response.data = {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors,
    }

    return response


def _get_message(exc, response):
    """Extract a single human-readable message from the exception."""
    if isinstance(exc, NotAuthenticated):
        return "Authentication credentials were not provided."
    if isinstance(exc, AuthenticationFailed):
        return "Invalid or expired credentials."
    if isinstance(exc, PermissionDenied):
        return "You do not have permission to perform this action."
    if isinstance(exc, NotFound):
        return "The requested resource was not found."
    if isinstance(exc, MethodNotAllowed):
        return f"Method '{exc.args[0] if exc.args else ''}' not allowed."
    if isinstance(exc, Throttled):
        wait = exc.wait
        if wait:
            return f"Request throttled. Expected available in {int(wait)} seconds."
        return "Request throttled. Too many requests."
    if isinstance(exc, ValidationError):
        data = response.data
        if isinstance(data, list) and data:
            return str(data[0])
        if isinstance(data, dict):
            for key in ("detail", "non_field_errors"):
                if key in data:
                    val = data[key]
                    return str(val[0]) if isinstance(val, list) else str(val)
            # Return first field error
            first_key = next(iter(data))
            val = data[first_key]
            return str(val[0]) if isinstance(val, list) else str(val)
        return "Validation failed."
    # Generic fallback
    if hasattr(response, "data") and isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail:
            return str(detail)
    return "An error occurred."


def _get_errors(data):
    """Return errors dict or None."""
    if isinstance(data, dict) and "detail" in data:
        return None  # don't double-expose simple detail errors
    if isinstance(data, (dict, list)):
        return data
    return None
