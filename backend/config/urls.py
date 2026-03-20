"""
Root URL configuration for USAM Career Compass backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.core.views import HealthCheckView

urlpatterns = [
    # Admin (path from ENV for security)
    path(settings.ADMIN_URL, admin.site.urls),

    # Health check
    path("health/", HealthCheckView.as_view(), name="health-check"),

    # API v1
    path("api/v1/", include([
        path("auth/", include("apps.accounts.urls")),
        path("users/", include("apps.users.urls")),
        path("jobs/", include("apps.jobs.urls")),
        path("analytics/", include("apps.analytics.urls")),
        path("admin-api/", include("apps.core.admin_urls")),
    ])),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # django-allauth (for social auth callbacks)
    path("accounts/", include("allauth.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
