from __future__ import annotations

import hashlib
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class DeduplicationResult:
    content_hash: str
    is_duplicate: bool
    duplicate_of_id: int | None = None
    method: str = ""


class DeduplicatorStage:
    """Stage 6: Detect duplicate job listings."""

    def run(self, company_name: str, title: str, location: str) -> DeduplicationResult:
        content_hash = self._compute_hash(company_name, title, location)

        from apps.verification.models import VerificationResult

        existing = (
            VerificationResult.objects.filter(content_hash=content_hash)
            .exclude(status="rejected")
            .select_related("job")
            .first()
        )

        if existing:
            return DeduplicationResult(
                content_hash=content_hash,
                is_duplicate=True,
                duplicate_of_id=existing.job_id,
                method="exact_hash",
            )

        return DeduplicationResult(
            content_hash=content_hash,
            is_duplicate=False,
        )

    def _compute_hash(self, company_name: str, title: str, location: str) -> str:
        normalized = f"{company_name.strip().lower()}|{title.strip().lower()}|{location.strip().lower()}"
        return hashlib.sha256(normalized.encode()).hexdigest()
