"""
Root URL configuration for USAM Career Compass backend.
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.core.views import HealthCheckView, DetailedHealthCheckView
from apps.jobs.sitemaps import sitemaps as job_sitemaps

# Import custom admin views
from apps.scraper.admin_views import scraper_dashboard, health_monitor

urlpatterns = [
    # Admin (path from ENV for security)
    path(settings.ADMIN_URL, admin.site.urls),
    
    # Custom admin dashboard views (Phase 3C)
    path("admin/scraper-dashboard/", scraper_dashboard, name="admin-scraper-dashboard"),
    path("admin/health-monitor/", health_monitor, name="admin-health-monitor"),

    # Health check
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("health/detailed/", DetailedHealthCheckView.as_view(), name="health-check-detailed"),

    # API v1
    path("api/v1/", include([
        path("auth/", include("apps.accounts.urls")),
        path("users/", include("apps.users.urls")),
        path("jobs/", include("apps.jobs.urls")),
        path("profile/", include("apps.profiles.urls")),
        path("analytics/", include("apps.analytics.urls")),
        path("admin-api/", include("apps.core.admin_urls")),
        # Rashid AI Assistant (Phase 2B)
        path("rashid/", include("apps.rashid.urls")),
        # Employer Portal (Phase 3A)
        path("employer/", include("apps.employers.urls")),
        # Search (Phase 1)
        path("search/", include("apps.search.urls")),
        # Vector Search (Phase 1 Week 6)
        path("vectors/", include("apps.vectors.urls")),
        # Career Intelligence (Phase 2)
        path("career/", include("apps.career.urls")),
        # Salary Intelligence (Phase 3)
        path("salary/", include("apps.salary.urls")),
        # Assessment Platform (Phase 3)
        path("assessment/", include("apps.assessment.urls")),
        # Core (Rule Engine, Feature Flags, GitHub) - Week 13
        path("core/", include("apps.core.urls")),
    ])),

    # Email tracking (Phase 2D)
    path("emails/", include("apps.emails.urls")),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # django-allauth (for social auth callbacks)
    path("accounts/", include("allauth.urls")),

    # Sitemap for SEO
    path('sitemap.xml', sitemap, {'sitemaps': job_sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)