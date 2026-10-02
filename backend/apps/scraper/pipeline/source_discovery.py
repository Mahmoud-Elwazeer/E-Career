"""ATS Source Discovery + fingerprinting (§8/§9/§10).

Turns a company identifier (slug / domain / careers URL) into a concrete,
health-checked ATS source: which provider hosts their jobs and under what
tenant/slug. This is how we stop static seed lists from silently rotting — the
same probe that found Notion/Plaid/Ramp had migrated Lever -> Ashby, made
repeatable.

Design constraints:
- Deterministic HTTP first (no browser, no AI) — cheap, explainable, reliable.
- Every result carries EVIDENCE (which endpoint answered, http status, job
  count) so a migration decision is auditable, never a black box.
- No Django imports here so it is unit-testable standalone; the management
  command / service layer wires it to Source rows.

The network call is injected (`fetcher`) so tests run offline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


# Public ATS endpoint templates keyed by provider. `{slug}` is the tenant.
# Each returns machine-structured JSON we already know how to parse, EXCEPT
# where noted. Ordered by how commonly we see them so the first hit wins.
ATS_ENDPOINTS: Dict[str, str] = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{slug}/postings",
    "workable": "https://apply.workable.com/api/v3/accounts/{slug}/jobs",
    "recruitee": "https://{slug}.recruitee.com/api/offers/",
    "personio": "https://{slug}.jobs.personio.de/search.json",
    "breezy": "https://{slug}.breezy.hr/json",
    "bamboohr": "https://{slug}.bamboohr.com/careers/list",
}

# How to read a "job count" out of each provider's payload shape so a 200 with
# an empty board is not mistaken for a healthy source.
def _count_jobs(provider: str, payload) -> Optional[int]:
    try:
        if provider == "greenhouse":
            return len(payload.get("jobs", []))
        if provider == "lever":
            return len(payload) if isinstance(payload, list) else None
        if provider == "ashby":
            return len(payload.get("jobs", []))
        if provider == "smartrecruiters":
            return payload.get("totalFound", len(payload.get("content", [])))
        if provider == "workable":
            return len(payload.get("results", payload.get("jobs", [])))
        if provider == "recruitee":
            return len(payload.get("offers", []))
        if provider == "personio":
            return len(payload) if isinstance(payload, list) else None
        if provider == "breezy":
            return len(payload) if isinstance(payload, list) else None
        if provider == "bamboohr":
            return len(payload.get("result", []))
    except (AttributeError, TypeError):
        return None
    return None


@dataclass
class DiscoveryResult:
    slug: str
    provider: Optional[str] = None            # winning provider, or None
    tenant: Optional[str] = None
    endpoint: Optional[str] = None
    job_count: int = 0
    healthy: bool = False                      # provider found AND job_count > 0
    evidence: List[Dict] = field(default_factory=list)  # every probe attempt

    def to_dict(self) -> Dict:
        return {
            "slug": self.slug, "provider": self.provider, "tenant": self.tenant,
            "endpoint": self.endpoint, "job_count": self.job_count,
            "healthy": self.healthy, "evidence": self.evidence,
        }


# A fetcher returns (status_code, json_or_none). Injected so tests are offline.
Fetcher = Callable[[str], Tuple[int, object]]


def discover_ats(
    slug: str,
    *,
    fetcher: Fetcher,
    candidates: Optional[List[str]] = None,
) -> DiscoveryResult:
    """Probe candidate ATS providers for `slug` and return the first healthy hit.

    `candidates` restricts/orders which providers to try (default: all). The
    result always records evidence for every probe so a MIGRATED/INVALID
    decision downstream can cite exactly what was seen.
    """
    result = DiscoveryResult(slug=slug)
    providers = candidates or list(ATS_ENDPOINTS.keys())

    for provider in providers:
        template = ATS_ENDPOINTS.get(provider)
        if not template:
            continue
        url = template.format(slug=slug)
        try:
            status, payload = fetcher(url)
        except Exception as e:  # noqa: BLE001
            result.evidence.append({"provider": provider, "url": url,
                                     "error": type(e).__name__})
            continue

        count = _count_jobs(provider, payload) if status == 200 else None
        result.evidence.append({
            "provider": provider, "url": url, "status": status,
            "job_count": count,
        })

        if status == 200 and count and count > 0:
            result.provider = provider
            result.tenant = slug
            result.endpoint = url
            result.job_count = count
            result.healthy = True
            return result  # first healthy provider wins

    return result


def compare_for_migration(
    old_provider: str,
    discovery: DiscoveryResult,
) -> Dict:
    """Decide the lifecycle verdict for a failing source given a fresh probe.

    Returns {verdict, reason, ...} where verdict is one of:
      MIGRATED  — found a DIFFERENT healthy provider (employer moved ATS)
      ACTIVE    — same provider is still healthy (false alarm)
      INVALID   — no healthy provider found anywhere
    """
    if discovery.healthy and discovery.provider and discovery.provider != old_provider:
        return {
            "verdict": "MIGRATED",
            "reason": f"{old_provider} -> {discovery.provider}",
            "new_provider": discovery.provider,
            "new_tenant": discovery.tenant,
            "new_endpoint": discovery.endpoint,
            "job_count": discovery.job_count,
            "evidence": discovery.evidence,
        }
    if discovery.healthy and discovery.provider == old_provider:
        return {"verdict": "ACTIVE", "reason": "same provider still healthy",
                "evidence": discovery.evidence}
    return {"verdict": "INVALID",
            "reason": "no healthy ATS provider found on any known endpoint",
            "evidence": discovery.evidence}
