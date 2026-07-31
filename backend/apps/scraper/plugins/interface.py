"""
Scraper Plugin Interface

Defines the interface for scraper plugins and the plugin registry.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from django.utils import timezone


class ScraperPlugin(ABC):
    """
    Interface for all scraper plugins.
    
    Plugins must implement:
    - get_platform_name(): Return the ATS platform name
    - fetch_jobs(): Fetch jobs from the ATS
    - get_schedule_cron(): Return the default scraping schedule
    - requires_playwright(): Return True if headless browser is needed
    """
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the ATS platform name (e.g., 'greenhouse')."""
        pass
    
    @abstractmethod
    def fetch_jobs(self, company_slug: str) -> List[Dict]:
        """
        Fetch jobs from the ATS for a company.
        
        Args:
            company_slug: Company slug/identifier
            
        Returns:
            List of job dictionaries
        """
        pass
    
    def get_schedule_cron(self) -> str:
        """
        Return the default scraping schedule (cron expression).
        
        Returns:
            Cron expression string (default: every 6 hours)
        """
        return '0 */6 * * *'
    
    def requires_playwright(self) -> bool:
        """
        Return True if this scraper requires headless browser (Playwright).
        
        Returns:
            False by default (override in subclasses)
        """
        return False
    
    def validate_company(self, company_slug: str) -> bool:
        """
        Validate that a company has an active career page.
        
        Args:
            company_slug: Company slug/identifier
            
        Returns:
            True if valid, False otherwise
        """
        try:
            jobs = self.fetch_jobs(company_slug)
            return len(jobs) > 0
        except Exception:
            return False
    
    def normalize_job(self, raw_job: Dict) -> Dict:
        """
        Normalize a raw job to our standard format.
        
        Args:
            raw_job: Raw job data from ATS
            
        Returns:
            Normalized job dictionary
        """
        return {
            'title': raw_job.get('title', ''),
            'company_slug': raw_job.get('company_slug', ''),
            'direct_apply_url': raw_job.get('direct_apply_url', ''),
            'description': raw_job.get('description', ''),
            'location': raw_job.get('location', ''),
            'employment_type': raw_job.get('employment_type'),
            'experience_level': raw_job.get('experience_level'),
            'remote_type': raw_job.get('remote_type'),
            'salary_min': raw_job.get('salary_min'),
            'salary_max': raw_job.get('salary_max'),
            'salary_currency': raw_job.get('salary_currency', 'USD'),
            'ats_platform': self.get_platform_name(),
            'ats_job_id': str(raw_job.get('id', '')),
            'raw_data': raw_job,
            'scraped_at': raw_job.get('posted_at'),
        }


class BaseScraperPlugin(ScraperPlugin):
    """
    Base class for scraper plugins with common functionality.
    """
    
    def __init__(self, company_slug: str = ''):
        self.company_slug = company_slug
        self.last_error: Optional[str] = None
        self.last_run_at: Optional[timezone.datetime] = None
        self.run_count = 0
        self.failure_count = 0
    
    def get_platform_name(self) -> str:
        """Return the platform name from the class name."""
        name = self.__class__.__name__
        if name.endswith('Scraper'):
            return name[:-7].lower()
        return name.lower()
    
    def fetch_jobs(self, company_slug: str) -> List[Dict]:
        """
        Fetch jobs with error handling and tracking.
        
        Args:
            company_slug: Company slug/identifier
            
        Returns:
            List of job dictionaries
        """
        self.last_run_at = timezone.now()
        self.run_count += 1
        
        try:
            jobs = self._do_fetch_jobs(company_slug)
            self.failure_count = 0
            return jobs
        except Exception as e:
            self.last_error = str(e)
            self.failure_count += 1
            return []
    
    def _do_fetch_jobs(self, company_slug: str) -> List[Dict]:
        """
        Actual job fetching implementation (override in subclasses).
        
        Args:
            company_slug: Company slug/identifier
            
        Returns:
            List of job dictionaries
        """
        return []
    
    def should_disable(self, max_failures: int = 5) -> bool:
        """
        Check if this scraper should be disabled due to failures.
        
        Args:
            max_failures: Maximum allowed failures before disabling
            
        Returns:
            True if should be disabled
        """
        return self.failure_count >= max_failures


def create_scraper_from_platform(platform: str, company_slug: str) -> Optional[ScraperPlugin]:
    """
    Factory function to create a scraper plugin from platform name.
    
    Args:
        platform: Platform name (e.g., 'greenhouse')
        company_slug: Company slug/identifier
        
    Returns:
        ScraperPlugin instance or None if platform not found
    """
    from .registry import plugin_registry
    
    return plugin_registry.get_scraper(platform, company_slug)