"""SmartRecruiters API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class SmartRecruitersScraper(BaseATSScraper):
    """
    Scrapes jobs from SmartRecruiters REST API.
    API: https://api.smartrecruiters.com/
    
    SmartRecruiters provides a public REST API for job board data.
    For company-specific scraping, we use the company slug to construct
    the API endpoint.
    """
    
    # SmartRecruiters API base URL
    API_BASE = "https://api.smartrecruiters.com"
    
    # Public job search endpoint
    SEARCH_URL = "https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
    
    def get_platform_name(self) -> str:
        return 'smartrecruiters'
    
    def fetch_jobs(self) -> List[Dict]:
        """
        Fetch all jobs from SmartRecruiters for a company.
        
        SmartRecruiters API uses pagination with 'offset' parameter.
        We'll fetch all pages until no more results are returned.
        """
        try:
            jobs = []
            offset = 0
            page_size = 50  # Max per request
            
            while True:
                url = self.SEARCH_URL.format(company_slug=self.company_slug)
                params = {
                    'offset': offset,
                    'limit': page_size,
                }
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                postings = data.get('postings', [])
                
                if not postings:
                    break
                
                for job in postings:
                    normalized = self._normalize_job(job)
                    if normalized.get('direct_apply_url'):
                        jobs.append(normalized)
                
                # Check if we've fetched all results
                total_count = data.get('totalNumber', 0)
                offset += len(postings)
                
                if offset >= total_count:
                    break
            
            return jobs
            
        except requests.RequestException as e:
            print(f"SmartRecruiters scrape failed for {self.company_slug}: {e}")
            return []
    
    def _normalize_job(self, job: Dict) -> Dict:
        """Normalize a SmartRecruiters job posting to our standard format."""
        # Get the apply URL - SmartRecruiters provides direct links
        apply_url = job.get('webUrl', '')
        
        # Get location info
        location_data = job.get('location', {})
        location = location_data.get('city', '') + ', ' + location_data.get('country', '')
        location = location.strip(', ')
        
        # Parse employment type
        employment_type = self._parse_employment_type(job)
        
        # Parse salary if available
        salary_info = job.get('salary', {})
        salary_min = salary_info.get('min')
        salary_max = salary_info.get('max')
        salary_currency = salary_info.get('currency', 'USD')
        
        # Get department
        department = job.get('department', {})
        department_name = department.get('name', '') if department else ''
        
        return {
            'title': job.get('name', ''),
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
            'posted_at': job.get('postingDate'),
            'departments': [department_name] if department_name else [],
            'raw_data': job,
        }
    
    def _parse_employment_type(self, job: Dict) -> str:
        """Parse employment type from SmartRecruiters job data."""
        employment_types = job.get('employmentTypes', [])
        
        if not employment_types:
            return None
        
        # Get the first employment type
        et = employment_types[0].lower()
        
        if 'full' in et:
            return 'full_time'
        elif 'part' in et:
            return 'part_time'
        elif 'contract' in et:
            return 'contract'
        elif 'intern' in et:
            return 'internship'
        elif 'temporary' in et or 'short' in et:
            return 'temporary'
        
        return None
    
    def _parse_experience_level(self, job: Dict) -> str:
        """Parse experience level from SmartRecruiters job data."""
        experience_levels = job.get('experienceLevels', [])
        
        if not experience_levels:
            return None
        
        level = experience_levels[0].lower()
        
        if 'entry' in level or 'junior' in level:
            return 'entry'
        elif 'mid' in level or 'intermediate' in level:
            return 'mid'
        elif 'senior' in level:
            return 'senior'
        elif 'lead' in level or 'principal' in level:
            return 'lead'
        
        return None
    
    def _parse_remote_type(self, job: Dict) -> str:
        """Parse remote type from SmartRecruiters job data."""
        work_locations = job.get('workLocations', [])
        
        if not work_locations:
            return None
        
        # Check for remote work indicators
        for location in work_locations:
            location_name = location.get('name', '').lower()
            if 'remote' in location_name or 'virtual' in location_name:
                return 'remote'
        
        # Default to onsite if no remote indicator
        return 'onsite'


def fetch_smartrecruiters_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch SmartRecruiters jobs."""
    scraper = SmartRecruitersScraper(company_slug)
    return scraper.fetch_jobs()