"""BambooHR careers-board API scraper.

CORRECTED 2026-10-03 - the previous implementation targeted a DEAD endpoint
(`{company}.bamboohr.com/jobs/list/`, confirmed live to return HTTP 404) with
a JSON shape assumption (`result[].jobOpening.title`) that does not match the
real API either. Verified live against a real board (cubecare.bamboohr.com,
14 real open roles):

  LIST:   https://{company}.bamboohr.com/careers/list
          -> {"meta": {"totalCount": N}, "result": [{"id", "jobOpeningName",
             "departmentLabel", "employmentStatusLabel", "atsLocation": {...},
             "locationType", ...}, ...]}
          Does NOT include the full description - only summary fields.

  DETAIL: https://{company}.bamboohr.com/careers/{id}/detail
          -> {"result": {"jobOpening": {"jobOpeningShareUrl", "description"
             (full HTML), "datePosted", "compensation",
             "minimumExperience", ...}}}
          `jobOpeningShareUrl` is the job's own page on the employer's OWN
          bamboohr.com subdomain (e.g. https://cubecare.bamboohr.com/careers/439)
          - moat-compliant, direct, not an aggregator.

This connector fetches the list, then fetches each job's detail page for the
full description + canonical share URL (bounded by MAX_DETAIL_FETCHES to
avoid unbounded N+1 cost on very large boards; remaining jobs still get a
constructed share URL and the summary-only data).
"""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class BambooHRScraper(BaseATSScraper):
    """Scrapes jobs from a BambooHR company's public careers board."""

    LIST_URL = "https://{company}.bamboohr.com/careers/list"
    DETAIL_URL = "https://{company}.bamboohr.com/careers/{job_id}/detail"
    HEADERS = {
        "Accept": "application/json",
        "User-Agent": "USAM-Career-Compass/1.0",
    }

    # Cap on how many job detail pages we fetch per run (N+1 request cost
    # guard - the list endpoint alone is enough to produce valid, moat-
    # compliant jobs even without the detail fetch, since the share URL is
    # deterministically {company}.bamboohr.com/careers/{id}).
    MAX_DETAIL_FETCHES = 60

    def get_platform_name(self) -> str:
        return 'bamboohr'

    def fetch_jobs(self) -> List[Dict]:
        try:
            url = self.LIST_URL.format(company=self.company_slug)
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            print(f"BambooHR scrape failed for {self.company_slug}: {e}")
            return []

        results = data.get('result', [])
        jobs = []
        for i, opening in enumerate(results):
            job_id = opening.get('id')
            if not job_id:
                continue

            # The share URL is deterministic even without a detail fetch.
            apply_url = f"https://{self.company_slug}.bamboohr.com/careers/{job_id}"

            ats_location = opening.get('atsLocation') or {}
            location = ats_location.get('city') or ats_location.get('state') or ats_location.get('country') or ''

            description = ''
            posted_at = None
            if i < self.MAX_DETAIL_FETCHES:
                detail = self._fetch_detail(job_id)
                if detail:
                    description = detail.get('description', '')
                    posted_at = detail.get('datePosted')
                    apply_url = detail.get('jobOpeningShareUrl') or apply_url

            is_remote = (ats_location.get('state') or '').lower() == 'remote' or \
                        (ats_location.get('city') or '').lower() == 'remote'

            normalized = {
                'title': opening.get('jobOpeningName', ''),
                'apply_url': apply_url,
                'description': description,
                'location': location,
                'id': job_id,
                'posted_at': posted_at,
                'remote_type': 'remote' if is_remote else 'onsite',
            }
            jobs.append(self.normalize_job(normalized))

        return jobs

    def _fetch_detail(self, job_id) -> dict:
        """Fetch one job's detail page for the full description + canonical
        share URL. Returns {} on any failure - the caller already has a
        valid fallback apply_url, so a detail-fetch failure degrades
        gracefully instead of dropping the job."""
        try:
            url = self.DETAIL_URL.format(company=self.company_slug, job_id=job_id)
            resp = requests.get(url, headers=self.HEADERS, timeout=15)
            resp.raise_for_status()
            return (resp.json().get('result') or {}).get('jobOpening') or {}
        except (requests.RequestException, ValueError):
            return {}


def fetch_bamboohr_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch BambooHR jobs."""
    scraper = BambooHRScraper(company_slug)
    return scraper.fetch_jobs()
