"""Jobvite connector — DISCOVERY_UNSUPPORTED (§6).

STATUS: not enabled. Marked unsupported WITH EVIDENCE rather than shipping a
brittle HTML scraper or a connector that silently can't authenticate.

Why it is hard to do reliably right now:
- Jobvite's official structured API (api.jobvite.com/api/v2/job) requires
  PER-EMPLOYER credentials (an `api` feed key + a `sc` secret/company code).
  Confirmed via Jobvite's own Help Center article "Jobvite API" (as of this
  engagement): authentication is header-based (encrypted or plaintext API
  key + secret), not a public/anonymous mode. There is no generic,
  unauthenticated JSON endpoint that works for an arbitrary company the way
  Greenhouse/Lever/Ashby/Recruitee's public board APIs do.
- The only unauthenticated option is scraping the server-rendered HTML
  careers page at jobs.jobvite.com/careers/{company} (confirmed live: this
  page returns real job titles/locations as plain server-rendered HTML with
  no backing JSON endpoint found). Multiple third-party scraping services
  independently confirm this is HTML-only, not JSON. Building a parser
  against unversioned, unofficial HTML markup is exactly the "shipping a
  connector that guesses" anti-pattern already rejected for Oracle/SAP in
  this codebase - a markup change silently breaks it with no error, and a
  wrong assumption could surface a non-direct-apply URL and weaken the
  platform's moat.

Note: this is a DIFFERENT and now-confirmed-correct situation from the
historical bug noted in icims.py's docstring - a previous iCIMS
implementation pointed at a Jobvite URL by mistake. This module is the
first real investigation of Jobvite as its own ATS, not a correction of
that unrelated bug.

Path to enable (future, if ever justified): if a specific employer using
Jobvite provides USAM with their own `api` feed key + `sc` secret (the same
credentials they'd give any legitimate HR integration), a per-tenant
connector using those credentials could be built - mirroring the
WORKDAY_TENANTS / ORACLE_TENANTS per-tenant registry pattern. Scraping the
public HTML page is NOT recommended as a fallback given the moat/
reliability concerns above; if Tier-3 adaptive extraction (Scrapling) is
ever pointed at a Jobvite board, treat it as a last resort, not a default.
"""
from typing import List, Dict, Optional
from .base import BaseATSScraper

# Flip to True only once real per-tenant API credentials exist for a
# specific employer (see module docstring - this is not derivable from a
# bare company slug the way other connectors' tenant registries are).
SUPPORTED = False

# slug -> (api_feed_key, sc_secret). Populate ONLY with credentials a real
# employer has explicitly provided to USAM for this purpose.
JOBVITE_TENANTS: Dict[str, tuple] = {}


class JobviteScraper(BaseATSScraper):
    """Jobvite connector (currently unsupported — see module docstring)."""

    def get_platform_name(self) -> str:
        return 'jobvite'

    def fetch_jobs(self) -> List[Dict]:
        if not SUPPORTED or self.company_slug.lower() not in JOBVITE_TENANTS:
            print(f"Jobvite: DISCOVERY_UNSUPPORTED for '{self.company_slug}' — "
                  f"requires per-employer API credentials (see jobvite.py docstring)")
            return []
        return []


def fetch_jobvite_jobs(company_slug: str, api_key: Optional[str] = None) -> List[Dict]:
    """Convenience function (returns [] while Jobvite is unsupported)."""
    return JobviteScraper(company_slug).fetch_jobs()
