"""Authoritative normalized job contract (§5) + ingestion lifecycle states (§7).

WHY THIS EXISTS
---------------
Every ATS connector historically emitted its own ad-hoc dict. The base
connector (`apps/scraper/ats/base.py`) only ever set `company_slug` (= the
source board slug), never a real employer name, and downstream engines had to
guess connector-specific keys. That is exactly the "downstream engines guess
connector keys" failure this contract removes.

`NormalizedJob` is the SINGLE typed structure every connector maps into BEFORE
quality / legitimacy / dedup / matching / search. Connectors keep emitting
their current dicts; `NormalizedJob.from_connector_dict()` adapts any of them
(company / company_name / company_slug / company_id, apply_url /
direct_apply_url) into one shape, so the mapping lives in ONE place.

This module has NO Django imports so it can be unit-tested standalone and
imported from management commands, Celery tasks, and tests alike.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# §7 Ingestion lifecycle states
# ---------------------------------------------------------------------------
# These describe where a DISCOVERY is in the pipeline. They are intentionally
# distinct from Job.quality_state (which is a PERSISTED job's health). A record
# can be NORMALIZED-but-not-yet-persisted; that is different from a persisted
# job that is `needs_verification`. Keeping the two vocabularies separate is
# what prevents "not publishable yet" from being confused with "throw away".
class IngestionState:
    DISCOVERED = "DISCOVERED"
    NORMALIZING = "NORMALIZING"
    NEEDS_ENRICHMENT = "NEEDS_ENRICHMENT"
    NORMALIZED = "NORMALIZED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    PUBLISHABLE = "PUBLISHABLE"
    PUBLISHED = "PUBLISHED"

    # Failure / terminal states — a record here is NOT silently dropped; the
    # reason is recorded so run metrics can explain the funnel.
    NORMALIZATION_FAILED = "NORMALIZATION_FAILED"
    DIRECT_APPLY_FAILED = "DIRECT_APPLY_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    DUPLICATE = "DUPLICATE"

    TERMINAL_FAILURES = frozenset({
        NORMALIZATION_FAILED, DIRECT_APPLY_FAILED, VERIFICATION_FAILED,
        INVALID, EXPIRED, DUPLICATE,
    })

    # Maps a PUBLISHED ingestion outcome onto the persisted Job.quality_state
    # vocabulary so the two systems stay consistent.
    TO_QUALITY_STATE = {
        VERIFIED: "direct_verified",
        PUBLISHABLE: "probably_active",
        PUBLISHED: "active",
        EXPIRED: "expired",
        DUPLICATE: "duplicate",
        INVALID: "rejected",
        DIRECT_APPLY_FAILED: "rejected",
        VERIFICATION_FAILED: "needs_verification",
    }


# Fields whose provenance we track individually (value/source/method/confidence).
PROVENANCE_FIELDS = (
    "title", "company_name", "location", "employment_type", "seniority",
    "salary_min", "salary_max", "salary_currency", "direct_apply_url",
    "canonical_job_url", "ats_provider", "ats_job_id", "published_at",
)


@dataclass
class NormalizedJob:
    """The one job shape all connectors converge on (§5).

    Only `title` and a usable apply URL are strictly required to be non-empty
    for a record to be a candidate; everything else may be enriched later. Use
    `validate()` to get the list of contract violations rather than raising, so
    the pipeline can record a reason instead of crashing a whole run.
    """

    # --- source / provenance identity ---
    source_id: str = ""
    source_type: str = "scraper"          # scraper | api | manual
    source_job_id: str = ""               # id as given by the source board
    ats_provider: str = ""                # greenhouse | lever | ashby | ...
    ats_job_id: str = ""                  # provider's stable job/requisition id

    # --- core content ---
    title: str = ""
    normalized_title: str = ""
    company_name: str = ""                # REAL employer display name
    company_slug: str = ""                # board/source slug (NOT the name)
    company_domain: str = ""
    company_id: str = ""                  # external/canonical company id if known

    location_raw: str = ""
    country: str = ""
    region: str = ""
    city: str = ""
    remote_type: str = ""                 # remote | hybrid | onsite

    employment_type: Optional[str] = None
    seniority: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "USD"
    salary_period: str = ""               # year | month | hour

    description: str = ""
    requirements: str = ""
    responsibilities: str = ""
    benefits: str = ""
    skills: List[str] = field(default_factory=list)

    # --- urls ---
    source_url: str = ""                  # where we discovered it
    canonical_job_url: str = ""           # the job's own canonical page
    direct_apply_url: str = ""            # employer/ATS apply link (moat gate)

    # --- dates ---
    published_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None

    # --- raw + provenance ---
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    field_provenance: Dict[str, Any] = field(default_factory=dict)

    # --- pipeline bookkeeping (not persisted directly) ---
    ingestion_state: str = IngestionState.DISCOVERED

    # ------------------------------------------------------------------
    @classmethod
    def from_connector_dict(cls, d: Dict[str, Any], *, source=None) -> "NormalizedJob":
        """Adapt ANY connector output dict into the contract.

        Tolerates every company-key variant a connector might use
        (company / company_name / company_slug / company_id) and both apply-url
        keys (direct_apply_url / apply_url). This is the ONE place that
        knowledge lives, so downstream code never guesses connector keys.
        """
        get = d.get

        # Company name resolution order: an explicit real name wins; the board
        # slug is the LAST resort and is title-cased so we never surface a raw
        # "airbnb-greenhouse"-style slug as an employer name.
        company_name = (
            get("company_name")
            or get("company")
            or (getattr(source, "name", "") if source else "")
            or ""
        )
        company_slug = get("company_slug") or (getattr(source, "slug", "") if source else "")
        if not company_name and company_slug:
            company_name = _humanize_slug(company_slug)

        apply_url = get("direct_apply_url") or get("apply_url") or ""

        nj = cls(
            source_id=str(getattr(source, "id", "") or get("source_id", "")),
            source_type=(getattr(source, "type", "") if source else "") or get("source_type", "scraper"),
            source_job_id=str(get("source_job_id") or get("id") or ""),
            ats_provider=get("ats_platform") or get("ats_provider") or "",
            ats_job_id=str(get("ats_job_id") or get("id") or ""),
            title=(get("title") or "").strip(),
            company_name=company_name.strip(),
            company_slug=company_slug,
            company_domain=get("company_domain", ""),
            company_id=str(get("company_id") or ""),
            location_raw=get("location") or get("location_raw") or "",
            remote_type=get("remote_type") or "",
            employment_type=get("employment_type"),
            seniority=get("seniority") or get("experience_level"),
            salary_min=get("salary_min"),
            salary_max=get("salary_max"),
            currency=get("salary_currency") or get("currency") or "USD",
            description=get("description") or "",
            requirements=get("requirements") or "",
            responsibilities=get("responsibilities") or "",
            benefits=get("benefits") or "",
            skills=list(get("skills") or []),
            source_url=get("source_url") or get("canonical_job_url") or apply_url or "",
            canonical_job_url=get("canonical_job_url") or apply_url or "",
            direct_apply_url=apply_url,
            published_at=get("posted_at") or get("published_at"),
            updated_at=get("updated_at"),
            raw_payload=get("raw_data") or d,
        )
        return nj

    # ------------------------------------------------------------------
    def validate(self) -> List[str]:
        """Return a list of contract violations (empty == valid candidate)."""
        problems: List[str] = []
        if not self.title:
            problems.append("missing_title")
        if not self.direct_apply_url:
            problems.append("missing_direct_apply_url")
        if not self.company_name:
            problems.append("missing_company_name")
        return problems

    @property
    def is_valid(self) -> bool:
        return not self.validate()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _humanize_slug(slug: str) -> str:
    """Turn a board slug like 'airbnb-greenhouse' or 'modern_health' into a
    presentable employer name ('Airbnb', 'Modern Health').

    Strips a trailing known-ATS suffix so the manufactured name is the company,
    not the board id.
    """
    s = (slug or "").strip()
    for suffix in ("-greenhouse", "-lever", "-ashby", "-workday", "-smartrecruiters",
                   "-icims", "-workable", "-teamtailor", "-bamboohr", "-oracle", "-sap"):
        if s.lower().endswith(suffix):
            s = s[: -len(suffix)]
            break
    s = s.replace("-", " ").replace("_", " ").strip()
    return s.title() if s else slug
