"""Company Resolution Service (§11).

ONE canonical place that answers "which Company record is this?" for every
caller that currently has to turn a connector's company fields (ATS platform
+ tenant slug + optional domain/name) into a `Company` row. This is the
foundation the user's roadmap calls out as a prerequisite for:
  - Company Claim (an employer later proves ownership of a company we
    discovered via scraping, and the discovery's history must attach to the
    one Company that gets claimed - no duplicate/orphaned records)
  - Company Discovery (deriving canonical companies from scraped jobs before
    any employer has signed up)
  - Employer-posted jobs sharing the same canonical Company graph as scraped
    jobs (so Search/Matching/Talent Pool never have to special-case source)

WHY THIS EXISTS (the gap it closes)
------------------------------------
Before this module, there were TWO different, DIVERGING company-resolution
implementations in the codebase:

  1. `apps/scraper/tasks.py::process_and_store_jobs` (the function that
     ACTUALLY runs on the production Celery Beat schedule) did:
         company_name = job_data.get('company_slug', source.name)
         Company.objects.get_or_create(slug=company_name.lower()...,
                                        defaults={'name': company_name})
     This stores the RAW BOARD SLUG as the company's `name` (e.g. a company
     literally named "stripe" instead of "Stripe") - a real, live bug on the
     authoritative path.

  2. `apps/scraper/orchestrator.py::_process_jobs` (a secondary/manual path,
     NOT Beat-scheduled) already fixed this specific symptom locally by
     reading `NormalizedJob.company_name` and stripping ATS suffixes from the
     slug key - but duplicated the entire get_or_create+backfill logic
     inline, with no persisted identity table, so each ATS migration (e.g.
     Notion/Plaid/Ramp moving Lever -> Ashby - see source_discovery.py) still
     risks creating a SECOND Company row rather than recognizing the same
     employer under a new tenant slug, unless the stripped slug happens to
     match exactly.

This module unifies both into ONE resolver with a persisted, auditable
identity table (`CompanyResolutionIdentity`) so:
  - Both callers (tasks.py AND orchestrator.py) get the SAME real company
    name, not a slug.
  - A (platform, tenant_slug) pair is only ever resolved once; subsequent
    calls are a direct, explainable lookup instead of a fresh heuristic.
  - Resolution evidence (how the Company was matched: by domain, by slug, or
    newly created) is recorded for future Company Claim verification instead
    of being thrown away.

Resolution order (cheapest/strongest signal first, confidence-scored):
  1. Known tenant identity: an exact (platform, tenant_slug) hit in
     CompanyResolutionIdentity -> direct lookup, confidence 1.0.
  2. Domain match: if the connector gave a company_domain and an existing
     Company already has that non-blank `domain`, reuse it (one real
     employer should never get two Company rows just because it migrated
     ATS) - confidence 0.9.
  3. Slug match: fall back to the existing ATS-suffix-stripped slug heuristic
     (ported verbatim from orchestrator.py, now in ONE place) - confidence
     0.6 (a slug collision is weaker evidence than a domain match).
  4. Create: no match found -> create a new canonical Company with the REAL
     resolved name (never a raw slug) - confidence 1.0 ("new" is certain,
     just not yet corroborated by multiple signals).

This module has Django model imports (Company, CompanyResolutionIdentity,
Source) but no Celery/view imports, so it can be unit-tested with normal
Django test-DB fixtures and imported from both tasks.py and orchestrator.py
without a circular-import risk.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from apps.jobs.models import Company, CompanyResolutionIdentity

# Kept in sync with the equivalent suffix list in orchestrator.py / tasks.py'
# _dispatch_structured_ats companion data and strategy_router.STRUCTURED_ATS.
# A trailing "-{platform}" on a board slug is NOT part of the employer's
# identity (e.g. "airbnb-greenhouse" and a future "airbnb-lever" are the same
# employer), so it is always stripped before using a slug as a dedup key.
_ATS_SLUG_SUFFIXES = (
    "-greenhouse", "-lever", "-ashby", "-workday", "-smartrecruiters",
    "-icims", "-workable", "-teamtailor", "-bamboohr", "-oracle", "-sap",
    "-recruitee", "-personio", "-eightfold", "-jobvite",
)


@dataclass
class ResolutionResult:
    company: Company
    created: bool
    matched_by: str          # "identity" | "domain" | "slug" | "created"
    confidence: float
    evidence: dict


def _strip_ats_suffix(slug: str) -> str:
    s = (slug or "").lower().strip()
    for suffix in _ATS_SLUG_SUFFIXES:
        if s.endswith(suffix):
            return s[: -len(suffix)]
    return s


def _humanize(slug: str) -> str:
    s = (slug or "").replace("-", " ").replace("_", " ").strip()
    return s.title() if s else slug


class CompanyResolutionService:
    """Resolves (platform, tenant_slug, name, domain) -> ONE canonical Company.

    Usage (replaces the inline get_or_create blocks in tasks.py and
    orchestrator.py):

        resolver = CompanyResolutionService()
        result = resolver.resolve(
            platform="greenhouse", tenant_slug="stripe",
            company_name="Stripe", company_domain="stripe.com",
            source=source,
        )
        job.company = result.company
    """

    def resolve(
        self,
        *,
        platform: str = "",
        tenant_slug: str = "",
        company_name: str = "",
        company_domain: str = "",
        fallback_name: str = "",
        source=None,
    ) -> ResolutionResult:
        platform = (platform or "").lower().strip()
        tenant_slug = (tenant_slug or "").strip()
        company_domain = (company_domain or "").lower().strip().removeprefix("www.")
        resolved_name = (company_name or "").strip()

        # ---- Step 1: known tenant identity (strongest, cheapest) ----
        if platform and tenant_slug:
            identity = (
                CompanyResolutionIdentity.objects
                .select_related("company")
                .filter(platform=platform, tenant_slug=tenant_slug)
                .first()
            )
            if identity:
                company = identity.company
                # Backfill a real name if the company still only has a
                # slug-shaped placeholder name (closes the tasks.py bug for
                # companies resolved before this service existed).
                self._backfill_name_if_placeholder(company, resolved_name)
                return ResolutionResult(
                    company=company, created=False, matched_by="identity",
                    confidence=1.0,
                    evidence={"platform": platform, "tenant_slug": tenant_slug},
                )

        # ---- Step 2: domain match (strong - same real employer, new tenant) ----
        company = None
        matched_by = ""
        confidence = 0.0
        evidence: dict = {}

        if company_domain:
            company = Company.objects.filter(domain=company_domain).first()
            if company:
                matched_by, confidence = "domain", 0.9
                evidence = {"domain": company_domain}

        # ---- Step 3: slug match (weaker - fall back to the historical
        #      ATS-suffix-stripped slug heuristic, now defined in ONE place) ----
        slug_key = ""
        if company is None:
            slug_key = _strip_ats_suffix(tenant_slug or resolved_name or fallback_name)
            if slug_key:
                company = Company.objects.filter(slug=slug_key).first()
                if company:
                    matched_by, confidence = "slug", 0.6
                    evidence = {"slug": slug_key}
                    self._backfill_name_if_placeholder(company, resolved_name)

        # ---- Step 4: create ----
        created = False
        if company is None:
            if not slug_key:
                slug_key = _strip_ats_suffix(tenant_slug or resolved_name or fallback_name)
            final_name = resolved_name or _humanize(slug_key) or fallback_name or slug_key or "Unknown"
            # Company.slug is globally unique; guard against a rare collision
            # (e.g. two different real employers whose stripped slugs happen
            # to match) by suffixing rather than silently reusing someone
            # else's Company row.
            candidate_slug = slug_key or _humanize(final_name).lower().replace(" ", "-")
            unique_slug = candidate_slug
            n = 2
            while Company.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{candidate_slug}-{n}"
                n += 1
            company = Company.objects.create(
                slug=unique_slug, name=final_name,
                domain=company_domain or "",
            )
            created = True
            matched_by, confidence = "created", 1.0
            evidence = {"slug": unique_slug, "name": final_name}

        # ---- Persist the (platform, tenant_slug) identity for next time ----
        if platform and tenant_slug:
            CompanyResolutionIdentity.objects.update_or_create(
                platform=platform, tenant_slug=tenant_slug,
                defaults={
                    "company": company,
                    "domain": company_domain,
                    "source": source,
                    "confidence": confidence,
                    "matched_by": matched_by,
                    "evidence": evidence,
                },
            )

        return ResolutionResult(
            company=company, created=created, matched_by=matched_by,
            confidence=confidence, evidence=evidence,
        )

    @staticmethod
    def _backfill_name_if_placeholder(company: Company, resolved_name: str) -> None:
        """If the Company's name is just its own slug with dashes->spaces
        (the historical tasks.py bug signature), and we now have a real
        resolved name, fix it. Never overwrite a name that isn't slug-shaped
        - that would risk clobbering a real admin-edited name.
        """
        if not resolved_name:
            return
        placeholder_shape = company.name.lower().replace(" ", "-") == company.slug
        if placeholder_shape and company.name != resolved_name:
            company.name = resolved_name
            company.save(update_fields=["name"])


# Module-level singleton mirroring the pattern used by
# apps/scraper/orchestrator.py's `orchestrator` global instance - callers can
# `from apps.jobs.company_resolution import company_resolver` without having
# to construct one, since this service is stateless (no per-run caching).
company_resolver = CompanyResolutionService()
