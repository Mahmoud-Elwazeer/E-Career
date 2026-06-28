"""Base class for all ATS scrapers."""
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class BaseATSScraper(ABC):
    """
    Base class for all ATS API scrapers.
    Each ATS scraper must implement fetch_jobs().
    """
    
    def __init__(self, company_slug: str):
        self.company_slug = company_slug
    
    @abstractmethod
    def fetch_jobs(self) -> List[Dict]:
        """
        Fetch jobs from ATS API.
        Must return list of normalized job dicts.
        """
        pass
    
    def normalize_job(self, raw_job: Dict) -> Dict:
        """
        Normalize raw ATS data to our standard format.
        Override in subclass if needed.
        """
        return {
            'title': raw_job.get('title', ''),
            'company_slug': self.company_slug,
            'direct_apply_url': raw_job.get('apply_url', ''),
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
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return ATS platform name (e.g., 'greenhouse')"""
        pass