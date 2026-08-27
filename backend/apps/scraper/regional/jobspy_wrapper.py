"""
JobSpy wrapper for regional job discovery.

IMPORTANT: JobSpy scrapes Indeed/LinkedIn, NOT the named regional boards.
These functions are named by TARGET REGION, not by data source.
The actual source is Indeed (via JobSpy). Results are used for company
discovery only — apply URLs from aggregators are discarded.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False


def scrape_region_egypt(search_term: str = "software engineer") -> List[Dict]:
    """
    Discover jobs in Egypt via Indeed (JobSpy).

    Results are used for COMPANY DISCOVERY only — we extract company names
    and resolve their direct careers pages. Apply URLs from Indeed are not used.
    """
    if not JOBSPY_AVAILABLE:
        return []

    try:
        jobs = scrape_jobs(
            site_name=["indeed"],
            search_term=search_term,
            location="Egypt",
            results_wanted=100,
            hours_old=72,
        )

        results = []
        for _, job in jobs.iterrows():
            results.append({
                'title': job.get('title', ''),
                'company_name': job.get('company', ''),
                'description': job.get('description', ''),
                'location': job.get('location', ''),
                'source': 'indeed_egypt',
                'source_url': job.get('job_url', ''),
            })
        return results

    except Exception as e:
        logger.error("Regional scrape (Egypt) failed: %s", e)
        return []


def scrape_region_gulf(search_term: str = "software engineer") -> List[Dict]:
    """
    Discover jobs in Gulf region via Indeed (JobSpy).

    Same discovery-only pattern as scrape_region_egypt.
    """
    if not JOBSPY_AVAILABLE:
        return []

    try:
        jobs = scrape_jobs(
            site_name=["indeed"],
            search_term=search_term,
            location="UAE",
            results_wanted=100,
            hours_old=72,
        )

        results = []
        for _, job in jobs.iterrows():
            results.append({
                'title': job.get('title', ''),
                'company_name': job.get('company', ''),
                'description': job.get('description', ''),
                'location': job.get('location', ''),
                'source': 'indeed_gulf',
                'source_url': job.get('job_url', ''),
            })
        return results

    except Exception as e:
        logger.error("Regional scrape (Gulf) failed: %s", e)
        return []


# Backwards compatibility — these old names were misleading (they never scraped
# the named boards, only Indeed). Kept as aliases to avoid breaking Celery tasks
# that reference them by name.
scrape_bayt = scrape_region_egypt
scrape_gulftalent = scrape_region_gulf
