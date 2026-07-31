from __future__ import annotations

import re
from dataclasses import dataclass, field

import httpx
import structlog

logger = structlog.get_logger()

SCAM_INDICATORS = [
    (r"(?i)(work from home|earn \$\d+|guaranteed income|no experience needed)", "scam_language"),
    (r"(?i)(western union|wire transfer|money order|bitcoin payment)", "suspicious_payment"),
    (r"(?i)(personal bank|social security|ssn|passport number)", "pii_harvesting"),
    (r"(?i)(fee required|pay upfront|registration fee|training fee)", "upfront_fee"),
    (r"(?i)(100% commission|unlimited earning)", "mlm_language"),
]

QUALITY_INDICATORS = [
    (r"(?i)(years of experience|bachelor|master|phd|degree)", "education_requirement"),
    (r"(?i)(401k|health insurance|dental|vision|pto|paid time off)", "benefits_listed"),
    (r"(?i)(equal opportunity|eeo|diversity)", "eeo_statement"),
    (r"(?i)(responsibilities|qualifications|requirements)", "structured_posting"),
]


@dataclass
class LegitimacyResult:
    score: float
    flags: list[str] = field(default_factory=list)
    url_accessible: bool = False
    http_status: int | None = None


class LegitimacyScorerStage:
    """Stage 4: Score job legitimacy based on content analysis and URL accessibility."""

    def run(self, description: str, apply_url: str, salary_min: int | None = None) -> LegitimacyResult:
        flags = []
        score = 0.5

        scam_count = self._check_scam_indicators(description, flags)
        quality_count = self._check_quality_indicators(description, flags)

        score -= scam_count * 0.15
        score += quality_count * 0.08

        if salary_min and salary_min > 500000:
            flags.append("unrealistic_salary")
            score -= 0.1

        if description and len(description) < 100:
            flags.append("description_too_short")
            score -= 0.1
        elif description and len(description) > 300:
            score += 0.05

        url_accessible = False
        http_status = None
        if apply_url:
            url_accessible, http_status = self._check_url_accessibility(apply_url)
            if url_accessible:
                score += 0.2
            else:
                flags.append(f"url_not_accessible:{http_status}")
                score -= 0.2

        score = max(0.0, min(1.0, score))

        return LegitimacyResult(
            score=round(score, 3),
            flags=flags,
            url_accessible=url_accessible,
            http_status=http_status,
        )

    def _check_scam_indicators(self, text: str, flags: list[str]) -> int:
        count = 0
        for pattern, flag_name in SCAM_INDICATORS:
            if re.search(pattern, text):
                flags.append(flag_name)
                count += 1
        return count

    def _check_quality_indicators(self, text: str, flags: list[str]) -> int:
        count = 0
        for pattern, flag_name in QUALITY_INDICATORS:
            if re.search(pattern, text):
                count += 1
        return count

    def _check_url_accessibility(self, url: str) -> tuple[bool, int | None]:
        try:
            response = httpx.head(url, timeout=10, follow_redirects=True, verify=False)
            return response.status_code < 400, response.status_code
        except httpx.TimeoutException:
            return False, 408
        except Exception:
            return False, None
