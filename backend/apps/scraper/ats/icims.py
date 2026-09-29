"""iCIMS career-portal scraper.

iCIMS employers publish jobs on tenant portals at:
  https://careers-{tenant}.icims.com/jobs/search?ss=1&searchScreenTitle=...
The search page lists jobs whose detail/apply links live on the SAME tenant
domain (careers-{tenant}.icims.com) — i.e. genuine employer ATS destinations
(moat-compliant, never an aggregator). There is no simple unauthenticated JSON
list endpoint that works across all tenants, so we parse the public search page
with BeautifulSoup (already a project dependency).

Previous implementation pointed at a Jobvite URL (jobs.jobvite.com) which is a
different ATS entirely — that was a bug and never returned iCIMS jobs.
Content was rephrased for compliance with licensing restrictions.
"""
import re
import requests
import structlog
from typing import List, Dict
from urllib.parse import urljoin

from .base import BaseATSScraper

logger = structlog.get_logger()


class IcimsScraper(BaseATSScraper):
    """Scrapes published jobs from a company's public iCIMS career portal."""

    PORTAL = "https://careers-{tenant}.icims.com"
    SEARCH_PATH = "/jobs/search?ss=1&hashed=-435695674&mobile=false&width=1200"
    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/json",
        "User-Agent": "Mozilla/5.0 (compatible; USAM-Career-Compass/1.0)",
    }
    MAX_PAGES = 20

    def get_platform_name(self) -> str:
        return "icims"

    def _tenant(self) -> str:
        # Slug may be given as bare tenant ("rambus") or full host.
        s = self.company_slug.strip().lower()
        s = s.replace("careers-", "").replace(".icims.com", "")
        return s

    def fetch_jobs(self) -> List[Dict]:
        tenant = self._tenant()
        base = self.PORTAL.format(tenant=tenant)
        jobs: List[Dict] = []
        try:
            from bs4 import BeautifulSoup
        except Exception:
            logger.warning("icims_no_bs4", tenant=tenant)
            return []

        try:
            for page in range(1, self.MAX_PAGES + 1):
                url = urljoin(base, self.SEARCH_PATH) + f"&pr={page}"
                resp = requests.get(url, headers=self.HEADERS, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # iCIMS job rows link to /jobs/{id}/{slug}/job on the tenant host.
                anchors = soup.select('a[href*="/jobs/"]')
                page_jobs = 0
                seen = set()
                for a in anchors:
                    href = a.get("href", "")
                    m = re.search(r"/jobs/(\d+)/", href)
                    if not m:
                        continue
                    job_id = m.group(1)
                    if job_id in seen:
                        continue
                    seen.add(job_id)
                    apply_url = urljoin(base, href)
                    title = a.get_text(strip=True) or ""
                    if not title:
                        continue
                    jobs.append(self.normalize_job({
                        "title": title,
                        "apply_url": apply_url,
                        "direct_apply_url": apply_url,
                        "description": "",
                        "location": "",
                        "id": job_id,
                        "posted_at": "",
                    }))
                    page_jobs += 1

                if page_jobs == 0:
                    break

            return jobs
        except requests.RequestException as e:
            logger.warning("icims_scrape_failed", tenant=tenant, error=str(e))
            return jobs


def fetch_icims_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch iCIMS jobs."""
    return IcimsScraper(company_slug).fetch_jobs()
