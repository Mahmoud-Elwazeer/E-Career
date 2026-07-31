"""Teamtailor JSON API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class TeamtailorScraper(BaseATSScraper):
    """
    Scrapes jobs from Teamtailor JSON API.
    API: https://api.teamtailor.com/
    
    Teamtailor provides a REST API for job listings.
    The API endpoint is: https://api.teamtailor.com/v1/jobs?filter[company]={company_slug}
    """
    
    # Teamtailor API base URL
    API_BASE = "https://api.teamtailor.com"
    
    # Jobs endpoint
    JOBS_URL = "https://api.teamtailor.com/v1/jobs"
    
    def get_platform_name(self) -> str:
        return 'teamtailor'
    
    def fetch_jobs(self) -> List[Dict]:
        """
        Fetch all jobs from Teamtailor for a company.
        
        Teamtailor API uses pagination with 'page[number]' and 'page[size]' parameters.
        """
        try:
            jobs = []
            page = 1
            page_size = 50
            
            while True:
                params = {
                    'page[number]': page,
                    'page[size]': page_size,
                }
                
                response = requests.get(self.JOBS_URL, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                job_list = data.get('data', [])
                
                if not job_list:
                    break
                
                for job in job_list:
                    normalized = self._normalize_job(job)
                    if normalized.get('direct_apply_url'):
                        jobs.append(normalized)
                
                # Check if we've fetched all pages
                meta = data.get('meta', {})
                total_pages = meta.get('total-pages', 1)
                
                if page >= total_pages:
                    break
                
                page += 1
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Teamtailor scrape failed for {self.company_slug}: {e}")
            return []
    
    def _normalize_job(self, job: Dict) -> Dict:
        """Normalize a Teamtailor job posting to our standard format."""
        # Teamtailor provides direct apply URL
        attributes = job.get('attributes', {})
        apply_url = attributes.get('application_url', '')
        
        # Get location
        location = attributes.get('location', '')
        
        # Parse employment type
        employment_type = self._parse_employment_type(attributes)
        
        # Parse salary if available
        salary_info = attributes.get('salary', {})
        salary_min = salary_info.get('min') if isinstance(salary_info, dict) else None
        salary_max = salary_info.get('max') if isinstance(salary_info, dict) else None
        salary_currency = salary_info.get('currency', 'USD') if isinstance(salary_info, dict) else 'USD'
        
        # Get department
        department = attributes.get('department', {})
        department_name = department.get('name', '') if isinstance(department, dict) else ''
        
        return {
            'title': attributes.get('title', ''),
            'apply_url': apply_url,
            'direct_apply_url': apply_url,
            'description': attributes.get('description', ''),
            'location': location,
            'employment_type': employment_type,
            'experience_level': self._parse_experience_level(attributes),
            'remote_type': self._parse_remote_type(attributes),
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_currency': salary_currency,
            'id': job.get('id'),
            'ats_job_id': job.get('id'),
            'posted_at': attributes.get('created_at'),
            'departments': [department_name] if department_name else [],
            'raw_data': job,
        }
    
    def _parse_employment_type(self, attributes: Dict) -> str:
        """Parse employment type from Teamtailor job data."""
        employment_types = attributes.get('employment_types', [])
        
        if not employment_types:
            return None
        
        # Get the first employment type
        et = employment_types[0].lower() if isinstance(employment_types, list) else employment_types.lower()
        
        if 'full' in et:
            return 'full_time'
        elif 'part' in et:
            return 'part_time'
        elif 'contract' in et:
            return 'contract'
        elif 'intern' in et:
            return 'internship'
        elif 'temporary' in et:
            return 'temporary'
        
        return None
    
    def _parse_experience_level(self, attributes: Dict) -> str:
        """Parse experience level from Teamtailor job data."""
        experience_level = attributes.get('experience_level', '').lower()
        
        if 'entry' in experience_level or 'junior' in experience_level:
            return 'entry'
        elif 'mid' in experience_level or 'intermediate' in experience_level:
            return 'mid'
        elif 'senior' in experience_level:
            return 'senior'
        elif 'lead' in experience_level or 'principal' in experience_level:
            return 'lead'
        
        return None
    
    def _parse_remote_type(self, attributes: Dict) -> str:
        """Parse remote type from Teamtailor job data."""
        work_location = attributes.get('work_location', '').lower()
        
        if 'remote' in work_location or 'virtual' in work_location:
            return 'remote'
        
        # Check for remote work indicators in location
        location = attributes.get('location', '').lower()
        
        if 'remote' in location or 'virtual' in location:
            return 'remote'
        
        return 'onsite'


def fetch_teamtailor_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Teamtailor jobs."""
    scraper = TeamtailorScraper(company_slug)
    return scraper.fetch_jobs()