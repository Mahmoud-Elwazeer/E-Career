"""Scraper app configuration."""
from django.apps import AppConfig


class ScraperConfig(AppConfig):
    """Configuration for the scraper app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scraper'
    verbose_name = 'Job Scraper'
    
    def ready(self):
        """Import tasks when app is ready."""
        try:
            import apps.scraper.tasks  # noqa
        except ImportError:
            pass