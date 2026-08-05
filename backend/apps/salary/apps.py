"""
Salary Intelligence App Configuration
"""

from django.apps import AppConfig


class SalaryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.salary'
    verbose_name = 'Salary Intelligence'