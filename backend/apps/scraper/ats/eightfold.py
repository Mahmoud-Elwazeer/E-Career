"""Eightfold AI careers-hub scraper (§10).

Many large employers (e.g. Netflix at explore.jobs.netflix.net) run their
careers site on Eightfold AI rather than a classic ATS. Eightfold exposes a
PUBLIC, structured JSON jobs API:

    https://{host}/api/apply/v2/jobs?domain={domain}&start={n}&num={k}

Verified live 2026-09-29 for Netflix: 474 positions, each with a
`canonicalPositionUrl` that is the employer's OWN job page
(https://explore.jobs.netflix.net/careers/job/{id}) — a direct-apply,
moat-compliant link (not an aggregator).

We key an Eightfold source by "{tenant}" where tenant carries both the host and
domain. To keep the existing `company_slug`-based dispatch, the source slug is
the tenant name and we resolve host/domain from a small registry (extendable),
falling back to a sensible default.
"""
import requests
from typing import List, Dict, Optional
from .base import BaseATSScraper


# tenant -> (host, domain). Host is where the careers hub lives; domain is the
# Eightfold customer domain used by the API. Add entries as coverage grows;
# source discovery can populate this over time.
EIGHTFOLD_TENANTS = {
    "netflix": ("explore.jobs.netflix.net", "netflix.com"),
}


class EightfoldScraper(BaseATSScraper):
    """Scrapes jobs from an Eightfold AI careers hub public API."""

    PAGE_SIZE = 50
    MAX_PAGES = 40  # safety cap (50*40 = 2000 postings)

    def get_platform_name(self) -> str:
        return 'eightfold'

    def _resolve(self) -> Optional[tuple]:
        return EIGHTFOLD_TENANTS.get(self.company_slug.lower())

    def fetch_jobs(self) -> List[Dict]:
        resolved = self._resolve()
        if not resolved:
            print(f"Eightfold: unknown tenant '{self.company_slug}' "
                  f"(add to EIGHTFOLD_TENANTS)")
            return []
        host, domain = resolved

        jobs: List[Dict] = []
        start = 0
        try:
            for _page in range(self.MAX_PAGES):
                url = (f"https://{host}/api/apply/v2/jobs"
                       f"?domain={domain}&start={start}&num={self.PAGE_SIZE}")
                resp = requests.get(
                    url, timeout=20,
                    headers={"User-Agent": "usam-jobs/1.0"},
                )
                resp.raise_for_status()
                data = resp.json()
                positions = data.get('positions', []) or []
                if not positions:
                    break

                for p in positions:
                    apply_url = p.get('canonicalPositionUrl', '')
                    if not apply_url:
                        continue
                    location = p.get('location', '')
                    if not location and p.get('locations'):
                        location = ', '.join(p.get('locations') or [])
                    normalized = {
                        'title': p.get('name', '') or p.get('posting_name', ''),
                        'apply_url': apply_url,
                        'description': p.get('job_description', ''),
                        'location': location,
                        'id': p.get('ats_job_id') or p.get('display_job_id') or p.get('id'),
                        'posted_at': self._epoch(p.get('t_create') or p.get('t_update')),
                        'remote_type': self._remote(p),
                    }
                    jobs.append(self.normalize_job(normalized))

                # Advance; stop once we've pulled the reported total.
                total = data.get('count')
                start += self.PAGE_SIZE
                if total is not None and start >= total:
                    break

            return jobs
        except requests.RequestException as e:
            print(f"Eightfold scrape failed for {self.company_slug}: {e}")
            return jobs  # return whatever we collected before the error

    def _remote(self, p: Dict) -> str:
        opt = (p.get('work_location_option') or p.get('location_flexibility') or '').lower()
        if 'remote' in opt:
            return 'remote'
        if 'hybrid' in opt:
            return 'hybrid'
        loc = (p.get('location') or '').lower()
        if 'remote' in loc:
            return 'remote'
        return 'onsite'

    @staticmethod
    def _epoch(ts) -> Optional[str]:
        """Eightfold timestamps are unix seconds; return ISO date string."""
        try:
            from datetime import datetime, timezone as _tz
            return datetime.fromtimestamp(int(ts), _tz.utc).date().isoformat()
        except (TypeError, ValueError, OSError):
            return None


def fetch_eightfold_jobs(company_slug: str) -> List[Dict]:
    """Convenience function to fetch Eightfold jobs."""
    return EightfoldScraper(company_slug).fetch_jobs()
