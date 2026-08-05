"""iCIMS API scraper."""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class IcimsScraper(BaseATSScraper):
    """
    Scrapes jobs from iCIMS API.
    
    iCIMS uses a REST API at:
    https://jobs.jobvite.com/{company}/api/jobs
    
    Some iCIMS instances may require authentication or have different endpoints.
    """
    
    API_URL = "https://jobs.jobvite.com/{company}/api/jobs"
    
    def get_platform_name(self) -> str:
        return 'icims'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from iCIMS API."""
        try:
            url = self.API_URL.format(company=self.company_slug)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            # iCIMS typically returns jobs in an 'items' array
            job_list = data.get('items', data.get('jobs', []))
            
            for job in job_list:
                # Get apply URL - iCIMS usually provides a direct link
                apply_url = job.get('url', '')
                
                if not apply_url:
                    # Try alternative field names
                    apply_url = job.get('apply_url', job.get('link', ''))
                
                if not apply_url:
                    continue
                
                normalized = {
                    'title': job.get('title', ''),
                    'apply_url': apply_url,
                    'direct_apply_url': apply_url,
                    'description': job.get('description', ''),
                    'location': job.get('location', {}).get('name', job.get('location', '')),
                    'id': job.get('id', job.get('jobId', '')),
                    'posted_at': job.get('postedDate', job.get('createdDate', '')),
                    'employment_type': job.get('employmentType', job.get('type')),
                    'departments': [job.get('category', '')] if job.get('category') else [],
                }
                
                jobs.append(self.normalize_job(normalized))
            
            return jobs
            
        except requests.RequestException as e:
            print(f"iCIMS scrape failed for {self.company_slug}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error scraping iCIMS for {self.company_slug}: {e}")
            return []


def fetch_icims_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch iCIMS jobs."""
    scraper = IcimsScraper(company_slug)
    return scraper.fetch_jobs()