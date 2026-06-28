"""Ashby API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class AshbyScraper(BaseATSScraper):
    """
    Scrapes jobs from Ashby public API.
    API: https://api.ashbyhq.com/posting-api/job-board/{company}
    """
    
    API_URL = "https://api.ashbyhq.com/posting-api/job-board/{company}"
    
    def get_platform_name(self) -> str:
        return 'ashby'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from Ashby."""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job in data.get('jobs', []):
                # Ashby jobUrl IS the direct apply link
                apply_url = job.get('jobUrl', '')
                
                if not apply_url:
                    continue
                
                normalized = {
                    'title': job.get('title', ''),
                    'apply_url': apply_url,
                    'description': job.get('description', ''),
                    'location': job.get('location', ''),
                    'id': job.get('id'),
                    'posted_at': job.get('publishedDate'),
                    'employment_type': job.get('employmentType'),
                    'remote_type': self._parse_remote(job.get('isRemote')),
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"Ashby scrape failed for {self.company_slug}: {e}")
            return []
    
    def _parse_remote(self, is_remote: bool) -> str:
        """Parse remote type."""
        if is_remote:
            return 'remote'
        return 'onsite'


def fetch_ashby_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Ashby jobs."""
    scraper = AshbyScraper(company_slug)
    return scraper.fetch_jobs()