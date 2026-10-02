"""Recruitee API scraper.

Verified live 2026-10-02 against a real company board
(veocareers.recruitee.com): 57 real, current job offers returned.

Endpoint: https://{company_subdomain}.recruitee.com/api/offers/
Public, unauthenticated, documented at https://docs.recruitee.com/reference/offers-get
(note: that page documents a DIFFERENT, auth-required legacy endpoint,
api.recruitee.com/c/{company_id}/offers, which returned 401 when tested live.
The subdomain-based /api/offers/ endpoint used here is the one that actually
works unauthenticated and is what apps/scraper/pipeline/source_discovery.py
already probes for ATS detection - this connector completes that half of the
contract with a real fetcher.)

Response shape confirmed live: {"offers": [...]}, each offer has `title`,
`careers_url` (the job's own listing page on the employer's recruitee
subdomain - moat-compliant, direct, not a `.../c/new` apply-form link),
`employment_type_code`, `remote` (bool), `salary` ({min,max,period,currency},
usually all null), `description` (HTML), `id`, `slug`, `country`/`city`,
`published_at`.
"""
import requests
from typing import List, Dict
from .base import BaseATSScraper


class RecruiteeScraper(BaseATSScraper):
    """Scrapes jobs from the Recruitee careers-site API."""

    API_URL = "https://{company_subdomain}.recruitee.com/api/offers/"
    HEADERS = {
        "Accept": "application/json",
        "User-Agent": "USAM-Career-Compass/1.0",
    }

    def get_platform_name(self) -> str:
        return "recruitee"

    def fetch_jobs(self) -> List[Dict]:
        try:
            url = self.API_URL.format(company_subdomain=self.company_slug)
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            print(f"Recruitee scrape failed for {self.company_slug}: {e}")
            return []

        jobs = []
        for offer in data.get("offers", []):
            offer_id = offer.get("id")
            if not offer_id:
                continue

            # careers_url is the job's own listing page (direct, employer-
            # hosted) - careers_apply_url points at the "/c/new" application
            # FORM, which is a worse "job page" URL for our direct-apply
            # moat check even though it's also employer-hosted.
            apply_url = offer.get("careers_url") or ""

            salary = offer.get("salary") or {}
            location = offer.get("city") or offer.get("country") or ""

            normalized = {
                "title": offer.get("title", ""),
                "apply_url": apply_url,
                "description": offer.get("description", ""),
                "location": location,
                "id": offer_id,
                "posted_at": offer.get("published_at", ""),
                "employment_type": offer.get("employment_type_code", ""),
                "remote_type": "remote" if offer.get("remote") else "onsite",
                "salary_min": salary.get("min"),
                "salary_max": salary.get("max"),
                "salary_currency": salary.get("currency") or "USD",
            }
            jobs.append(self.normalize_job(normalized))

        return jobs


def fetch_recruitee_jobs(company_subdomain: str) -> List[Dict]:
    """Convenience function to fetch Recruitee jobs."""
    scraper = RecruiteeScraper(company_subdomain)
    return scraper.fetch_jobs()
