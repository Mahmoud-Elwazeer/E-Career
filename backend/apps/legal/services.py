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
    CookieConsent,
)

# Marker that must never be live in an ACTIVE, publicly-served version. Kept
# as a plain constant here (not imported from readiness_service) to avoid a
# circular import; both modules intentionally use the identical literal.
UNRESOLVED_MARKER = "REQUIRES LEGAL REVIEW"


class ActivationBlocked(ValueError):
    """Raised when a version cannot be safely activated — e.g. it still
    contains an unresolved placeholder marker. A ValueError subclass so
    existing `except ValueError` call sites (admin_views.py) keep working
    without changes."""


# ── Policy lifecycle ─────────────────────────────────────────────────────────

@db_transaction.atomic
def activate_version(*, version: PolicyVersion, approver=None,
                     allow_unresolved_markers: bool = False) -> PolicyVersion:
    """Promote a version to ACTIVE, retiring any previously-active version for
    the same (document, locale, jurisdiction). Never deletes/overwrites the
    retired version's content — it just flips status + retired_at.

    Safety gate (directive-mandated): by default, a version whose content
    still contains an unresolved "REQUIRES LEGAL REVIEW" placeholder (this
    covers missing legal-entity/contact facts too — every such gap is
    represented by this literal marker in the seeded text) CANNOT be
    activated through this function — enforced here, at the one real
    activation chokepoint, not merely reported after the fact by
    `legal_readiness`. This is the path the Admin Legal Control Plane uses
    (`admin_views.policy_version_transition`), so production activation can
    never publish an unreviewed placeholder.

    `allow_unresolved_markers=True` exists ONLY for `seed_legal
    --activate-drafts`'s test/staging convenience path, which is itself
    gated behind an explicit, never-production-default CLI flag — it is not
    reachable from any admin-facing API.

    Every activation writes an append-only `core.ActivityLog` entry
    (actor/policy/version/previous-active/timestamp/material_change/
    effective_at/reacceptance_required) — reusing the platform's existing
    audit mechanism rather than building a second, competing one.
    """
    if version.status not in (PolicyVersion.Status.APPROVED, PolicyVersion.Status.SCHEDULED):
        raise ValueError("Only an APPROVED or SCHEDULED version can be activated.")

    if not allow_unresolved_markers and UNRESOLVED_MARKER in (version.content_markdown or ""):
        raise ActivationBlocked(
            f"Cannot activate {version.document.slug} v{version.version_label}: "
            f"its content still contains an unresolved '{UNRESOLVED_MARKER}' "
            f"placeholder (missing legal entity/contact/other confirmed fact). "
            f"Resolve the placeholder (or create a reviewed version) before activating."
        )

    siblings = PolicyVersion.objects.filter(
        document=version.document, locale=version.locale,
        jurisdiction=version.jurisdiction, status=PolicyVersion.Status.ACTIVE,
    ).exclude(pk=version.pk)
    previous_active = siblings.first()
    previous_active_label = previous_active.version_label if previous_active else None
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

    _log_policy_activation(version=version, approver=approver,
                            previous_active_label=previous_active_label, now=now)
    return version


def _log_policy_activation(*, version: PolicyVersion, approver, previous_active_label, now) -> None:
    """Append-only audit entry for a policy activation, using the existing
    `apps.core.models.ActivityLog` table rather than a second audit system."""
    from apps.core.models import ActivityLog

    ActivityLog.objects.create(
        user=approver,
        action="legal.policy_activate",
        target_type="PolicyVersion",
        target_id=str(version.uuid),
        metadata={
            "document_slug": version.document.slug,
            "version_label": version.version_label,
            "locale": version.locale,
            "jurisdiction": version.jurisdiction,
            "previous_active_version_label": previous_active_label,
            "material_change": version.material_change,
            "effective_at": version.effective_at.isoformat() if version.effective_at else None,
            "reacceptance_required": version.material_change,
            "activated_at": now.isoformat(),
        },
    )


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

def sync_anonymous_cookie_consent_to_user(*, user, session_key: str | None) -> "CookieConsent | None":
    """Carry an anonymous visitor's most recent cookie-consent choice
    forward to their account at login (directive item 6).

    Directive-mandated rules this function enforces:
      - Never invents or broadens consent. It copies the anonymous
        session's exact `action`/`categories` dict verbatim into a new row
        — it never upgrades a REJECT_NON_ESSENTIAL into ACCEPT_ALL or adds
        a category the anonymous choice didn't have.
      - Only runs when a real anonymous `session_key` is available (the
        caller is responsible for not fabricating one) and that session
        actually has a recorded `CookieConsent` row — if either is
        missing, this is a no-op (returns None), and the user simply sees
        the banner again post-login, which is the privacy-safe default
        already documented in the master compliance doc (never silently
        broadens consent).
      - Idempotent per login: if this user already has ANY CookieConsent
        row (their own prior choice, or an earlier carryover), this never
        overwrites it — carryover only ever fills a genuine gap for a
        brand-new account, never clobbers an existing authenticated choice.
      - Provenance is recorded (`carried_over_from_session_key`) so the
        carryover is distinguishable in the audit trail from a choice the
        user actually made while authenticated.
    """
    if not session_key:
        return None
    if CookieConsent.objects.filter(user=user).exists():
        return None  # user already has their own authenticated choice — never overwrite

    anon_consent = (
        CookieConsent.objects.filter(session_key=session_key, user__isnull=True)
        .order_by("-created_at").first()
    )
    if anon_consent is None:
        return None

    return CookieConsent.objects.create(
        user=user, session_key="", policy_version=anon_consent.policy_version,
        action=anon_consent.action, categories=dict(anon_consent.categories),
        ip_address=anon_consent.ip_address,
        carried_over_from_session_key=session_key,
    )


