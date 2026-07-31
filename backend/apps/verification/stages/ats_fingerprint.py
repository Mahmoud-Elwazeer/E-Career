from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class ATSFingerprint:
    platform: str
    confidence: float
    pattern_matched: str


ATS_PATTERNS: list[tuple[str, str, float]] = [
    # (regex pattern, platform name, confidence)
    (r"greenhouse\.io/", "greenhouse", 0.95),
    (r"boards\.greenhouse\.io/", "greenhouse", 0.99),
    (r"lever\.co/", "lever", 0.95),
    (r"jobs\.lever\.co/", "lever", 0.99),
    (r"ashbyhq\.com/", "ashby", 0.95),
    (r"jobs\.ashbyhq\.com/", "ashby", 0.99),
    (r"myworkdayjobs\.com/", "workday", 0.95),
    (r"wd\d+\.myworkdayjobs\.com/", "workday", 0.99),
    (r"/wday/cxs/", "workday", 0.95),
    (r"smartrecruiters\.com/", "smartrecruiters", 0.95),
    (r"jobs\.smartrecruiters\.com/", "smartrecruiters", 0.99),
    (r"workable\.com/", "workable", 0.90),
    (r"apply\.workable\.com/", "workable", 0.99),
    (r"teamtailor\.com/", "teamtailor", 0.90),
    (r"career\.teamtailor\.com/", "teamtailor", 0.95),
    (r"bamboohr\.com/", "bamboohr", 0.90),
    (r"icims\.com/", "icims", 0.90),
    (r"taleo\.net/", "taleo", 0.90),
    (r"oracle.*cloud.*jobs", "oracle_hcm", 0.85),
    (r"successfactors\.com/", "sap_successfactors", 0.90),
    (r"jobvite\.com/", "jobvite", 0.90),
    (r"recruitee\.com/", "recruitee", 0.90),
    (r"breezy\.hr/", "breezy", 0.90),
    (r"jazz\.co/", "jazzhr", 0.90),
    (r"personio\.de/", "personio", 0.90),
    (r"deel\.com/careers", "deel", 0.85),
    (r"rippling\.com/careers", "rippling", 0.85),
    (r"/careers/?$", "company_careers_page", 0.60),
    (r"/jobs/?$", "company_careers_page", 0.55),
]

BLOCKED_DOMAINS = {
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "ziprecruiter.com",
    "monster.com",
    "careerbuilder.com",
    "dice.com",
    "simplyhired.com",
    "snagajob.com",
    "bayt.com",
    "wuzzuf.net",
    "gulftalent.com",
    "naukri.com",
    "seek.com.au",
    "reed.co.uk",
}


class ATSFingerprintStage:
    """Stage 1: Identify ATS platform from URL patterns."""

    def run(self, url: str) -> ATSFingerprint:
        if not url:
            return ATSFingerprint(platform="unknown", confidence=0.0, pattern_matched="")

        parsed = urlparse(url)
        domain = parsed.netloc.lower().lstrip("www.")

        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            return ATSFingerprint(
                platform="BLOCKED_AGGREGATOR",
                confidence=1.0,
                pattern_matched=f"blocked_domain:{domain}",
            )

        for pattern, platform, confidence in ATS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return ATSFingerprint(
                    platform=platform,
                    confidence=confidence,
                    pattern_matched=pattern,
                )

        return ATSFingerprint(
            platform="unknown",
            confidence=0.3,
            pattern_matched="no_match",
        )

    def is_blocked(self, url: str) -> bool:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().lstrip("www.")
        return any(blocked in domain for blocked in BLOCKED_DOMAINS)
