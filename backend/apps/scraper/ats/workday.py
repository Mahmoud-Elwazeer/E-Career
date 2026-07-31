"""
Workday scraper - requires Playwright for JS rendering.
Workday is heavily JavaScript-based.
"""
from typing import List, Dict, Optional
from .base import BaseATSScraper


class WorkdayScraper(BaseATSScraper):
    """
    Workday scraper using Playwright for headless browser automation.
    
    Workday uses a POST-based JSON API at:
    /wday/cxs/{company}/{site}/jobs
    
    This requires JavaScript rendering to get the proper API endpoints
    and authentication tokens.
    """
    
    def get_platform_name(self) -> str:
        return 'workday'
    
    def fetch_jobs(self) -> List[Dict]:
        """
        Fetch all jobs from Workday using Playwright.
        
        Workday requires:
        1. Load the careers page to get the company/site identifiers
        2. Extract the API endpoint and any required tokens
        3. POST to /wday/cxs/{company}/{site}/jobs
        """
        try:
            import asyncio
            from playwright.async_api import async_playwright
            
            # Get company and site from slug
            # Workday URLs typically follow: company.workday.com/company
            company_slug = self.company_slug.replace('-', '')
            
            # Default site is usually the same as company
            site = company_slug
            
            jobs = []
            
            # Try to fetch jobs using Playwright
            asyncio.run(self._fetch_jobs_with_playwright(company_slug, site, jobs))
            
            return jobs
            
        except ImportError:
            print("Playwright not installed. Install with: pip install playwright && playwright install chromium")
            return []
        except Exception as e:
            print(f"Workday scrape failed for {self.company_slug}: {e}")
            return []
    
    async def _fetch_jobs_with_playwright(self, company: str, site: str, jobs: List[Dict]):
        """Fetch jobs using Playwright async API."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set user agent to avoid blocking
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                # Try to load the careers page
                careers_url = f"https://{company}.workday.com/{company}/job"
                try:
                    await page.goto(careers_url, timeout=30000)
                except Exception:
                    # Try alternative URL format
                    careers_url = f"https://{site}.workday.com/{company}/jobs"
                    try:
                        await page.goto(careers_url, timeout=30000)
                    except Exception:
                        await browser.close()
                        return
                
                # Wait for jobs to load
                await page.wait_for_selector('.jobListing', timeout=10000)
                
                # Extract job data from the page
                job_elements = await page.query_selector_all('.jobListing')
                
                for element in job_elements:
                    try:
                        job = await self._extract_job_from_element(element)
                        if job.get('direct_apply_url'):
                            jobs.append(job)
                    except Exception:
                        continue
                
                await browser.close()
                
        except Exception as e:
            print(f"Playwright fetch failed: {e}")
    
    async def _extract_job_from_element(self, element) -> Dict:
        """Extract job data from a Workday job listing element."""
        # Try to get job title
        title_elem = await element.query_selector('.jobTitle')
        title = await title_elem.inner_text() if title_elem else ''
        
        # Try to get job URL
        link_elem = await element.query_selector('a')
        apply_url = await link_elem.get_attribute('href') if link_elem else ''
        
        # Try to get location
        location_elem = await element.query_selector('.jobLocation')
        location = await location_elem.inner_text() if location_elem else ''
        
        # Try to get department
        dept_elem = await element.query_selector('.jobDepartment')
        department = await dept_elem.inner_text() if dept_elem else ''
        
        return {
            'title': title.strip(),
            'apply_url': apply_url,
            'direct_apply_url': apply_url,
            'description': '',  # Workday often loads description on click
            'location': location.strip(),
            'employment_type': None,
            'experience_level': None,
            'remote_type': 'onsite' if 'onsite' in location.lower() else 'remote' if 'remote' in location.lower() else None,
            'salary_min': None,
            'salary_max': None,
            'salary_currency': 'USD',
            'id': None,
            'ats_job_id': None,
            'posted_at': None,
            'departments': [department.strip()] if department else [],
            'raw_data': {},
        }


def fetch_workday_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Workday jobs."""
    scraper = WorkdayScraper(company_slug)
    return scraper.fetch_jobs()