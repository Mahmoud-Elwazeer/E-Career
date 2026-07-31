"""
Skills App Configuration

This module defines the Django app configuration for the skills app.
"""

from django.apps import AppConfig


class SkillsConfig(AppConfig):
    """Django app configuration for the skills app."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.skills"
    verbose_name = "Skills & Occupations"