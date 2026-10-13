"""
Legal/consent orchestration services.

Business rules that must not leak into views:
  - Policy activation (only one ACTIVE version per document+locale+jurisdiction)
  - Consent grant/withdraw (always append a new row, never mutate history)
  - DSR lifecycle transitions + SLA computation from JurisdictionPolicyProfile
"""
from __future__ import annotations

from django.db import transaction as db_transaction
from django.utils import timezone

from .models import (
    PolicyVersion, PolicyAcceptance, ConsentPurpose, ConsentRecord,
    PrivacyRequest, PrivacyRequestEvent, JurisdictionPolicyProfile,
)


# ── Policy lifecycle ─────────────────────────────────────────────────────────

@db_transaction.atomic
def activate_version(*, version: PolicyVersion, approver=None) -> PolicyVersion:
    """Promote a version to ACTIVE, retiring any previously-active version for
    the same (document, locale, jurisdiction). Never deletes/overwrites the
    retired version's content — it just flips status + retired_at.
    """
    if version.status not in (PolicyVersion.Status.APPROVED, PolicyVersion.Status.SCHEDULED):
        raise ValueError("Only an APPROVED or SCHEDULED version can be activated.")

    siblings = PolicyVersion.objects.filter(
        document=version.document, locale=version.locale,
        jurisdiction=version.jurisdiction, status=PolicyVersion.Status.ACTIVE,
    ).exclude(pk=version.pk)
    now = timezone.now()
    for sibling in siblings:
        sibling.status = PolicyVersion.Status.RETIRED
        sibling.retired_at = now
        sibling.save(update_fields=["status", "retired_at"])

    version.status = PolicyVersion.Status.ACTIVE
    version.effective_at = version.effective_at or now
    if approver is not None:
        version.approved_by = approver
    version.save(update_fields=["status", "effective_at", "approved_by"])
    return version


def get_active_version(document_slug: str, *, locale: str = "en",
                       jurisdiction: str | None = None) -> PolicyVersion | None:
    from .models import PolicyDocument
    qs = PolicyVersion.objects.filter(
        document__slug=document_slug, locale=locale, status=PolicyVersion.Status.ACTIVE,
    )
    if jurisdiction:
        qs = qs.filter(jurisdiction=jurisdiction)
    return qs.order_by("-effective_at").first() or PolicyVersion.objects.filter(
        document__slug=document_slug, locale=locale, status=PolicyVersion.Status.ACTIVE,
    ).order_by("-effective_at").first()


def record_acceptance(*, user, policy_version: PolicyVersion, method: str,
                      ip_address: str | None = None, user_agent: str = "") -> PolicyAcceptance:
    return PolicyAcceptance.objects.create(
        user=user, policy_version=policy_version, method=method,
        ip_address=ip_address, user_agent=user_agent[:500],
    )


def needs_reacceptance(user, document_slug: str, *, locale: str = "en") -> bool:
    """True if the user has never accepted the current ACTIVE version of a
    policy document, OR the active version is a material change they haven't
    re-accepted yet."""
    active = get_active_version(document_slug, locale=locale)
    if active is None:
        return False
    return not PolicyAcceptance.objects.filter(user=user, policy_version=active).exists()


# ── Consent ──────────────────────────────────────────────────────────────────

def current_consent_status(user, purpose_key: str) -> bool:
    """Latest consent state for one purpose. Defaults to False (no silent
    opt-in) unless the purpose itself is marked required (e.g. necessary
    cookies, which aren't modeled through this table anyway)."""
    record = (ConsentRecord.objects.filter(user=user, purpose__key=purpose_key)
             .order_by("-created_at").first())
    if record is None:
        return False
    return record.status == ConsentRecord.Status.GRANTED


@db_transaction.atomic
def set_consent(*, user, purpose_key: str, granted: bool, method: str = "settings",
                ip_address: str | None = None, policy_version: PolicyVersion | None = None) -> ConsentRecord:
    purpose = ConsentPurpose.objects.get(key=purpose_key, is_active=True)
    if purpose.is_required and not granted:
        raise ValueError(f"Consent purpose '{purpose_key}' is required and cannot be withdrawn.")
    return ConsentRecord.objects.create(
        user=user, purpose=purpose,
        status=ConsentRecord.Status.GRANTED if granted else ConsentRecord.Status.WITHDRAWN,
        method=method, ip_address=ip_address, policy_version=policy_version,
    )


# ── DSR workflow ─────────────────────────────────────────────────────────────

def _compute_due_at(jurisdiction: str):
    profile = JurisdictionPolicyProfile.objects.filter(jurisdiction=jurisdiction).first()
    if not profile or not profile.dsr_sla_days:
        return None
    return timezone.now() + timezone.timedelta(days=profile.dsr_sla_days)


@db_transaction.atomic
def open_privacy_request(*, user, request_type: str, details: str = "",
                         jurisdiction: str = "OTHER", ip_address: str | None = None) -> PrivacyRequest:
    req = PrivacyRequest.objects.create(
        user=user, request_type=request_type, details=details,
        jurisdiction=jurisdiction, ip_address=ip_address,
        due_at=_compute_due_at(jurisdiction),
    )
    PrivacyRequestEvent.objects.create(request=req, event_type="opened", note=details[:500])
    return req


@db_transaction.atomic
def transition_privacy_request(*, request: PrivacyRequest, new_status: str, actor=None,
                                note: str = "") -> PrivacyRequest:
    valid = {s for s, _ in PrivacyRequest.Status.choices}
    if new_status not in valid:
        raise ValueError(f"Unknown status: {new_status}")
    request.status = new_status
    if new_status in (PrivacyRequest.Status.COMPLETED, PrivacyRequest.Status.REJECTED,
                      PrivacyRequest.Status.CANCELLED):
        request.resolved_at = timezone.now()
        request.resolved_by = actor
        if note:
            request.resolution_note = note
    request.save()
    PrivacyRequestEvent.objects.create(
        request=request, actor=actor, event_type=f"status:{new_status}", note=note,
    )
    return request
