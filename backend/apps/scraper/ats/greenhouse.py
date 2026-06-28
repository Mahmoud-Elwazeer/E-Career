"""Greenhouse API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class GreenhouseScraper(BaseATSScraper):
    """
    Scrapes jobs from Greenhouse public API.
    API: https://api.greenhouse.io/v1/boards/{company}/jobs?content=true
    """
    
    API_URL = "https://api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    
    def get_platform_name(self) -> str:
        return 'greenhouse'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from Greenhouse."""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job in data.get('jobs', []):
                # Greenhouse absolute_url IS the direct apply link
                apply_url = job.get('absolute_url', '')
                
                if not apply_url:
                    continue
                
                normalized = {
                    'title': job.get('title', ''),
                    'apply_url': apply_url,
                    'description': job.get('content', ''),
                    'location': job.get('location', {}).get('name', ''),
                    'id': job.get('id'),
                    'posted_at': job.get('updated_at'),
                    'departments': [d['name'] for d in job.get('departments', [])],
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Greenhouse scrape failed for {self.company_slug}: {e}")
            return []


def fetch_greenhouse_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Greenhouse jobs."""
    scraper = GreenhouseScraper(company_slug)
    return scraper.fetch_jobs()