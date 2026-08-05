"""SAP SuccessFactors API scraper."""
import requests
from typing import List, Dict, Optional
from .base import BaseATSScraper


class SAPScraper(BaseATSScraper):
    """
    Scrapes jobs from SAP SuccessFactors.
    
    SAP SuccessFactors uses REST API endpoints.
    Common endpoints:
    - /odata/v2/Job
    - /odata/v2/JobPosting
    
    Authentication typically requires OAuth2 or API keys.
    """
    
    def __init__(self, company_slug: str, api_key: Optional[str] = None):
        super().__init__(company_slug)
        self.api_key = api_key
        # SAP endpoints can vary by instance
        self.base_url = f"https://jobs.sap.com"
    
    def get_platform_name(self) -> str:
        return 'sap'
    
    def fetch_jobs(self) -> List[Dict]:
        """Fetch all jobs from SAP SuccessFactors."""
        try:
            jobs = []
            
            # Try to fetch jobs from SAP jobs site
            # SAP typically uses jobs.sap.com for public listings
            url = f"{self.base_url}/search"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
            }
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # SAP jobs site may require JavaScript rendering
            # For now, try direct API access
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    job_list = data.get('results', data.get('jobs', data.get('content', [])))
                    
                    for job in job_list:
                        apply_url = job.get('apply_url', job.get('url', job.get('link', '')))
                        
                        if not apply_url:
                            # Try to construct apply URL from job ID
                            job_id = job.get('id', job.get('jobId', ''))
                            if job_id:
                                apply_url = f"{self.base_url}/job/{job_id}"
                        
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
                            'experience_level': job.get('experienceLevel'),
                            'remote_type': job.get('remoteType'),
                            'salary_min': job.get('salaryMin'),
                            'salary_max': job.get('salaryMax'),
                            'salary_currency': job.get('salaryCurrency', 'USD'),
                            'departments': [job.get('category', '')] if job.get('category') else [],
                        }
                        
                        jobs.append(self.normalize_job(normalized))
                except Exception:
                    # If JSON parsing fails, try HTML parsing or return empty
                    print(f"SAP response not in expected format for {self.company_slug}")
            
            return jobs
            
        except requests.RequestException as e:
            print(f"SAP scrape failed for {self.company_slug}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error scraping SAP for {self.company_slug}: {e}")
            return []


def fetch_sap_jobs(company_slug: str, api_key: Optional[str] = None) -> List[Dict]:
    """Convenience function to fetch SAP jobs."""
    scraper = SAPScraper(company_slug, api_key)
    return scraper.fetch_jobs()