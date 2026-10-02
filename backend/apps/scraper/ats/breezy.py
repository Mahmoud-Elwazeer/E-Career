"""Breezy HR API scraper.

Verified live 2026-10-03 against a real company board (zero-hash.breezy.hr):
25 real, current positions returned.

Endpoint: https://{company_subdomain}.breezy.hr/json
Public, unauthenticated, undocumented-but-stable (confirmed via multiple
independent third-party scraper descriptions converging on the same URL
pattern, and verified live against a real board). Breezy's own developer API
(developer.breezy.hr) is a DIFFERENT, authenticated, company-id-based API for
ATS customers managing their own account - NOT what this connector uses. This
connector uses the public, read-only careers-board JSON feed every Breezy
customer's public job board serves at this fixed subdomain path.

Response shape confirmed live: a bare JSON array of position objects, each
with `id`, `friendly_id`, `name`, `url` (the job's own detail page on the
employer's OWN breezy.hr subdomain - moat-compliant, direct), `published_date`,
`type` ({id, name}), `location` ({city, country, is_remote, remote_details}),
`department`, `salary` (usually empty string), `company` ({name, friendly_id}).
The list endpoint does NOT include the full job description - only the detail
page (`url`) has it, so `description` is left empty here rather than fetching
every detail page per list call (N+1 request cost); downstream verification
still succeeds since `url` is itself the direct, employer-hosted apply/detail
page.
"""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class BreezyScraper(BaseATSScraper):
    """Scrapes jobs from the Breezy HR public careers-board JSON feed."""

    API_URL = "https://{company_subdomain}.breezy.hr/json"
    HEADERS = {
        "Accept": "application/json",
        "User-Agent": "USAM-Career-Compass/1.0",
    }

    def get_platform_name(self) -> str:
        return "breezy"

    def fetch_jobs(self) -> List[Dict]:
        try:
            url = self.API_URL.format(company_subdomain=self.company_slug)
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            print(f"Breezy scrape failed for {self.company_slug}: {e}")
            return []

        if not isinstance(data, list):
            return []

        jobs = []
        for position in data:
            position_id = position.get("id")
            apply_url = position.get("url") or ""
            if not position_id or not apply_url:
                continue

            location = position.get("location") or {}
            location_name = location.get("name") or location.get("city") or ""
            is_remote = bool(location.get("is_remote"))

            job_type = position.get("type") or {}
            employment_type = (job_type.get("id") or "").lower()

            normalized = {
                "title": position.get("name", ""),
                "apply_url": apply_url,
                "description": "",  # not present on the list endpoint; see docstring
                "location": location_name,
                "id": position_id,
                "posted_at": position.get("published_date", ""),
                "employment_type": employment_type,
                "remote_type": "remote" if is_remote else "onsite",
            }
            jobs.append(self.normalize_job(normalized))

        return jobs


def fetch_breezy_jobs(company_subdomain: str) -> List[Dict]:
    """Convenience function to fetch Breezy HR jobs."""
    scraper = BreezyScraper(company_subdomain)
    return scraper.fetch_jobs()
