"""Oracle Cloud HCM / Recruiting connector — DISCOVERY_UNSUPPORTED (§11/§13/§14).

STATUS: not enabled. Marked unsupported WITH EVIDENCE rather than shipping a
connector that guesses, because doing it wrong would either yield nothing or
(worse) surface non-direct-apply URLs and weaken the moat.

Why it is hard to do reliably right now:
- Oracle Recruiting Cloud (ORC) job feeds are per-tenant and site-specific. The
  public REST surface is typically:
    https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions
    ?onlyData=true&expand=requisitionList.secondaryLocations&finder=findReqs;...
  where {host} and the site code differ per employer and are NOT derivable from
  a bare company slug.
- Many tenants gate the feed behind a site token / require the exact
  `siteNumber` finder param; without per-tenant config we cannot construct a
  correct, candidate-facing apply URL.

Path to enable (future): add a per-tenant registry
  {slug: (host, site_number)}  # verified live
mirroring WORKDAY_TENANTS / EIGHTFOLD_TENANTS, populated via Source Discovery
against a real employer's ORC careers page, then map
  requisition -> https://{host}/.../job/{reqId}  (the employer's own ORC page).

The previous implementation posted to a generic jobs.oracle.com endpoint that
is not tenant-scoped and guessed response keys; it is intentionally disabled.
"""
from typing import List, Dict, Optional
from .base import BaseATSScraper

# Flip to True only once a verified per-tenant registry + real parse exist.
SUPPORTED = False

# slug -> (host, site_number). Populate with VERIFIED-LIVE entries only.
ORACLE_TENANTS: Dict[str, tuple] = {}


class OracleScraper(BaseATSScraper):
    """Oracle Cloud HCM connector (currently unsupported — see module docstring)."""

    def get_platform_name(self) -> str:
        return 'oracle'

    def fetch_jobs(self) -> List[Dict]:
        if not SUPPORTED or self.company_slug.lower() not in ORACLE_TENANTS:
            print(f"Oracle: DISCOVERY_UNSUPPORTED for '{self.company_slug}' — "
                  f"per-tenant ORC host/site required (see oracle.py docstring)")
            return []
        # Reserved for the real per-tenant implementation once registry exists.
        return []


def fetch_oracle_jobs(company_slug: str, api_key: Optional[str] = None) -> List[Dict]:
    """Convenience function (returns [] while Oracle is unsupported)."""
    return OracleScraper(company_slug).fetch_jobs()
