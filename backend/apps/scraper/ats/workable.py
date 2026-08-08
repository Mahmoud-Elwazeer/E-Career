"""Workable API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class WorkableScraper(BaseATSScraper):
    """
    Scrapes jobs from Workable ATS API.
    
    Base URL pattern: https://apply.workable.com/j/{job_id}
    API endpoint: https://{company}.workable.com/spi/v3/jobs
    
    Workable uses company subdomain for API access.
    """
    
    API_URL = "https://{company_subdomain}.workable.com/spi/v3/jobs"
    JOB_URL_PATTERN = "https://apply.workable.com/j/{job_id}"
    HEADERS = {
        'Accept': 'application/json',
        'User-Agent': 'USAM-Career-Compass/1.0',
    }
    
    def get_platform_name(self) -> str:
        return 'workable'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from Workable API."""
        try:
            # Workable uses company subdomain (not company_slug)
            # Try to use company_slug as subdomain first
            url = self.API_URL.format(company_subdomain=self.company_slug)
            
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job in data.get('jobs', []):
                job_id = job.get('shortcode', '')
                if not job_id:
                    continue
                
                # Build direct apply URL
                apply_url = self.JOB_URL_PATTERN.format(job_id=job_id)
                
                # Extract location
                location_data = job.get('location', {})
                location = location_data.get('city', '') + ', ' + location_data.get('country', '')
                location = location.strip(', ')
                
                # Extract department
                department = ''
                if job.get('department'):
                    department = job.get('department', {}).get('name', '')
                
                # Extract experience level
                experience_level = ''
                if job.get('type'):
                    experience_level = job.get('type', {}).get('name', '').lower()
                
                # Extract salary
                salary_min = None
                salary_max = None
                if job.get('salary'):
                    salary_range = job.get('salary', {})
                    salary_min = salary_range.get('min', None)
                    salary_max = salary_range.get('max', None)
                
                normalized = {
                    'title': job.get('title', ''),
                    'apply_url': apply_url,
                    'description': job.get('description', ''),
                    'location': location,
                    'id': job_id,
                    'posted_at': job.get('created_at', ''),
                    'departments': [department] if department else [],
                    'employment_type': job.get('type', {}).get('name', ''),
                    'experience_level': experience_level,
                    'remote_type': self._get_remote_type(job),
                    'salary_min': salary_min,
                    'salary_max': salary_max,
                    'salary_currency': job.get('salary', {}).get('currency', 'USD'),
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Workable scrape failed for {self.company_slug}: {e}")
            return []
    
    def _get_remote_type(self, job: Dict) -> str:
        """Determine remote type from job data."""
        job_type = job.get('type', {}).get('name', '').lower()
        location = job.get('location', {})
        
        # Check for remote keywords in job type
        if 'remote' in job_type or 'virtual' in job_type:
            return 'remote'
        
        # Check for hybrid keywords
        if 'hybrid' in job_type or 'flexible' in job_type:
            return 'hybrid'
        
        # Check location for remote indicators
        city = location.get('city', '').lower()
        if 'remote' in city or 'virtual' in city:
            return 'remote'
        
        return 'onsite'


def fetch_workable_jobs(company_subdomain: str) -> List[Dict]:
    """Convenience function to fetch Workable jobs."""
    scraper = WorkableScraper(company_subdomain)
    return scraper.fetch_jobs()