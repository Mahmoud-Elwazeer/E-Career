"""
Email Verification Service.

Multi-layer email validation for employer registration and contact verification.
Layers:
1. Syntax validation (RFC compliance)
2. Disposable domain blocking
3. MX/DNS deliverability check
4. Domain authentication (SPF, DMARC) — optional
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger()


class VerificationStatus(str, Enum):
    VALID = "valid"
    INVALID_SYNTAX = "invalid_syntax"
    DISPOSABLE = "disposable"
    NO_MX_RECORD = "no_mx_record"
    UNDELIVERABLE = "undeliverable"
    RISKY = "risky"
    UNKNOWN = "unknown"


@dataclass
class EmailVerificationResult:
    email: str
    normalized_email: str
    status: VerificationStatus
    is_valid: bool
    is_disposable: bool
    has_mx_record: bool
    domain: str
    checks_performed: list[str]
    details: str = ""


class EmailVerificationService:
    """Multi-layer email verification."""

    def __init__(self):
        self._disposable_domains: set[str] | None = None

    @property
    def disposable_domains(self) -> set[str]:
        """Lazy-load disposable domain list."""
        if self._disposable_domains is None:
            self._disposable_domains = self._load_disposable_domains()
        return self._disposable_domains

    def verify(self, email: str, check_mx: bool = True) -> EmailVerificationResult:
        """Perform full email verification."""
        checks = []

        normalized, syntax_error = self._check_syntax(email)
        checks.append("syntax")
        if syntax_error:
            return EmailVerificationResult(
                email=email,
                normalized_email=email.lower().strip(),
                status=VerificationStatus.INVALID_SYNTAX,
                is_valid=False,
                is_disposable=False,
                has_mx_record=False,
                domain="",
                checks_performed=checks,
                details=syntax_error,
            )

        domain = normalized.split("@")[1]

        is_disposable = self._check_disposable(domain)
        checks.append("disposable")
        if is_disposable:
            return EmailVerificationResult(
                email=email,
                normalized_email=normalized,
                status=VerificationStatus.DISPOSABLE,
                is_valid=False,
                is_disposable=True,
                has_mx_record=False,
                domain=domain,
                checks_performed=checks,
                details="Disposable/temporary email domain detected.",
            )

        has_mx = True
        if check_mx:
            has_mx = self._check_mx(domain)
            checks.append("mx_record")
            if not has_mx:
                return EmailVerificationResult(
                    email=email,
                    normalized_email=normalized,
                    status=VerificationStatus.NO_MX_RECORD,
                    is_valid=False,
                    is_disposable=False,
                    has_mx_record=False,
                    domain=domain,
                    checks_performed=checks,
                    details=f"No MX record found for domain {domain}.",
                )

        return EmailVerificationResult(
            email=email,
            normalized_email=normalized,
            status=VerificationStatus.VALID,
            is_valid=True,
            is_disposable=False,
            has_mx_record=has_mx,
            domain=domain,
            checks_performed=checks,
        )

    def verify_batch(self, emails: list[str]) -> list[EmailVerificationResult]:
        """Verify multiple emails."""
        return [self.verify(email) for email in emails]

    def _check_syntax(self, email: str) -> tuple[str, str | None]:
        """Check email syntax and normalize. Returns (normalized, error_or_none)."""
        try:
            from email_validator import validate_email, EmailNotValidError
            result = validate_email(email, check_deliverability=False)
            return result.normalized, None
        except ImportError:
            import re
            email = email.strip().lower()
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return email, None
            return email, "Invalid email format."
        except Exception as e:
            return email.strip().lower(), str(e)

    def _check_disposable(self, domain: str) -> bool:
        """Check if domain is a known disposable email provider."""
        return domain.lower() in self.disposable_domains

    def _check_mx(self, domain: str) -> bool:
        """Check if domain has MX records."""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, "MX")
            return len(answers) > 0
        except ImportError:
            try:
                from email_validator import validate_email
                result = validate_email(f"test@{domain}", check_deliverability=True)
                return True
            except Exception:
                return False
        except Exception:
            return False

    def _load_disposable_domains(self) -> set[str]:
        """Load disposable domain list."""
        domains = set()

        try:
            from disposable_email_domains import blocklist
            domains.update(blocklist)
            logger.info("disposable_domains_loaded", count=len(domains), source="package")
            return domains
        except ImportError:
            pass

        known_disposable = {
            "mailinator.com", "guerrillamail.com", "tempmail.com",
            "throwaway.email", "yopmail.com", "10minutemail.com",
            "trashmail.com", "sharklasers.com", "guerrillamailblock.com",
            "grr.la", "dispostable.com", "getairmail.com",
            "mailnesia.com", "tempr.email", "fakeinbox.com",
            "temp-mail.org", "emailondeck.com", "33mail.com",
        }
        domains.update(known_disposable)
        logger.info("disposable_domains_loaded", count=len(domains), source="hardcoded_fallback")
        return domains


_service: EmailVerificationService | None = None


def get_email_verification_service() -> EmailVerificationService:
    """Get singleton email verification service."""
    global _service
    if _service is None:
        _service = EmailVerificationService()
    return _service


def verify_email(email: str) -> EmailVerificationResult:
    """Convenience function for single email verification."""
    return get_email_verification_service().verify(email)
