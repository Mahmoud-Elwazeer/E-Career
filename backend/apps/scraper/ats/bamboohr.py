"""BambooHR scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class BambooHRScraper(BaseATSScraper):
    """
    Scrapes jobs from BambooHR public board.
    URL: https://{company}.bamboohr.com/jobs/list/
    """
    
    API_URL = "https://{company}.bamboohr.com/jobs/list/"
    
    def get_platform_name(self) -> str:
        return 'bamboohr'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from BambooHR."""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # BambooHR returns JSON with job list
            data = response.json()
            jobs = []
            
            for job in data.get('result', []):
                job_id = job.get('id')
                apply_url = f"https://{self.company_slug}.bamboohr.com/jobs/view.php?id={job_id}"
                
                normalized = {
                    'title': job.get('jobOpening', {}).get('title', ''),
                    'apply_url': apply_url,
                    'description': job.get('jobOpening', {}).get('description', ''),
                    'location': job.get('location', {}).get('city', ''),
                    'id': job_id,
                    'posted_at': job.get('postingDate'),
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"BambooHR scrape failed for {self.company_slug}: {e}")
            return []


def fetch_bamboohr_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch BambooHR jobs."""
    scraper = BambooHRScraper(company_slug)
    return scraper.fetch_jobs()