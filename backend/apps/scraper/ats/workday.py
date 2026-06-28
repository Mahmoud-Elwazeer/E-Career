"""
Workday scraper - requires Playwright for JS rendering.
Workday is heavily JavaScript-based.
"""
from typing import List, Dict
from .base import BaseATSScraper


class WorkdayScraper(BaseATSScraper):
    """
    Workday requires headless browser.
    Implementation deferred to Phase 1B advanced section.
    For MVP, we skip Workday or use JobSpy wrapper.
    """
    
    def get_platform_name(self) -> str:
        return 'workday'
    
    def fetch_jobs(self) -> List[Dict]:
        """Workday scraping - placeholder."""
        # TODO: Implement with Playwright in advanced section
        return []


def fetch_workday_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Workday jobs."""
    scraper = WorkdayScraper(company_slug)
    return scraper.fetch_jobs()