from __future__ import annotations

import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urlparse

import structlog

logger = structlog.get_logger()

KNOWN_ATS_DOMAINS = {
    "greenhouse.io", "boards.greenhouse.io",
    "lever.co", "jobs.lever.co",
    "ashbyhq.com", "jobs.ashbyhq.com",
    "myworkdayjobs.com",
    "smartrecruiters.com", "jobs.smartrecruiters.com",
    "workable.com", "apply.workable.com",
    "teamtailor.com",
    "bamboohr.com",
    "icims.com",
    "taleo.net",
    "jobvite.com",
    "recruitee.com",
    "breezy.hr",
}


@dataclass
class DomainVerification:
    domain_trust: float
    domain_matches_company: bool
    ssl_valid: bool
    notes: list[str]


class DomainVerifierStage:
    """Stage 3: Verify the apply URL domain belongs to the company or known ATS."""

    def run(self, url: str, company_domain: str = "", careers_page_url: str = "") -> DomainVerification:
        if not url:
            return DomainVerification(
                domain_trust=0.0, domain_matches_company=False, ssl_valid=False, notes=["empty_url"]
            )

        parsed = urlparse(url)
        apply_domain = parsed.netloc.lower().lstrip("www.")
        notes = []
        trust = 0.0

        is_ats = self._is_known_ats(apply_domain)
        if is_ats:
            trust += 0.5
            notes.append(f"known_ats_domain:{apply_domain}")

        domain_matches = False
        if company_domain:
            company_domain = company_domain.lower().lstrip("www.")
            if company_domain in apply_domain or apply_domain in company_domain:
                domain_matches = True
                trust += 0.3
                notes.append("domain_matches_company")

        if careers_page_url:
            careers_parsed = urlparse(careers_page_url)
            careers_domain = careers_parsed.netloc.lower().lstrip("www.")
            if careers_domain == apply_domain or apply_domain in careers_domain:
                trust += 0.15
                notes.append("matches_careers_page")

        ssl_valid = self._check_ssl(parsed.netloc)
        if ssl_valid:
            trust += 0.05
            notes.append("ssl_valid")

        trust = min(trust, 1.0)

        return DomainVerification(
            domain_trust=round(trust, 3),
            domain_matches_company=domain_matches,
            ssl_valid=ssl_valid,
            notes=notes,
        )

    def _is_known_ats(self, domain: str) -> bool:
        for ats_domain in KNOWN_ATS_DOMAINS:
            if ats_domain in domain:
                return True
        return False

    def _check_ssl(self, host: str) -> bool:
        if ":" in host:
            host = host.split(":")[0]
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    return cert is not None
        except Exception:
            return False
