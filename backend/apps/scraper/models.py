"""Scraper models.

Note: We use existing models from apps.jobs and apps.core:
- Job: stores scraped jobs
- Company: stores company information
- Source: stores scraping sources
- PipelineHealth: tracks scraping pipeline health
- PlatformConfig: stores platform configuration

This file is kept for potential future scraper-specific models.
"""
from django.db import models

# Scraper-specific models can be added here in the future
# For now, all models are in apps.jobs and apps.core