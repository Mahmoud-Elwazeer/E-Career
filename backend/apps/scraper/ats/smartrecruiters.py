"""SmartRecruiters Posting API scraper.

Uses the PUBLIC Posting API which requires no auth for published postings:
  GET https://api.smartrecruiters.com/v1/companies/{companyIdentifier}/postings
The {companyIdentifier} is the slug that appears after the "/" in
https://careers.smartrecruiters.com/{slug} — i.e. exactly the company_slug we
already have (per official docs developers.smartrecruiters.com/docs/endpoints).
The response is paginated ({limit,offset} → {totalFound, content[]}); the apply
destination is the posting's own careers URL (a real direct-apply page).
Content was rephrased for compliance with licensing restrictions.
"""
import requests
import structlog
from typing import List, Dict
from .base import BaseATSScraper

logger = structlog.get_logger()


class SmartRecruitersScraper(BaseATSScraper):
    """Scrapes published jobs from the SmartRecruiters public Posting API."""

    LIST_URL = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
    PAGE_LIMIT = 100  # API max per page
    MAX_PAGES = 20    # safety cap (≤2000 postings/company)
    HEADERS = {
        'Accept': 'application/json',
        'User-Agent': 'USAM-Career-Compass/1.0',
    }

    def get_platform_name(self) -> str:
        return 'smartrecruiters'

    def fetch_jobs(self) -> List[Dict]:
        """Fetch all published postings, following pagination."""
        url = self.LIST_URL.format(company=self.company_slug)
        jobs: List[Dict] = []
        offset = 0
        try:
            for _ in range(self.MAX_PAGES):
                response = requests.get(
                    url,
                    params={'limit': self.PAGE_LIMIT, 'offset': offset},
                    headers=self.HEADERS,
                    timeout=15,
                )
                response.raise_for_status()
                data = response.json()
                content = data.get('content', []) or []
                if not content:
                    break

                for job in content:
                    normalized = self._normalize_posting(job)
                    if normalized:
                        jobs.append(self.normalize_job(normalized))

                offset += self.PAGE_LIMIT
                total = data.get('totalFound', 0)
                if offset >= total or len(content) < self.PAGE_LIMIT:
                    break

            return jobs
        except requests.RequestException as e:
            logger.warning(
                "smartrecruiters_scrape_failed",
                company=self.company_slug,
                error=str(e),
            )
            return jobs  # return whatever we collected before failure

    def _normalize_posting(self, job: Dict) -> Dict | None:
        job_id = job.get('id', '')
        if not job_id:
            return None

        # Real direct-apply destination on the company's SmartRecruiters site.
        apply_url = (
            job.get('applyUrl')
            or job.get('ref')
            or f"https://jobs.smartrecruiters.com/{self.company_slug}/{job_id}"
        )

        loc = job.get('location', {}) or {}
        location = ", ".join(
            p for p in (loc.get('city', ''), loc.get('region', ''), loc.get('country', '')) if p
        )

        department = (job.get('department') or {}).get('label', '') if job.get('department') else ''
        if not department and job.get('function'):
            department = (job.get('function') or {}).get('label', '')

        emp = (job.get('typeOfEmployment') or {}).get('label', '') if job.get('typeOfEmployment') else ''

        return {
            'title': job.get('name', ''),
            'apply_url': apply_url,
            'direct_apply_url': apply_url,
            # List endpoint carries no full description; the detail endpoint
            # (/postings/{id}) has jobAd.sections. Left blank here so the
            # normalizer/verifier can enrich later without fabricating text.
            'description': job.get('summary', '') or '',
            'location': location,
            'id': job_id,
            'posted_at': job.get('releasedDate', job.get('createdOn', '')),
            'departments': [department] if department else [],
            'employment_type': emp,
            'experience_level': (job.get('experienceLevel') or {}).get('label', '') if job.get('experienceLevel') else '',
            'remote_type': self._get_remote_type(job),
            'salary_min': None,
            'salary_max': None,
            'salary_currency': 'USD',
        }
    
    def _get_remote_type(self, job: Dict) -> str:
        """Determine remote type from SmartRecruiters Posting API fields."""
        location = job.get('location', {}) or {}
        # The Posting API exposes a boolean 'remote' flag on location.
        if location.get('remote') is True:
            return 'remote'

        blob = " ".join(
            str(v).lower()
            for v in (
                location.get('city', ''),
                location.get('region', ''),
                (job.get('typeOfEmployment') or {}).get('label', ''),
            )
        )
        if 'remote' in blob or 'virtual' in blob:
            return 'remote'
        if 'hybrid' in blob or 'flexible' in blob:
            return 'hybrid'
        return 'onsite'


def fetch_smartrecruiters_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch SmartRecruiters jobs."""
    scraper = SmartRecruitersScraper(company_slug)
    return scraper.fetch_jobs()