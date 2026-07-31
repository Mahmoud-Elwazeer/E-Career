"""Scraper plugins package."""
from .interface import ScraperPlugin, BaseScraperPlugin
from .registry import plugin_registry

__all__ = [
    'ScraperPlugin',
    'BaseScraperPlugin',
    'plugin_registry',
]