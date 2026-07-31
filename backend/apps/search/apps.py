"""
Search App Configuration

This module defines the Django app configuration for the search app.
"""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    """Django app configuration for the search app."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search"
    verbose_name = "Search"
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.search.signals  # noqa: F401