"""Company Claim Service (Task #12).

Lets an employer user claim ownership of an EXISTING Company row (most often
one discovered via scraping, with jobs already attached through the Company
Resolution Service — see company_resolution.py) rather than attaching to any
active Company with zero proof (the gap in
apps.employers.views.EmployerRegistrationView), or always creating a brand
new duplicate Company for a real employer that was already discovered.

Evidence model (deliberately conservative — same-name or free-mail claims
are NEVER sufficient on their own, per the directive):

  corporate_email  claimant's account email domain == Company.domain (or a
                    domain ever observed for this Company via
                    CompanyResolutionIdentity), AND that domain is not a
                    known free-mail provider. This is the only evidence type
                    that can reach HIGH automated confidence, and even then
                    the claim lands in UNDER_REVIEW, not auto-APPROVED — see
                    `AUTO_APPROVE` note on `evaluate()`. Admin review is
                    always the final gate in this implementation; nothing
                    here auto-approves a claim unattended.

  dns_txt           claimant proves control of the company's own domain by
                     publishing a TXT record containing a server-generated
                     token at `_usam-verify.<domain>`. This is a real,
                     independent website-ownership proof (the same technique
                     Google Search Console / many SaaS "verify your domain"
                     flows use) and does NOT depend on the claimant's email
                     provider at all.

  document           claimant uploads a document (business registration,
                      incorporation certificate, letterhead) for a human
                      admin to review. Always VERIFICATION_REQUIRED ->
                      UNDER_REVIEW; this service does no automated scoring
                      of document content (that would require OCR/LLM review
                      not currently wired to this evidence type — honestly
                      left as a human-review-only path, not faked).

  admin_manual        an admin creates/approves a claim directly, bypassing
                      every automated check (e.g. after an out-of-band
                      support conversation). Not reachable from the
                      employer-facing API — admin action only.

Approval does not touch any existing Job or CompanyResolutionIdentity row —
it only grants the claimant an EmployerProfile + EmployerTeamMember(role=
'owner') on the SAME Company (idempotent: approving twice, or a user who
already has a profile elsewhere, is handled without crashing or duplicating).
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.jobs.models import Company, CompanyClaim, CompanyResolutionIdentity

# A deliberately short, well-known list of free/consumer mail providers. This
# is NOT meant to be exhaustive (there is no universal authoritative list —
# new free providers appear constantly) — it only has to catch the common
# case well enough that "same name, free mail" is correctly never treated as
# strong evidence. Anything not on this list is treated as a (weaker,
# non-corporate-confirmed) possible-corporate domain, not as automatically
# trusted — the domain-match check against Company.domain is what actually
# gates confidence, this list only prevents a gmail.com match from ever
# being miscounted as a domain match in the first place (it can't be, since
# no real Company.domain would ever legitimately be "gmail.com", but the
# flag is still recorded on the claim for admin visibility and for any
# future stricter check that wants to use it independent of domain match).
FREE_MAIL_DOMAINS = frozenset({
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
    "icloud.com", "aol.com", "protonmail.com", "proton.me", "gmx.com",
    "mail.com", "zoho.com", "yandex.com", "qq.com", "163.com",
})

DNS_TXT_PREFIX = "_usam-verify"


@dataclass
class ClaimEvaluation:
    """Result of evaluating a claim's evidence (does NOT itself change the
    claim's status — the caller decides what to do with this)."""
    confidence: float
    recommended_status: str
    evidence: dict = field(default_factory=dict)
    is_free_mail_domain: bool = False


def email_domain(email: str) -> str:
    """Extract the domain portion of an email address, lowercased. Public
    helper (used by both this service's own evaluation and by the
    employer-facing CompanyClaim API view when first recording the
    claimant's email domain on claim creation)."""
    email = (email or "").strip().lower()
    return email.rsplit("@", 1)[-1] if "@" in email else ""


def _known_domains_for_company(company: Company) -> set[str]:
    """Every domain this Company has ever been associated with: its own
    `domain` field plus any domain recorded in its CompanyResolutionIdentity
    history (an ATS migration can observe a domain before Company.domain
    itself gets backfilled)."""
    domains = set()
    if company.domain:
        domains.add(company.domain.lower().removeprefix("www."))
    for d in CompanyResolutionIdentity.objects.filter(
        company=company
    ).exclude(domain="").values_list("domain", flat=True):
        domains.add(d.lower().removeprefix("www."))
    return domains


