import re
from django.utils.text import slugify as django_slugify


def make_unique_slug(model_class, base_text, field_name="slug", instance=None):
    """
    Generate a unique slug for a model instance.
    Appends a counter suffix if the slug already exists.
    """
    slug = django_slugify(base_text)
    qs = model_class.objects.filter(**{field_name: slug})
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)

    if not qs.exists():
        return slug

    counter = 1
    while True:
        candidate = f"{slug}-{counter}"
        if not model_class.objects.filter(**{field_name: candidate}).exists():
            return candidate
        counter += 1


def get_client_ip(request):
    """Extract the real client IP from the request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def success_response(data=None, message="", status_code=200):
    """Build a standard success response dict."""
    return {
        "success": True,
        "data": data,
        "message": message,
        "errors": None,
    }


def error_response(message="An error occurred.", errors=None, status_code=400):
    """Build a standard error response dict."""
    return {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors,
    }
