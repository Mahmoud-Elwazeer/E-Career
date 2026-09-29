"""SAP SuccessFactors connector — DISCOVERY_UNSUPPORTED (§11/§13/§14).

STATUS: not enabled. Marked unsupported WITH EVIDENCE rather than shipping a
guessing connector that could surface non-direct-apply URLs and weaken the moat.

Why it is hard to do reliably right now:
- SuccessFactors Recruiting exposes jobs via the OData API, e.g.
    https://{host}/odata/v2/JobRequisitionPosting?$format=json&...
  or the Career Site Builder (CSB) search endpoints. Both are per-tenant: the
  {host} (e.g. career{N}.successfactors.{eu|com}), the company career-site id,
  and often an API key / OAuth are required. None are derivable from a bare
  company slug.
- The candidate-facing apply page is
    https://{careersite-host}/careers/job/{postingId}
  which again depends on the tenant's Career Site Builder host.

Path to enable (future): add a per-tenant registry
  {slug: (odata_host, careersite_host, company_id)}  # verified live
mirroring WORKDAY_TENANTS, populated via Source Discovery against a real
employer's SuccessFactors career site, mapping each posting to the employer's
own CSB apply page.

The previous implementation hit a generic jobs.sap.com/search endpoint that is
not tenant-scoped and guessed response keys; it is intentionally disabled.
"""
from typing import List, Dict, Optional
from .base import BaseATSScraper

# Flip to True only once a verified per-tenant registry + real parse exist.
SUPPORTED = False

# slug -> (odata_host, careersite_host, company_id). VERIFIED-LIVE entries only.
SAP_TENANTS: Dict[str, tuple] = {}


class SAPScraper(BaseATSScraper):
    """SAP SuccessFactors connector (currently unsupported — see module docstring)."""

    def get_platform_name(self) -> str:
        return 'sap'

    def fetch_jobs(self) -> List[Dict]:
        if not SUPPORTED or self.company_slug.lower() not in SAP_TENANTS:
            print(f"SAP: DISCOVERY_UNSUPPORTED for '{self.company_slug}' — "
                  f"per-tenant OData/CSB host required (see sap.py docstring)")
            return []
        return []


def fetch_sap_jobs(company_slug: str, api_key: Optional[str] = None) -> List[Dict]:
    """Convenience function (returns [] while SAP is unsupported)."""
    return SAPScraper(company_slug).fetch_jobs()