class CompanyClaimService:
    """Evaluate evidence and transition CompanyClaim state. Stateless —
    safe to use as a module-level singleton like `company_resolver`."""

    def generate_dns_token(self) -> str:
        """A random, unguessable token for a dns_txt challenge. 32 hex chars
        (16 bytes) — short enough to fit comfortably in a TXT record, long
        enough that guessing it is infeasible."""
        return secrets.token_hex(16)

    def evaluate_corporate_email(self, *, company: Company, claimant_email: str) -> ClaimEvaluation:
        """Score a corporate_email claim WITHOUT mutating anything. Pure
        evaluation so it can be called from both the claim-creation view
        (to set initial status) and from an admin review action (to show
        the admin the same evidence, re-computed fresh)."""
        domain = email_domain(claimant_email)
        is_free = domain in FREE_MAIL_DOMAINS
        known_domains = _known_domains_for_company(company)
        exact_match = bool(domain) and domain in known_domains

        evidence = {
            "claimant_email_domain": domain,
            "company_known_domains": sorted(known_domains),
            "exact_match": exact_match,
            "is_free_mail_domain": is_free,
        }

        if is_free:
            # Free-mail claims are NEVER sufficient alone, no matter what
            # the domain match says (a free-mail domain never legitimately
            # equals a real Company.domain anyway, but this guards the
            # confidence explicitly rather than relying on that coincidence).
            return ClaimEvaluation(
                confidence=0.1,
                recommended_status=CompanyClaim.STATUS_VERIFICATION_REQUIRED,
                evidence=evidence,
                is_free_mail_domain=True,
            )

        if not domain or not known_domains:
            # No company domain on record to compare against at all - this
            # claim can't be auto-scored higher than "needs more evidence".
            return ClaimEvaluation(
                confidence=0.2,
                recommended_status=CompanyClaim.STATUS_VERIFICATION_REQUIRED,
                evidence=evidence,
            )

        if exact_match:
            # Strong signal, but per this implementation's conservative
            # policy, even an exact corporate-domain match lands in
            # UNDER_REVIEW for a human admin to confirm - this service does
            # not auto-APPROVE anything (see module docstring).
            return ClaimEvaluation(
                confidence=0.8,
                recommended_status=CompanyClaim.STATUS_UNDER_REVIEW,
                evidence=evidence,
            )

        # Non-free domain that simply doesn't match any known company
        # domain - weak evidence, needs a stronger proof (dns_txt/document).
        return ClaimEvaluation(
            confidence=0.3,
            recommended_status=CompanyClaim.STATUS_VERIFICATION_REQUIRED,
            evidence=evidence,
        )

    def check_dns_txt(self, *, domain: str, expected_token: str, resolver=None) -> ClaimEvaluation:
        """Look up `_usam-verify.<domain>` TXT records and check whether
        `expected_token` is present in any of them.

        `resolver` is an injectable callable `(name: str) -> list[str]`
        returning raw TXT record strings, so this is unit-testable offline
        without a real DNS query (mirrors the injectable-resolver pattern
        already used by apps/scraper/pipeline/ssrf_guard.py). The default
        resolver uses dnspython if installed, else falls back to an honest
        "cannot verify" result rather than silently claiming success -
        dnspython is NOT currently a project dependency (confirmed: no
        `dns.resolver` import anywhere in the codebase, not in
        requirements/*.txt), so by default this always returns
        UNVERIFIABLE until an operator adds it.
        """
        domain = (domain or "").strip().lower().removeprefix("www.")
        if not domain or not expected_token:
            return ClaimEvaluation(
                confidence=0.0, recommended_status=CompanyClaim.STATUS_VERIFICATION_REQUIRED,
                evidence={"error": "missing domain or token"},
            )

        query_name = f"{DNS_TXT_PREFIX}.{domain}"

        if resolver is None:
            resolver = self._default_dns_resolver

        try:
            records = resolver(query_name)
        except _DnsUnavailable as e:
            return ClaimEvaluation(
                confidence=0.0,
                recommended_status=CompanyClaim.STATUS_VERIFICATION_REQUIRED,
                evidence={"query_name": query_name, "error": str(e), "unverifiable": True},
            )
        except Exception as e:  # live DNS lookups can fail many ways (NXDOMAIN, timeout, ...)
            return ClaimEvaluation(
                confidence=0.0,
                recommended_status=CompanyClaim.STATUS_VERIFICATION_REQUIRED,
                evidence={"query_name": query_name, "error": str(e)},
            )

        found = any(expected_token in (r or "") for r in records)
        evidence = {"query_name": query_name, "records_found": list(records), "token_matched": found}

        if found:
            # DNS control is a strong, website-ownership-independent proof.
            # Still lands in UNDER_REVIEW, not auto-approved - consistent
            # with the corporate_email policy above (admin is always the
            # final gate in this implementation).
            return ClaimEvaluation(
                confidence=0.9, recommended_status=CompanyClaim.STATUS_UNDER_REVIEW, evidence=evidence,
            )
        return ClaimEvaluation(
            confidence=0.1, recommended_status=CompanyClaim.STATUS_VERIFICATION_REQUIRED, evidence=evidence,
        )

    @staticmethod
    def _default_dns_resolver(query_name: str):
        try:
            import dns.resolver  # type: ignore
        except ImportError:
            raise _DnsUnavailable(
                "dnspython is not installed - dns_txt evidence cannot be "
                "automatically verified on this deployment. Install "
                "dnspython and set a resolver, or review manually."
            )
        answers = dns.resolver.resolve(query_name, "TXT")
        return ["".join(part.decode() if isinstance(part, bytes) else part for part in a.strings) for a in answers]

    @transaction.atomic
    def approve(self, claim: CompanyClaim, *, reviewed_by, note: str = ""):
        """Approve a claim: mark it APPROVED and grant the claimant an
        owner EmployerProfile + EmployerTeamMember on the claimed Company.
        Idempotent against a claimant who already has a profile/membership
        elsewhere - raises a clear error rather than silently reassigning
        their existing company.
        """
        from apps.employers.models import EmployerProfile, EmployerTeamMember

        if claim.status in (CompanyClaim.STATUS_APPROVED,):
            return claim  # already approved - no-op, not an error

        existing_profile = EmployerProfile.objects.filter(user=claim.claimant).first()
        if existing_profile and existing_profile.company_id != claim.company_id:
            raise ValueError(
                f"Claimant already has an employer profile for a different "
                f"company ({existing_profile.company_id}); cannot approve "
                f"this claim without resolving that conflict first."
            )

        claim.status = CompanyClaim.STATUS_APPROVED
        claim.reviewed_by = reviewed_by
        claim.reviewed_at = timezone.now()
        claim.review_note = note
        claim.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])

        if existing_profile is None:
            EmployerProfile.objects.create(
                user=claim.claimant, company=claim.company,
                job_title="Owner", is_verified=True,
                verified_at=timezone.now(), verified_by=reviewed_by,
            )
        else:
            if not existing_profile.is_verified:
                existing_profile.is_verified = True
                existing_profile.verified_at = timezone.now()
                existing_profile.verified_by = reviewed_by
                existing_profile.save(update_fields=["is_verified", "verified_at", "verified_by"])

        EmployerTeamMember.objects.update_or_create(
            user=claim.claimant, company=claim.company,
            defaults={"role": "owner", "is_active": True, "accepted_at": timezone.now()},
        )

        if claim.claimant.role != "employer":
            claim.claimant.role = "employer"
            claim.claimant.save(update_fields=["role"])

        return claim

    def reject(self, claim: CompanyClaim, *, reviewed_by, note: str = "") -> CompanyClaim:
        claim.status = CompanyClaim.STATUS_REJECTED
        claim.reviewed_by = reviewed_by
        claim.reviewed_at = timezone.now()
        claim.review_note = note
        claim.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])
        return claim

    def revoke(self, claim: CompanyClaim, *, reviewed_by, note: str = "") -> CompanyClaim:
        """Revoke a previously APPROVED claim (company sold, fraud found
        after the fact, etc). Does NOT delete the EmployerProfile/
        EmployerTeamMember it created - that is a separate, deliberate admin
        decision (revoking the claim's legitimacy and removing the
        employer's access are not always the same moment in practice)."""
        if claim.status != CompanyClaim.STATUS_APPROVED:
            raise ValueError("Only an approved claim can be revoked.")
        claim.status = CompanyClaim.STATUS_REVOKED
        claim.reviewed_by = reviewed_by
        claim.reviewed_at = timezone.now()
        claim.review_note = note
        claim.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])
        return claim


class _DnsUnavailable(Exception):
    """Raised when the dns_txt evidence check cannot run at all (no DNS
    library available) - distinct from a real lookup failure (NXDOMAIN,
    timeout), which is a normal operational outcome, not a code gap."""


company_claim_service = CompanyClaimService()
