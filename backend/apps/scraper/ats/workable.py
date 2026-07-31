"""Workable API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class WorkableScraper(BaseATSScraper):
    """
    Scrapes jobs from Workable public widget API.
    API: https://www.workable.com/
    
    Workable provides a public API for job listings through their widget system.
    The API endpoint is: https://www.workable.com/spi/v1/companies/{company}/jobs
    """
    
    # Workable API endpoint for company jobs
    API_URL = "https://www.workable.com/spi/v1/companies/{company}/jobs"
    
    def get_platform_name(self) -> str:
        return 'workable'
    
    def fetch_jobs(self) -> List[Dict]:
        """
        Fetch all jobs from Workable for a company.
        
        Workable API returns paginated results with 'next' link.
        """
        try:
            jobs = []
            url = self.API_URL.format(company=self.company_slug)
            
            while url:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                job_list = data.get('jobs', [])
                
                for job in job_list:
                    normalized = self._normalize_job(job)
                    if normalized.get('direct_apply_url'):
                        jobs.append(normalized)
                
                # Get next page URL if available
                url = data.get('next')
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Workable scrape failed for {self.company_slug}: {e}")
            return []
    
    def _normalize_job(self, job: Dict) -> Dict:
        """Normalize a Workable job posting to our standard format."""
        # Workable provides direct apply URL
        apply_url = job.get('url', '')
        
        # Get location
        location_data = job.get('location', {})
        location = location_data.get('city', '') + ', ' + location_data.get('country', '')
        location = location.strip(', ')
        
        # Parse employment type
        employment_type = self._parse_employment_type(job)
        
        # Parse salary if available
        salary_info = job.get('salary', {})
        salary_min = salary_info.get('min') if isinstance(salary_info, dict) else None
        salary_max = salary_info.get('max') if isinstance(salary_info, dict) else None
        salary_currency = salary_info.get('currency', 'USD') if isinstance(salary_info, dict) else 'USD'
        
        # Get department
        department = job.get('department', {})
        department_name = department.get('name', '') if department else ''
        
        return {
            'title': job.get('title', ''),
            'apply_url': apply_url,
            'direct_apply_url': apply_url,
            'description': job.get('description', ''),
            'location': location,
            'employment_type': employment_type,
            'experience_level': self._parse_experience_level(job),
            'remote_type': self._parse_remote_type(job),
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_currency': salary_currency,
            'id': job.get('id'),
            'ats_job_id': job.get('id'),
            'posted_at': job.get('created_at'),
            'departments': [department_name] if department_name else [],
            'raw_data': job,
        }
    
    def _parse_employment_type(self, job: Dict) -> str:
        """Parse employment type from Workable job data."""
        employment_type = job.get('type', '').lower()
        
        if 'full' in employment_type:
            return 'full_time'
        elif 'part' in employment_type:
            return 'part_time'
        elif 'contract' in employment_type:
            return 'contract'
        elif 'intern' in employment_type:
            return 'internship'
        elif 'temporary' in employment_type:
            return 'temporary'
        
        return None
    
    def _parse_experience_level(self, job: Dict) -> str:
        """Parse experience level from Workable job data."""
        experience_level = job.get('experience_level', '').lower()
        
        if 'entry' in experience_level or 'junior' in experience_level:
            return 'entry'
        elif 'mid' in experience_level or 'intermediate' in experience_level:
            return 'mid'
        elif 'senior' in experience_level:
            return 'senior'
        elif 'lead' in experience_level or 'principal' in experience_level:
            return 'lead'
        
        return None
    
    def _parse_remote_type(self, job: Dict) -> str:
        """Parse remote type from Workable job data."""
        work_location = job.get('work_location', '').lower()
        
        if 'remote' in work_location or 'virtual' in work_location:
            return 'remote'
        
        # Check location object for remote indicators
        location_data = job.get('location', {})
        location_name = location_data.get('name', '').lower()
        
        if 'remote' in location_name or 'virtual' in location_name:
            return 'remote'
        
        return 'onsite'


def fetch_workable_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Workable jobs."""
    scraper = WorkableScraper(company_slug)
    return scraper.fetch_jobs()