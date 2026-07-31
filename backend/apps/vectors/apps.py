"""
Vectors App Configuration
"""

from django.apps import AppConfig


class VectorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.vectors"
    verbose_name = "Vector Embeddings"

    def ready(self):
        """Import signals when app is ready."""
        import apps.vectors.signals  # noqa
