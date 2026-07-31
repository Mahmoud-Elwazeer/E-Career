from __future__ import annotations

import time
import structlog
from django.conf import settings
from django.utils import timezone

from .models import VerificationResult
from .stages import (
    ATSFingerprintStage,
    RedirectResolverStage,
    DomainVerifierStage,
    LegitimacyScorerStage,
    FreshnessCheckerStage,
    DeduplicatorStage,
)

logger = structlog.get_logger()

TRUST_SCORE_WEIGHTS = {
    "ats_confidence": 0.30,
    "domain_trust": 0.25,
    "legitimacy": 0.25,
    "freshness": 0.10,
    "accessibility": 0.10,
}


class VerificationEngine:
    """
    6-stage Direct Apply Verification Engine.

    Every job MUST pass through this before being shown to users.
    Jobs from blocked aggregator domains are ALWAYS rejected.
    """

    def __init__(self):
        self.ats_stage = ATSFingerprintStage()
        self.redirect_stage = RedirectResolverStage()
        self.domain_stage = DomainVerifierStage()
        self.legitimacy_stage = LegitimacyScorerStage()
        self.freshness_stage = FreshnessCheckerStage()
        self.dedup_stage = DeduplicatorStage()

    def verify_job(self, job) -> VerificationResult:
        """Run full 6-stage verification on a job instance."""
        start_time = time.time()
        apply_url = job.direct_apply_url or job.source_url

        # Stage 1: ATS Fingerprinting
        ats_result = self.ats_stage.run(apply_url)

        if ats_result.platform == "BLOCKED_AGGREGATOR":
            return self._create_result(
                job=job,
                status="rejected",
                trust_score=0.0,
                ats_platform_detected=ats_result.platform,
                ats_confidence=1.0,
                notes=f"BLOCKED: URL is from aggregator domain ({ats_result.pattern_matched})",
                duration_ms=self._elapsed_ms(start_time),
            )

        # Stage 2: Redirect Resolution
        redirect_result = self.redirect_stage.run(apply_url)
        final_url = redirect_result.final_url or apply_url

        if redirect_result.final_url:
            ats_recheck = self.ats_stage.run(redirect_result.final_url)
            if ats_recheck.platform == "BLOCKED_AGGREGATOR":
                return self._create_result(
                    job=job,
                    status="rejected",
                    trust_score=0.0,
                    ats_platform_detected="BLOCKED_AGGREGATOR",
                    ats_confidence=1.0,
                    final_url=redirect_result.final_url,
                    redirect_chain=redirect_result.chain,
                    redirect_count=redirect_result.redirect_count,
                    notes="BLOCKED: Redirect lands on aggregator domain",
                    duration_ms=self._elapsed_ms(start_time),
                )
            if ats_recheck.confidence > ats_result.confidence:
                ats_result = ats_recheck

        # Stage 3: Domain Verification
        company_domain = ""
        careers_page = ""
        if job.company:
            company_domain = job.company.domain or ""
            careers_page = job.company.careers_page_url or ""

        domain_result = self.domain_stage.run(final_url, company_domain, careers_page)

        # Stage 4: Legitimacy Scoring
        legitimacy_result = self.legitimacy_stage.run(
            description=job.description or "",
            apply_url=final_url,
            salary_min=job.salary_min,
        )

        # Stage 5: Freshness (only if URL not already checked in Stage 4)
        freshness_result = self.freshness_stage.run(final_url)

        # Stage 6: Deduplication
        dedup_result = self.dedup_stage.run(
            company_name=job.company.name if job.company else "",
            title=job.title or "",
            location=job.location or "",
        )

        # Calculate Trust Score
        freshness_score = 1.0 if freshness_result.is_accessible and not freshness_result.is_closed else 0.0
        accessibility_score = 1.0 if legitimacy_result.url_accessible else 0.0

        trust_score = (
            TRUST_SCORE_WEIGHTS["ats_confidence"] * ats_result.confidence
            + TRUST_SCORE_WEIGHTS["domain_trust"] * domain_result.domain_trust
            + TRUST_SCORE_WEIGHTS["legitimacy"] * legitimacy_result.score
            + TRUST_SCORE_WEIGHTS["freshness"] * freshness_score
            + TRUST_SCORE_WEIGHTS["accessibility"] * accessibility_score
        )

        trust_score = round(min(1.0, max(0.0, trust_score)), 3)

        threshold = getattr(settings, "SEARCH_TRUST_SCORE_THRESHOLD", 0.4)
        if dedup_result.is_duplicate:
            status = "rejected"
        elif trust_score >= threshold:
            status = "verified"
        else:
            status = "rejected"

        result = self._create_result(
            job=job,
            status=status,
            trust_score=trust_score,
            ats_platform_detected=ats_result.platform,
            ats_confidence=ats_result.confidence,
            final_url=final_url,
            redirect_chain=redirect_result.chain,
            redirect_count=redirect_result.redirect_count,
            domain_trust=domain_result.domain_trust,
            domain_matches_company=domain_result.domain_matches_company,
            ssl_valid=domain_result.ssl_valid,
            legitimacy_score=legitimacy_result.score,
            legitimacy_flags=legitimacy_result.flags,
            url_accessible=legitimacy_result.url_accessible,
            http_status_code=legitimacy_result.http_status,
            is_duplicate=dedup_result.is_duplicate,
            duplicate_of_id=dedup_result.duplicate_of_id,
            content_hash=dedup_result.content_hash,
            duration_ms=self._elapsed_ms(start_time),
        )

        # Update job model fields
        job.legitimacy_score = trust_score
        job.legitimacy_flags = legitimacy_result.flags
        job.apply_url_verified = status == "verified"
        job.apply_url_checked_at = timezone.now()
        job.apply_url_status_code = legitimacy_result.http_status
        if ats_result.platform and ats_result.platform != "unknown":
            job.ats_platform = ats_result.platform
        if final_url and final_url != apply_url:
            job.direct_apply_url = final_url
        job.save(update_fields=[
            "legitimacy_score", "legitimacy_flags", "apply_url_verified",
            "apply_url_checked_at", "apply_url_status_code", "ats_platform",
            "direct_apply_url",
        ])

        logger.info(
            "verification_complete",
            job_id=job.id,
            status=status,
            trust_score=trust_score,
            ats=ats_result.platform,
            duration_ms=self._elapsed_ms(start_time),
        )

        return result

    def verify_employer_posted_job(self, job) -> VerificationResult:
        """Employer-posted jobs from verified employers get auto-verified."""
        if job.company and job.company.is_verified:
            return self._create_result(
                job=job,
                status="verified",
                trust_score=0.9,
                notes="auto_verified:employer_is_verified",
                duration_ms=0,
            )
        return self.verify_job(job)

    def _create_result(self, job, **kwargs) -> VerificationResult:
        defaults = {
            "status": kwargs.get("status", "pending"),
            "trust_score": kwargs.get("trust_score", 0.0),
            "ats_platform_detected": kwargs.get("ats_platform_detected", ""),
            "ats_confidence": kwargs.get("ats_confidence", 0.0),
            "final_url": kwargs.get("final_url", ""),
            "redirect_chain": kwargs.get("redirect_chain", []),
            "redirect_count": kwargs.get("redirect_count", 0),
            "domain_trust": kwargs.get("domain_trust", 0.0),
            "domain_matches_company": kwargs.get("domain_matches_company", False),
            "ssl_valid": kwargs.get("ssl_valid", False),
            "legitimacy_score": kwargs.get("legitimacy_score", 0.0),
            "legitimacy_flags": kwargs.get("legitimacy_flags", []),
            "url_accessible": kwargs.get("url_accessible", False),
            "http_status_code": kwargs.get("http_status_code"),
            "is_duplicate": kwargs.get("is_duplicate", False),
            "duplicate_of_id": kwargs.get("duplicate_of_id"),
            "content_hash": kwargs.get("content_hash", ""),
            "verified_at": timezone.now(),
            "verification_duration_ms": kwargs.get("duration_ms"),
            "notes": kwargs.get("notes", ""),
        }

        result, _ = VerificationResult.objects.update_or_create(
            job=job, defaults=defaults
        )
        return result

    def _elapsed_ms(self, start_time: float) -> int:
        return int((time.time() - start_time) * 1000)
