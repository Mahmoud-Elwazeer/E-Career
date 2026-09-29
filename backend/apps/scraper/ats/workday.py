"""Workday connector (§11/§15/§17) — deterministic HTTP, no browser.

Workday career sites expose the SAME internal JSON API their own search box
calls, so we do NOT need Playwright for the common case:

    POST https://{tenant}.{wd_server}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
    body: {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}

Hard constraints verified live 2026-09-29 against NVIDIA (total=2000):
- `limit` is capped at 20 SERVER-SIDE. Asking for more returns HTTP 400 or an
  empty array — so we hardcode 20 and paginate by `offset`.
- `total` is reported but Workday stops returning rows past ~2000, so we cap.
- Each posting has `externalPath` (e.g. /job/US-CA-.../..._JR1973150) and
  `bulletFields` (the req id). The apply URL is the employer's own Workday host
  → direct-apply, moat-compliant.

Tenant/site/server can't be derived from a bare slug, so we keep a small
registry (extendable; source discovery can grow it). A source whose slug is not
in the registry returns [] with a clear log line rather than guessing wrong.

Playwright remains available as an OPTIONAL out-of-process fallback (§16/§17)
but is never the default path.
"""
import requests
from typing import List, Dict, Optional, Tuple
from .base import BaseATSScraper


# slug -> (tenant, wd_server, site). Verified-live entries only.
WORKDAY_TENANTS = {
    "nvidia": ("nvidia", "wd5", "NVIDIAExternalCareerSite"),
}

PAGE_SIZE = 20          # Workday server-side hard cap; do NOT raise.
MAX_TOTAL = 2000        # Workday stops returning rows past ~2000.


class WorkdayScraper(BaseATSScraper):
    """Scrapes a Workday career site via its public CXS JSON API."""

    def get_platform_name(self) -> str:
        return 'workday'

    def _resolve(self) -> Optional[Tuple[str, str, str]]:
        return WORKDAY_TENANTS.get(self.company_slug.lower())

    def _host(self, tenant: str, wd_server: str) -> str:
        return f"https://{tenant}.{wd_server}.myworkdayjobs.com"

    def fetch_jobs(self) -> List[Dict]:
        resolved = self._resolve()
        if not resolved:
            print(f"Workday: unknown tenant '{self.company_slug}' "
                  f"(add to WORKDAY_TENANTS: tenant/wd_server/site)")
            return []
        tenant, wd_server, site = resolved
        host = self._host(tenant, wd_server)
        api = f"{host}/wday/cxs/{tenant}/{site}/jobs"

        jobs: List[Dict] = []
        offset = 0
        try:
            while offset < MAX_TOTAL:
                resp = requests.post(
                    api,
                    json={"appliedFacets": {}, "limit": PAGE_SIZE,
                          "offset": offset, "searchText": ""},
                    timeout=20,
                    headers={"User-Agent": "usam-jobs/1.0",
                             "Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                postings = data.get("jobPostings", []) or []
                if not postings:
                    break

                for p in postings:
                    ext = p.get("externalPath", "")
                    if not ext:
                        continue
                    # The employer's OWN Workday job page = direct apply.
                    apply_url = f"{host}/{site}{ext}"
                    req_id = ""
                    bullets = p.get("bulletFields") or []
                    if bullets:
                        req_id = str(bullets[0])
                    # req id is also the trailing _JRxxxx token of externalPath.
                    job_id = req_id or ext.rsplit("_", 1)[-1]
                    normalized = {
                        "title": p.get("title", ""),
                        "apply_url": apply_url,
                        "direct_apply_url": apply_url,
                        "description": "",  # detail endpoint has full text (enrich later)
                        "location": p.get("locationsText", ""),
                        "id": job_id,
                        "ats_job_id": job_id,
                        "posted_at": self._parse_posted(p.get("postedOn", "")),
                        "raw_data": p,
                    }
                    jobs.append(self.normalize_job(normalized))

                total = data.get("total")
                offset += PAGE_SIZE
                if total is not None and offset >= min(total, MAX_TOTAL):
                    break

            return jobs
        except requests.RequestException as e:
            print(f"Workday scrape failed for {self.company_slug}: {e}")
            return jobs  # partial results are better than none

    @staticmethod
    def _parse_posted(posted_on: str) -> Optional[str]:
        """Workday gives relative strings ('Posted Today', 'Posted 3 Days Ago').
        Convert the common cases to an ISO date; leave others None (enrichment
        can refine from the detail endpoint)."""
        from datetime import date, timedelta
        s = (posted_on or "").lower()
        if "today" in s:
            return date.today().isoformat()
        if "yesterday" in s:
            return (date.today() - timedelta(days=1)).isoformat()
        import re
        m = re.search(r"(\d+)\s*day", s)
        if m:
            return (date.today() - timedelta(days=int(m.group(1)))).isoformat()
        m = re.search(r"(\d+)\+?\s*month", s)
        if m:
            return (date.today() - timedelta(days=30 * int(m.group(1)))).isoformat()
        return None


def fetch_workday_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Workday jobs."""
    return WorkdayScraper(company_slug).fetch_jobs()
