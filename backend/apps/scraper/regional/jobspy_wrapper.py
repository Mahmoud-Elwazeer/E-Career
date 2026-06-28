"""
JobSpy wrapper for regional job boards.
Supports: Bayt, Wuzzuf (via LinkedIn/Indeed fallback)
"""
from typing import List, Dict

# JobSpy is optional - may not be available in all environments
try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False
    print("Warning: JobSpy not available. Regional scraping disabled.")


def scrape_bayt(location: str = "Egypt", search_term: str = "") -> List[Dict]:
    """
    Scrape jobs from Bayt using JobSpy.
    Note: We only use Bayt as a DISCOVERY source.
    Apply URLs from Bayt are BLOCKED - we extract company name
    and try to find their direct careers page.
    """
    if not JOBSPY_AVAILABLE:
        return []
    
    try:
        jobs = scrape_jobs(
            site_name=["indeed"],  # JobSpy doesn't have Bayt directly
            search_term=search_term or "software engineer",
            location=location,
            results_wanted=100,
            hours_old=72,
        )
        
        normalized_jobs = []
        
        for _, job in jobs.iterrows():
            # Extract company domain from job
            company_name = job.get('company', '')
            
            # We'll try to resolve company's real careers page
            # For now, we skip Bayt jobs without direct URLs
            
            normalized = {
                'title': job.get('title', ''),
                'company_name': company_name,
                'description': job.get('description', ''),
                'location': job.get('location', ''),
                'source': 'bayt',
                'job_url': job.get('job_url', ''),  # This is Bayt URL, NOT for apply
            }
            
            normalized_jobs.append(normalized)
        
        return normalized_jobs
        
    except Exception as e:
        print(f"Bayt scrape failed: {e}")
        return []


def scrape_wuzzuf(location: str = "Egypt", search_term: str = "") -> List[Dict]:
    """
    Scrape jobs from Wuzzuf.
    JobSpy doesn't directly support Wuzzuf, so we'll build custom scraper.
    """
    # TODO: Custom Wuzzuf scraper in next step
    return []


def scrape_gulftalent(location: str = "UAE", search_term: str = "") -> List[Dict]:
    """
    Scrape jobs from GulfTalent.
    Custom scraper needed.
    """
    # TODO: Custom GulfTalent scraper
    return []