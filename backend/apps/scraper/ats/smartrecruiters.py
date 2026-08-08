"""SmartRecruiters API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class SmartRecruitersScraper(BaseATSScraper):
    """
    Scrapes jobs from SmartRecruiters ATS API.
    
    Base URL pattern: https://careers.smartrecruiters.com/{company_name}
    API endpoint: https://api.smartrecruiters.com/v1/companies/{id}/postings
    
    SmartRecruiters uses company IDs (not slugs) for API access.
    """
    
    API_URL = "https://api.smartrecruiters.com/v1/companies/{company_id}/postings"
    HEADERS = {
        'Accept': 'application/json',
        'User-Agent': 'USAM-Career-Compass/1.0',
    }
    
    def get_platform_name(self) -> str:
        return 'smartrecruiters'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from SmartRecruiters API."""
        try:
            # SmartRecruiters uses company_id (not company_slug)
            # Try to use company_slug as company_id first
            url = self.API_URL.format(company_id=self.company_slug)
            
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job in data.get('content', []):
                # Extract job details
                job_id = job.get('id', '')
                if not job_id:
                    continue
                
                # Build direct apply URL
                # SmartRecruiters uses: https://careers.smartrecruiters.com/{company_name}/{job_id}
                apply_url = f"https://careers.smartrecruiters.com/{self.company_slug}/{job_id}"
                
                # Extract location
                location_data = job.get('location', {})
                location = location_data.get('city', '') + ', ' + location_data.get('country', '')
                location = location.strip(', ')
                
                # Extract department
                department = ''
                if job.get('category'):
                    department = job.get('category', {}).get('name', '')
                
                # Extract experience level
                experience_level = ''
                if job.get('jobType'):
                    experience_level = job.get('jobType', {}).get('name', '').lower()
                
                normalized = {
                    'title': job.get('name', ''),
                    'apply_url': apply_url,
                    'description': job.get('descriptionText', ''),
                    'location': location,
                    'id': job_id,
                    'posted_at': job.get('creationDate', ''),
                    'departments': [department] if department else [],
                    'employment_type': job.get('jobType', {}).get('name', ''),
                    'experience_level': experience_level,
                    'remote_type': self._get_remote_type(job),
                    'salary_min': None,
                    'salary_max': None,
                    'salary_currency': 'USD',
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"SmartRecruiters scrape failed for {self.company_slug}: {e}")
            return []
    
    def _get_remote_type(self, job: Dict) -> str:
        """Determine remote type from job data."""
        job_type = job.get('jobType', {}).get('name', '').lower()
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


def fetch_smartrecruiters_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch SmartRecruiters jobs."""
    scraper = SmartRecruitersScraper(company_slug)
    return scraper.fetch_jobs()