def can_send_marketing(user, channel: str) -> bool:
    """Canonical marketing-send eligibility gate (directive item 11).

    This is the ONE function every marketing/promotional/campaign send path
    (email digest, re-engagement, SMS campaigns, future push campaigns)
    must call before sending to a given user. It is deliberately NOT used
    for transactional, security, billing, or application-status
    notifications — those are governed by `apps.notifications.
    NotificationPreference` and must never be gated by this function.

    `channel` is one of "email" or "sms" (matches
    `MarketingPreference.email_marketing_opt_in` /
    `.sms_marketing_opt_in`).

    Rules enforced, most restrictive wins:
      - No `MarketingPreference` row for the user -> not eligible (default
        is opt-OUT, never opt-in-by-absence).
      - `unsubscribed_at` is set -> never eligible on ANY channel, even if
        a specific channel's boolean is somehow still True — an explicit
        unsubscribe is an absolute stop, not just a per-channel toggle.
      - The channel-specific opt-in boolean must be True.
      - An inactive/soft-deleted user is never eligible on any channel.
    """
    if channel not in ("email", "sms"):
        raise ValueError(f"Unknown marketing channel: {channel!r}")

    if not getattr(user, "is_active", True):
        return False
    if getattr(user, "is_deleted", False):
        return False

    from .models import MarketingPreference

    pref = MarketingPreference.objects.filter(user=user).first()
    if pref is None:
        return False
    if pref.unsubscribed_at is not None:
        return False

    return pref.email_marketing_opt_in if channel == "email" else pref.sms_marketing_opt_in


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
    """Open a DSR ticket. `apps.legal.PrivacyRequest` is the CANONICAL
    governance record for every data-subject request on this platform
    (directive item 7 — consolidation, not a rewrite).

    For EXPORT and DELETE request types, this also triggers the REAL,
    already-working executor in `apps.accounts` (`tasks_gdpr.
    generate_data_export` / `.process_account_deletion`) via the legacy
    `DataExportRequest`/`AccountDeletionRequest` models — those legacy
    models are kept exactly as they are (not deleted, not duplicated with
    a second implementation) but are now LINKED back to this PrivacyRequest
    ticket (`privacy_request` FK) so the Privacy Center shows one ticket
    with real status, instead of a DSR row that silently does nothing.
    """
    req = PrivacyRequest.objects.create(
        user=user, request_type=request_type, details=details,
        jurisdiction=jurisdiction, ip_address=ip_address,
        due_at=_compute_due_at(jurisdiction),
    )
    PrivacyRequestEvent.objects.create(request=req, event_type="opened", note=details[:500])

    if request_type == PrivacyRequest.RequestType.EXPORT:
        _trigger_legacy_export(req, ip_address=ip_address)
    elif request_type == PrivacyRequest.RequestType.DELETE:
        _trigger_legacy_deletion(req, ip_address=ip_address)

    return req


def _trigger_legacy_export(req: PrivacyRequest, *, ip_address: str | None) -> None:
    """Create (or reuse) the legacy accounts.DataExportRequest row that
    actually generates the export file, link it to this ticket, and kick
    off the real Celery task — never a second, parallel implementation."""
    from apps.accounts.models_gdpr import DataExportRequest
    from apps.accounts.tasks_gdpr import generate_data_export

    existing = DataExportRequest.objects.filter(
        user=req.user, status__in=["pending", "processing"],
    ).first()
    if existing:
        if existing.privacy_request_id is None:
            existing.privacy_request = req
            existing.save(update_fields=["privacy_request"])
        PrivacyRequestEvent.objects.create(
            request=req, event_type="export_reused_existing",
            note=f"Reused in-flight export request {existing.pk}.",
        )
        return

    export_request = DataExportRequest.objects.create(
        user=req.user, ip_address=ip_address, privacy_request=req,
    )
    PrivacyRequestEvent.objects.create(
        request=req, event_type="export_triggered",
        note=f"Triggered accounts.DataExportRequest {export_request.pk}.",
    )
    generate_data_export.delay(str(export_request.id))


def _trigger_legacy_deletion(req: PrivacyRequest, *, ip_address: str | None) -> None:
    """Create (or reuse) the legacy accounts.AccountDeletionRequest row
    (OneToOne per user — only one grace-period deletion can ever be
    outstanding) and link it to this ticket. Does NOT call
    `process_account_deletion` immediately — that task only runs once the
    30-day grace period elapses, via the Celery Beat schedule (see
    `apps.accounts.tasks.execute_due_account_deletions`)."""
    from django.utils import timezone as _tz
    from apps.accounts.models_gdpr import AccountDeletionRequest

    existing = AccountDeletionRequest.objects.filter(
        user=req.user, status="pending",
    ).first()
    if existing:
        if existing.privacy_request_id is None:
            existing.privacy_request = req
            existing.save(update_fields=["privacy_request"])
        PrivacyRequestEvent.objects.create(
            request=req, event_type="deletion_reused_existing",
            note=f"Reused pending deletion request {existing.pk}, "
                 f"scheduled for {existing.scheduled_for.isoformat()}.",
        )
        return

    deletion_request = AccountDeletionRequest.objects.create(
        user=req.user, reason=req.details, ip_address=ip_address,
        scheduled_for=_tz.now() + _tz.timedelta(days=30),
        privacy_request=req,
    )
    PrivacyRequestEvent.objects.create(
        request=req, event_type="deletion_scheduled",
        note=f"Triggered accounts.AccountDeletionRequest {deletion_request.pk}, "
             f"scheduled for {deletion_request.scheduled_for.isoformat()}.",
    )


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
