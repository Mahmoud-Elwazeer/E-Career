"""Scraper app for job aggregation pipeline."""
from .orchestrator import orchestrator, scrape_all_sources_orchestrated
from .discovery.common_crawl import common_crawl_discovery, discover_companies_from_common_crawl

__all__ = [
    'orchestrator',
    'scrape_all_sources_orchestrated',
    'common_crawl_discovery',
    'discover_companies_from_common_crawl',
]

default_app_config = 'apps.scraper.apps.ScraperConfig'
