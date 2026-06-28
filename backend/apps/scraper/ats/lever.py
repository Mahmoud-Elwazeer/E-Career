"""Lever API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class LeverScraper(BaseATSScraper):
    """
    Scrapes jobs from Lever public API.
    API: https://api.lever.co/v0/postings/{company}?mode=json
    """
    
    API_URL = "https://api.lever.co/v0/postings/{company}?mode=json"
    
    def get_platform_name(self) -> str:
        return 'lever'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from Lever."""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            jobs_data = response.json()
            jobs = []
            
            for job in jobs_data:
                # Lever hostedUrl IS the direct apply link
                apply_url = job.get('hostedUrl', '')
                
                if not apply_url:
                    continue
                
                normalized = {
                    'title': job.get('text', ''),
                    'apply_url': apply_url,
                    'description': job.get('description', '') or job.get('descriptionPlain', ''),
                    'location': job.get('categories', {}).get('location', ''),
                    'id': job.get('id'),
                    'posted_at': job.get('createdAt'),
                    'employment_type': self._parse_employment_type(job),
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Lever scrape failed for {self.company_slug}: {e}")
            return []
    
    def _parse_employment_type(self, job: Dict) -> str:
        """Parse employment type from Lever categories."""
        commitment = job.get('categories', {}).get('commitment', '').lower()
        
        if 'full' in commitment:
            return 'full_time'
        elif 'part' in commitment:
            return 'part_time'
        elif 'contract' in commitment:
            return 'contract'
        elif 'intern' in commitment:
            return 'internship'
        
        return None


def fetch_lever_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Lever jobs."""
    scraper = LeverScraper(company_slug)
    return scraper.fetch_jobs()