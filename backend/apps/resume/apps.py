"""
Resume Builder App Configuration

This module defines the Django app configuration for the resume builder.
"""

from django.apps import AppConfig


class ResumeConfig(AppConfig):
    """Configuration for the resume app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.resume'
    verbose_name = 'Resume Builder'