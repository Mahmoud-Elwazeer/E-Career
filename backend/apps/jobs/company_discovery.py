"""Company Discovery Engine (Task #13).

Enriches canonical Company rows (domain, careers page URL, industry,
headquarters) using evidence this platform has ALREADY ingested — it does
NOT scrape new external sources. Every signal comes from data that already
exists in this database:

  domain              <- CompanyResolutionIdentity.domain (recorded when a
                          scraper connector observed a company_domain while
                          resolving an ATS tenant to this Company — see
                          apps/jobs/company_resolution.py).
  careers_page_url     <- the ATS board URL pattern for a known
                          (CompanyResolutionIdentity.platform, tenant_slug)
                          pair, using the SAME URL templates
                          setup_sources.py's _board_url() already uses to
                          seed Source.url — not a new pattern invented here.
  industry             <- majority vote across this Company's Source rows'
                          admin-set `industry` metadata field (Source.industry,
                          added in the §4 Source registry audit), when at
                          least one Source has a non-blank value.
  headquarters         <- majority vote across this Company's Job.location
                          values. Explicitly the WEAKEST signal here (a
                          company's most common job-posting location is a
                          proxy for HQ, not a proof of it) — confidence is
                          capped accordingly and this is the one field type
                          most likely to need admin correction.

Design mirrors CompanyResolutionService: additive-only (never overwrites a
non-blank field), every decision recorded as a CompanyEnrichment row whether
applied or not, confidence-scored, no network calls, pure DB read + write.
This is intentionally NOT a web crawler — "Company Discovery" here means
discovering structure already latent in data this platform acquired through
its existing, moat-compliant scraping pipeline, consistent with the
Master Resource Directive's instruction to prefer official/structured
signals over speculative external scraping.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List

from apps.jobs.models import Company, CompanyEnrichment, CompanyResolutionIdentity, Job


# Mirrors setup_sources.py::_board_url() for the platforms that have a
# well-known, slug-derivable public careers URL. Kept as a small local
# mapping (not an import) because that function builds URLs for SEEDING a
# new Source (different purpose/shape); duplicating the few patterns we can
# derive a careers page from is clearer than coupling two unrelated
# commands. Platforms without a simple {slug}-derivable public page
# (workday/eightfold/jobvite/oracle/sap - all per-tenant resolved) are
# deliberately omitted, same reasoning as source_discovery.py's documented
# ATS_ENDPOINTS omissions.
_CAREERS_URL_TEMPLATES = {
    "greenhouse": "https://boards.greenhouse.io/{slug}",
    "lever": "https://jobs.lever.co/{slug}",
    "ashby": "https://jobs.ashbyhq.com/{slug}",
    "recruitee": "https://{slug}.recruitee.com/",
    "personio": "https://{slug}.jobs.personio.de/",
    "breezy": "https://{slug}.breezy.hr/",
    "bamboohr": "https://{slug}.bamboohr.com/careers",
}


@dataclass
class EnrichmentOutcome:
    field_name: str
    value: str
    method: str
    confidence: float
    applied: bool
    conflict: bool
    evidence: dict


class CompanyDiscoveryService:
    """Stateless — safe as a module-level singleton, same pattern as
    company_resolver and company_claim_service."""

    def discover(self, company: Company) -> List[EnrichmentOutcome]:
        outcomes: List[EnrichmentOutcome] = []
        outcomes.extend(self._discover_domain(company))
        outcomes.extend(self._discover_careers_page_url(company))
        outcomes.extend(self._discover_industry(company))
        outcomes.extend(self._discover_headquarters(company))

        for o in outcomes:
            CompanyEnrichment.objects.create(
                company=company, field_name=o.field_name, value=o.value,
                method=o.method, confidence=o.confidence,
                evidence=o.evidence, applied=o.applied, conflict=o.conflict,
            )

        changed_fields = [o.field_name for o in outcomes if o.applied]
        if changed_fields:
            field_map = {
                "domain": "domain", "careers_page_url": "careers_page_url",
                "industry": "industry", "headquarters": "headquarters",
            }
            update_fields = []
            for o in outcomes:
                if o.applied:
                    setattr(company, field_map[o.field_name], o.value)
                    update_fields.append(field_map[o.field_name])
            company.save(update_fields=update_fields)

        return outcomes

    def _discover_domain(self, company: Company) -> List[EnrichmentOutcome]:
        identity = (
            CompanyResolutionIdentity.objects
            .filter(company=company)
            .exclude(domain="")
            .order_by("-confidence", "-created_at")
            .first()
        )
        if not identity:
            return []
        return [self._outcome_for_field(
            company, field_name="domain", value=identity.domain,
            method="resolution_identity_domain", confidence=0.9,
            evidence={"platform": identity.platform, "tenant_slug": identity.tenant_slug},
        )]

    def _discover_careers_page_url(self, company: Company) -> List[EnrichmentOutcome]:
        identity = (
            CompanyResolutionIdentity.objects
            .filter(company=company, platform__in=_CAREERS_URL_TEMPLATES.keys())
            .order_by("-confidence", "-created_at")
            .first()
        )
        if not identity:
            return []
        url = _CAREERS_URL_TEMPLATES[identity.platform].format(slug=identity.tenant_slug)
        return [self._outcome_for_field(
            company, field_name="careers_page_url", value=url,
            method="ats_board_url_pattern", confidence=0.85,
            evidence={"platform": identity.platform, "tenant_slug": identity.tenant_slug},
        )]

    def _discover_industry(self, company: Company) -> List[EnrichmentOutcome]:
        source_industries = list(
            Job.objects.filter(company=company, source__isnull=False)
            .exclude(source__industry="")
            .values_list("source__industry", flat=True)
        )
        if not source_industries:
            return []
        value, count = Counter(source_industries).most_common(1)[0]
        confidence = min(0.5 + 0.1 * count, 0.9)
        return [self._outcome_for_field(
            company, field_name="industry", value=value,
            method="source_industry_backfill", confidence=confidence,
            evidence={"vote_count": count, "total_sources_considered": len(source_industries)},
        )]

    def _discover_headquarters(self, company: Company) -> List[EnrichmentOutcome]:
        """Weakest signal in this service by design - a job-posting-location
        majority is a proxy for HQ, not proof. Capped confidence (<=0.5)
        reflects that; this field is the one most likely to need an admin
        correction, and callers should treat it accordingly."""
        locations = list(
            Job.objects.filter(company=company)
            .exclude(location="")
            .values_list("location", flat=True)
        )
        if len(locations) < 3:
            # Too few data points for a majority vote to mean anything -
            # explicitly decline rather than confidently guessing from n=1.
            return []
        value, count = Counter(locations).most_common(1)[0]
        total = len(locations)
        if count / total < 0.5:
            # No real majority (most common location is still a minority of
            # postings) - evidence too weak to even log as a weak signal.
            return []
        confidence = min(0.3 + 0.2 * (count / total), 0.5)
        return [self._outcome_for_field(
            company, field_name="headquarters", value=value,
            method="job_location_majority", confidence=confidence,
            evidence={"vote_count": count, "total_jobs_considered": total},
        )]

    @staticmethod
    def _outcome_for_field(company: Company, *, field_name: str, value: str,
                            method: str, confidence: float, evidence: dict) -> EnrichmentOutcome:
        model_field = {
            "domain": "domain", "careers_page_url": "careers_page_url",
            "industry": "industry", "headquarters": "headquarters",
        }[field_name]
        current = getattr(company, model_field) or ""
        # Company.industry has a non-blank DEFAULT ("other"), unlike every
        # other field here which defaults to "". Treat that default as the
        # "unset" sentinel for enrichment purposes only - a Company whose
        # industry was never actually set by anyone is not meaningfully
        # different from one with a blank industry, and should still be
        # enrichable. An admin who explicitly chose "other" after reviewing
        # the company is a real (if rare) edge case this cannot distinguish
        # from "never touched" - documented limitation, not silently ignored.
        if field_name == "industry" and current == "other":
            current = ""

        if not current:
            return EnrichmentOutcome(
                field_name=field_name, value=value, method=method,
                confidence=confidence, applied=True, conflict=False, evidence=evidence,
            )
        if current.strip().lower() != value.strip().lower():
            return EnrichmentOutcome(
                field_name=field_name, value=value, method=method,
                confidence=confidence, applied=False, conflict=True,
                evidence={**evidence, "existing_value": current},
            )
        # Values agree - nothing to apply, not a conflict either.
        return EnrichmentOutcome(
            field_name=field_name, value=value, method=method,
            confidence=confidence, applied=False, conflict=False,
            evidence={**evidence, "existing_value_matches": True},
        )


company_discovery_service = CompanyDiscoveryService()
