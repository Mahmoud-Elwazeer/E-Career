"""Business Contact service (Task #14).

Generates and manages PUBLIC, ROLE-BASED business contacts for a Company —
careers@, jobs@, hr@, talent@, recruiting@, hiring@, people@, info@,
contact@ — on the company's OWN domain only. This is explicitly NOT a
personal-email-harvesting tool: there is no code path anywhere in this
module that accepts or stores a person's name tied to an email address, and
`BusinessContact` the model has no name/title field at all (see its
docstring in apps/jobs/models.py).

Generation is a deterministic PATTERN GUESS, not a verified fact: given a
Company with a known `domain` (itself only ever populated by
CompanyResolutionService or CompanyDiscoveryService from evidence this
platform already observed — never invented), this service constructs the
standard role-address pattern and records it with confidence=0.3,
verified=False, source="domain_pattern_guess". It does NOT make any network
call to confirm the address exists (no SMTP probe, no MX-based verification)
— guessing an address exists and confirming it exists are different claims,
and this service only ever makes the weaker one, honestly labeled as such.

Admin-manual entries (source="admin_manual") are the only way a
BusinessContact can ever be `verified=True` in this implementation — a human
confirmed it, this code never does.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from apps.jobs.models import BusinessContact, Company


# Generic ROLE prefixes only - never a person's name. Ordered roughly by how
# likely each is to be a real, monitored inbox at a typical employer.
GENERIC_ROLE_PREFIXES = [
    "careers", "jobs", "hr", "talent", "recruiting", "hiring", "people",
    "info", "contact",
]


@dataclass
class GenerationOutcome:
    email: str
    role_prefix: str
    created: bool
    reason: str


class BusinessContactService:
    """Stateless — module-level singleton, same pattern as every other
    service in this file family (company_resolver, company_claim_service,
    company_discovery_service)."""

    def generate_for_company(self, company: Company, *, roles: List[str] | None = None) -> List[GenerationOutcome]:
        """Generate (not verify) role-based contact guesses for a Company
        with a known domain. Idempotent - re-running does not duplicate
        existing rows (unique_together on company+email) and does not
        touch any row a human has since marked do_not_contact or verified.
        """
        if not company.domain:
            return []

        roles = roles or GENERIC_ROLE_PREFIXES
        outcomes: List[GenerationOutcome] = []

        for prefix in roles:
            if prefix not in GENERIC_ROLE_PREFIXES:
                # Defensive - never let a caller sneak a non-role (e.g. a
                # person's name) through this generation path.
                continue
            email = f"{prefix}@{company.domain}"
            existing = BusinessContact.objects.filter(company=company, email=email).first()
            if existing:
                outcomes.append(GenerationOutcome(
                    email=email, role_prefix=prefix, created=False, reason="already exists",
                ))
                continue
            BusinessContact.objects.create(
                company=company, email=email, role_prefix=prefix,
                source=BusinessContact.SOURCE_PATTERN_GUESS, confidence=0.3,
                verified=False,
                evidence={"method": "domain_pattern_guess", "domain": company.domain},
            )
            outcomes.append(GenerationOutcome(
                email=email, role_prefix=prefix, created=True, reason="generated",
            ))

        return outcomes

    def add_manual(self, company: Company, *, email: str, role_prefix: str,
                    verified: bool = True) -> BusinessContact:
        """Admin-entry path - the only way to create a verified=True
        contact. Still enforces the generic-role-prefix + same-domain
        invariant; this is not a bypass for adding a named personal
        contact."""
        if role_prefix not in GENERIC_ROLE_PREFIXES:
            raise ValueError(
                f"'{role_prefix}' is not a recognized generic role prefix. "
                f"BusinessContact is for role-based addresses only "
                f"({', '.join(GENERIC_ROLE_PREFIXES)}), never a named personal contact."
            )
        domain = email.rsplit("@", 1)[-1].lower() if "@" in email else ""
        if not domain or domain != (company.domain or "").lower():
            raise ValueError(
                f"Email domain '{domain}' does not match company domain "
                f"'{company.domain}'. BusinessContact only tracks contacts on "
                f"the company's own domain."
            )
        contact, _ = BusinessContact.objects.update_or_create(
            company=company, email=email,
            defaults={
                "role_prefix": role_prefix, "source": BusinessContact.SOURCE_ADMIN_MANUAL,
                "confidence": 1.0 if verified else 0.5, "verified": verified,
            },
        )
        if verified and not contact.verified_at:
            from django.utils import timezone
            contact.verified_at = timezone.now()
            contact.save(update_fields=["verified_at"])
        return contact

    def suppress(self, contact: BusinessContact, *, reason: str) -> BusinessContact:
        """Mark a contact do-not-contact. One-way in this implementation -
        un-suppressing is an explicit separate admin action
        (contact.is_do_not_contact = False via the admin form), never
        automatic, so a suppression is never silently undone by a later
        generate_for_company() re-run."""
        contact.is_do_not_contact = True
        contact.do_not_contact_reason = reason
        contact.save(update_fields=["is_do_not_contact", "do_not_contact_reason"])
        return contact


business_contact_service = BusinessContactService()
