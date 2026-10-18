"""
Legal / Privacy / Consent domain models.

Backing store for the USAM Legal Center, cookie consent system, DSR
(Data Subject Request) workflow, retention/processor/transfer registers, and
the Admin Legal Control Plane. Built against verified, officially-sourced
facts about Egypt's Personal Data Protection Law (Law No. 151 of 2020 + the
Executive Regulations issued by Ministerial Decree No. 816 of 2025) and
Saudi Arabia's Personal Data Protection Law (Royal Decree M/19, amended
M/148, SDAIA Implementing Regulations) — see
``audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md`` for citations.

Hard rules enforced by convention across this app (directive non-negotiables):
  - Never claim full/100%/PCI/GDPR "compliance" in any seeded copy.
  - Any legal fact this codebase cannot verify (entity name, SLA number,
    minors' age threshold, etc.) is stored as NULL/blank with a
    ``requires_legal_review`` flag — never invented.
  - Policy content is versioned and NEVER overwritten; a new PolicyVersion
    row is the only way to change what's live.
  - All consent/acceptance/DSR actions are audit-logged (this app's own
    tables double as the audit trail — no raw card or payment data ever
    enters this app).
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel


# ── Shared choices ───────────────────────────────────────────────────────────

class Jurisdiction(models.TextChoices):
    EGYPT = "EG", "Egypt"
    SAUDI_ARABIA = "SA", "Saudi Arabia"
    OTHER = "OTHER", "Other / Unspecified"


# ── Policy lifecycle ─────────────────────────────────────────────────────────

class PolicyDocument(UUIDModel):
    """A legal document family (Terms, Privacy, Cookies, Refunds, ...).

    One row per document TYPE. The actual legal text lives in versioned
    ``PolicyVersion`` children — this row is just the stable identity/slug
    that public routes (``/legal/<slug>``) and acceptance records point to.
    """

    class DocType(models.TextChoices):
        TERMS = "terms", "Terms of Service"
        PRIVACY = "privacy", "Privacy Policy"
        COOKIES = "cookies", "Cookie Policy"
        REFUNDS = "refunds", "Refund & Cancellation Policy"
        PAYMENT_SECURITY = "payment_security", "Payment & Card Security Policy"
        SECURITY = "security", "Security Overview"
        AI_DISCLOSURE = "ai_disclosure", "AI Use & Rasheed Disclosure"
        # Added in the 2026-09-21 continuation pass to close real route/
        # disclosure gaps identified against the supplemental legal specs
        # (see audit/LEGAL_PRIVACY_COMPLIANCE_MASTER.md §9A, continuation
        # entry). Each is a genuinely distinct disclosure, not a duplicate
        # of an existing document — see the seed command's own docstring
        # for why each one exists and what it does NOT repeat.
        ACCEPTABLE_USE = "acceptable_use", "Acceptable Use Policy"
        DATA_RIGHTS = "data_rights", "Your Data Rights"
        SUBPROCESSORS = "subprocessors", "Sub-processor Disclosure"
        INTERNATIONAL_TRANSFERS = "international_transfers", "International Data Transfers"
        CANDIDATE_PRIVACY = "candidate_privacy", "Candidate Privacy Notice"
        BUSINESS_TERMS = "business_terms", "Employer & Business Terms"

    slug = models.SlugField(max_length=60, unique=True)
    doc_type = models.CharField(max_length=30, choices=DocType.choices, db_index=True)
    title = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "legal_policy_document"
        ordering = ["doc_type"]

    def __str__(self):
        return self.title

    @property
    def live_version(self):
        return self.versions.filter(status=PolicyVersion.Status.ACTIVE).order_by("-effective_at").first()


class PolicyVersion(UUIDModel):
    """One immutable version of a policy document's text.

    Lifecycle (directive-mandated, enforced by this ``status`` field, not by
    overwriting rows): DRAFT -> IN_REVIEW -> APPROVED -> SCHEDULED -> ACTIVE ->
    RETIRED. Only ONE version per (document, locale, jurisdiction) may be
    ACTIVE at a time — enforced in ``services.activate_version``, not at the
    DB level, so a migration can't silently violate it.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_REVIEW = "in_review", "In review"
        APPROVED = "approved", "Approved"
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE = "active", "Active"
        RETIRED = "retired", "Retired"

    document = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE, related_name="versions")
    version_label = models.CharField(max_length=30, help_text="e.g. '2026.1' — human-facing, never reused")
    locale = models.CharField(max_length=10, default="en", db_index=True)
    jurisdiction = models.CharField(max_length=10, choices=Jurisdiction.choices,
                                    default=Jurisdiction.OTHER, db_index=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)

    # Content: Markdown. Rendered client-side through a sanitizing renderer —
    # never injected as raw HTML (XSS guard for admin-authored legal text).
    content_markdown = models.TextField(blank=True)
    summary_of_changes = models.TextField(
        blank=True, help_text="What changed vs. the previous active version (shown to re-accepting users).",
    )
    material_change = models.BooleanField(
        default=False,
        help_text="If True, previously-accepted users must re-accept this version.",
    )
    is_machine_translated = models.BooleanField(
        default=False,
        help_text="True if this locale's text came from unreviewed machine translation (directive: must be flagged, not silently presented as official).",
    )

    effective_at = models.DateTimeField(null=True, blank=True, db_index=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="legal_versions_created")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="legal_versions_approved")

    class Meta:
        db_table = "legal_policy_version"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_label", "locale"],
                name="uniq_policy_version_label_locale",
            )
        ]

    def __str__(self):
        return f"{self.document.slug} v{self.version_label} ({self.locale}/{self.jurisdiction}) [{self.status}]"


class PolicyAcceptance(UUIDModel):
    """Immutable record that a user accepted a specific policy version.

    Never updated after creation — withdrawal/re-acceptance is a NEW row,
    not a mutation, so the acceptance history itself is auditable.
    """

    class Method(models.TextChoices):
        SIGNUP = "signup", "At signup"
        REACCEPTANCE_PROMPT = "reacceptance_prompt", "Re-acceptance prompt (material change)"
        CHECKOUT = "checkout", "At checkout"
        SETTINGS = "settings", "From account settings"
        ADMIN = "admin", "Recorded by admin"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="legal_acceptances")
    policy_version = models.ForeignKey(PolicyVersion, on_delete=models.PROTECT,
                                       related_name="acceptances")
    method = models.CharField(max_length=24, choices=Method.choices, default=Method.SIGNUP)
    accepted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "legal_policy_acceptance"
        ordering = ["-accepted_at"]
        indexes = [models.Index(fields=["user", "policy_version"])]

    def __str__(self):
        return f"{self.user_id} accepted {self.policy_version} at {self.accepted_at}"


# ── Consent (separate from Terms — directive non-negotiable) ────────────────

class ConsentPurpose(UUIDModel):
    """An admin-defined, independently-withdrawable purpose for processing.

    Terms-of-service acceptance is NOT consent. Marketing, Talent Pool
    visibility, and cookie categories are each their own ConsentPurpose so one
    can be withdrawn without affecting the others.
    """

    class Category(models.TextChoices):
        MARKETING_EMAIL = "marketing_email", "Marketing emails"
        MARKETING_SMS = "marketing_sms", "Marketing SMS"
        TALENT_POOL = "talent_pool", "Talent Pool visibility"
        AI_PROCESSING = "ai_processing", "AI-assisted processing (Rasheed, matching)"
        COOKIE_ANALYTICS = "cookie_analytics", "Analytics cookies"
        COOKIE_MARKETING = "cookie_marketing", "Marketing cookies"
        COOKIE_FUNCTIONAL = "cookie_functional", "Functional cookies"
        OTHER = "other", "Other"

    key = models.SlugField(max_length=60, unique=True)
    category = models.CharField(max_length=24, choices=Category.choices, db_index=True)
    label = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(
        default=False,
        help_text="If True this purpose cannot be declined (e.g. necessary cookies). "
                  "Directive: necessary cookies must never block login or be gated.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "legal_consent_purpose"
        ordering = ["category", "key"]

    def __str__(self):
        return self.label


class ConsentRecord(UUIDModel):
    """Current + historical state of a user's consent for one purpose.

    A withdrawal creates a NEW row (status=WITHDRAWN) rather than mutating the
    grant row, so the full history survives for audit. ``current_for(user,
    purpose)`` style lookups should order by -created_at and take the first.
    """

    class Status(models.TextChoices):
        GRANTED = "granted", "Granted"
        WITHDRAWN = "withdrawn", "Withdrawn"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="consent_records")
    purpose = models.ForeignKey(ConsentPurpose, on_delete=models.PROTECT, related_name="records")
    status = models.CharField(max_length=10, choices=Status.choices, db_index=True)
    policy_version = models.ForeignKey(PolicyVersion, null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="consent_records")
    method = models.CharField(max_length=24, blank=True, help_text="signup | settings | privacy_center | admin")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "legal_consent_record"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "purpose", "created_at"])]

    def __str__(self):
        return f"{self.user_id}/{self.purpose.key} -> {self.status}"


class MarketingPreference(UUIDModel):
    """Marketing-vs-transactional email/SMS split (directive: never bundle).

    Deliberately separate from ``notifications.NotificationPreference``,
    which governs transactional/product notifications. Transactional mail
    (password reset, application status, etc.) is never gated by this model.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="marketing_preference")
    email_marketing_opt_in = models.BooleanField(default=False)
    sms_marketing_opt_in = models.BooleanField(default=False)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legal_marketing_preference"

    def __str__(self):
        return f"{self.user_id} marketing(email={self.email_marketing_opt_in}, sms={self.sms_marketing_opt_in})"


# ── Cookie consent ───────────────────────────────────────────────────────────

class CookieCategory(UUIDModel):
    """Admin-configured cookie category shown in the consent banner/manager."""

    class Key(models.TextChoices):
        NECESSARY = "necessary", "Strictly necessary"
        FUNCTIONAL = "functional", "Functional"
        ANALYTICS = "analytics", "Analytics"
        MARKETING = "marketing", "Marketing"

    key = models.CharField(max_length=20, choices=Key.choices, unique=True)
    label = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_essential = models.BooleanField(
        default=False,
        help_text="Essential categories are always on and cannot be rejected (necessary only).",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "legal_cookie_category"
        ordering = ["key"]

    def __str__(self):
        return self.label


class CookieConsent(UUIDModel):
    """A visitor's cookie preference snapshot — versioned to the active
    Cookie Policy so a later policy change can require re-prompting.

    Supports BOTH authenticated users (``user`` set) and anonymous visitors
    (``session_key`` set, no FK) since the banner must work pre-login and
    necessary cookies must never require authentication to function.
    """

    class Action(models.TextChoices):
        ACCEPT_ALL = "accept_all", "Accept all"
        REJECT_NON_ESSENTIAL = "reject_non_essential", "Reject non-essential"
        CUSTOM = "custom", "Manage preferences (custom)"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.CASCADE, related_name="cookie_consents")
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    policy_version = models.ForeignKey(PolicyVersion, null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="cookie_consents")
    action = models.CharField(max_length=24, choices=Action.choices)
    # {"necessary": true, "functional": bool, "analytics": bool, "marketing": bool}
    categories = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # Provenance for anonymous->authenticated carryover (directive item 6):
    # when a user logs in and we carry their most recent anonymous cookie
    # choice forward into a new authenticated-user row (rather than making
    # them re-choose), this records exactly which anonymous session_key the
    # choice came from. Blank for every row created directly by a visitor's
    # own banner interaction — only set on the synthetic carryover row.
    carried_over_from_session_key = models.CharField(
        max_length=64, blank=True,
        help_text="If this row was carried over from an anonymous session at "
                  "login (rather than chosen directly by this authenticated "
                  "user), the originating session_key. Blank otherwise.",
    )

    class Meta:
        db_table = "legal_cookie_consent"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["session_key", "created_at"]),
        ]

    def __str__(self):
        who = self.user_id or self.session_key or "anon"
        return f"cookie-consent[{who}] {self.action}"


# ── Data Subject Requests (DSR) ──────────────────────────────────────────────

class PrivacyRequest(UUIDModel):
    """A data-subject rights request (access/correction/deletion/etc.).

    SLA (``due_at``) is computed from the user's declared/resolved
    jurisdiction via ``JurisdictionPolicyProfile.dsr_sla_days`` — never
    hardcoded here, and left NULL (with ``requires_legal_review``) when the
    jurisdiction's SLA hasn't been configured yet.
    """

    class RequestType(models.TextChoices):
        ACCESS = "access", "Access my data"
        EXPORT = "export", "Export my data (portability)"
        CORRECT = "correct", "Correct my data"
        DELETE = "delete", "Delete my data"
        RESTRICT = "restrict", "Restrict processing"
        OBJECT = "object", "Object to processing"
        WITHDRAW_CONSENT = "withdraw_consent", "Withdraw consent"
        OPT_OUT = "opt_out", "Opt out of marketing/profiling"
        COMPLAINT = "complaint", "Complaint"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_REVIEW = "in_review", "In review"
        ACTION_REQUIRED = "action_required", "Action required (needs more info)"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled by user"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="privacy_requests")
    request_type = models.CharField(max_length=20, choices=RequestType.choices, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    jurisdiction = models.CharField(max_length=10, choices=Jurisdiction.choices,
                                    default=Jurisdiction.OTHER)
    details = models.TextField(blank=True)
    resolution_note = models.TextField(blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="privacy_requests_resolved")
    due_at = models.DateTimeField(
        null=True, blank=True,
        help_text="SLA deadline from JurisdictionPolicyProfile; null if SLA not yet configured.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "legal_privacy_request"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_request_type_display()} — {self.user_id} [{self.status}]"


class PrivacyRequestEvent(UUIDModel):
    """Append-only audit trail for a PrivacyRequest's lifecycle."""

    request = models.ForeignKey(PrivacyRequest, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="privacy_request_events")
    event_type = models.CharField(max_length=40)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "legal_privacy_request_event"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.request_id}: {self.event_type}"


class DataExportJob(UUIDModel):
    """A legal-app-tracked export tied to a specific DSR (not the full-account
    export already handled by ``accounts.DataExportRequest`` — this exists for
    export requests scoped to a DSR ticket so the Privacy Center queue has one
    place to show status across every export flow)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"

    privacy_request = models.OneToOneField(PrivacyRequest, on_delete=models.CASCADE,
                                            related_name="export_job")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    file_path = models.CharField(max_length=500, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "legal_data_export_job"


class DeletionJob(UUIDModel):
    """A legal-app-tracked deletion execution tied to a DSR ticket.

    Mirrors ``accounts.AccountDeletionRequest``'s grace-period pattern for
    deletion requests that are SCOPED (e.g. "delete my CV" / "delete my
    interview transcripts") rather than full-account deletion.
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        BLOCKED = "blocked", "Blocked (active legal hold)"
        EXECUTED = "executed", "Executed"
        CANCELLED = "cancelled", "Cancelled"

    privacy_request = models.OneToOneField(PrivacyRequest, on_delete=models.CASCADE,
                                           related_name="deletion_job")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)
    scope_description = models.TextField(help_text="What data categories this deletion covers.")
    scheduled_for = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result_summary = models.TextField(blank=True)

    class Meta:
        db_table = "legal_deletion_job"


# ── Retention / holds / processors / transfers ───────────────────────────────

class RetentionPolicy(UUIDModel):
    """Declared retention period for one data category.

    ``retention_period_days`` is left NULL with ``requires_legal_review=True``
    until a real figure is confirmed — the directive forbids inventing
    retention numbers. Seeded rows for this platform mark categories with
    genuinely unknown periods (e.g. interview transcripts — see audit) as
    unconfigured rather than guessing.
    """

    data_category = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    retention_period_days = models.PositiveIntegerField(null=True, blank=True)
    legal_basis = models.CharField(max_length=255, blank=True)
    requires_legal_review = models.BooleanField(default=True)
    jurisdiction = models.CharField(max_length=10, choices=Jurisdiction.choices,
                                    default=Jurisdiction.OTHER)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "legal_retention_policy"
        ordering = ["data_category"]

    def __str__(self):
        days = self.retention_period_days
        return f"{self.data_category}: {days}d" if days else f"{self.data_category}: UNCONFIGURED"


class LegalHold(UUIDModel):
    """An active hold that blocks deletion/anonymization for a scope
    (e.g. a user under investigation, or data subject to a legal claim).
    ``DeletionJob``/account-deletion tasks should check for an active hold
    before executing (not yet wired into every deletion path — tracked as a
    known gap in the master doc until all deletion flows consult it).
    """

    reference = models.CharField(max_length=60, unique=True)
    scope_description = models.TextField()
    reason = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="legal_holds")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="legal_holds_created")
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "legal_hold"
        ordering = ["-created_at"]

    @property
    def is_active(self) -> bool:
        return self.released_at is None

    def __str__(self):
        return f"{self.reference} ({'active' if self.is_active else 'released'})"


class ProcessorRecord(UUIDModel):
    """A sub-processor / vendor that processes personal data on USAM's
    behalf (e.g. AWS, Stripe). Admin-maintained register — directive forbids
    inventing contract/DPA facts, so ``dpa_signed``/``contract_reference``
    default to unknown/blank until legal confirms them.
    """

    name = models.CharField(max_length=160)
    purpose = models.TextField(blank=True)
    data_categories = models.TextField(blank=True, help_text="Comma-separated or free text")
    country = models.CharField(max_length=80, blank=True)
    contract_reference = models.CharField(max_length=160, blank=True)
    dpa_signed = models.BooleanField(null=True, blank=True, help_text="NULL = not yet confirmed by legal")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legal_processor_record"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DataTransferRecord(UUIDModel):
    """A declared cross-border transfer of personal data, with the safeguard
    mechanism relied upon. Egypt requires PDPC authorization + consent for
    every outbound transfer (Art. 15 / Executive Regs Art. 16); Saudi PDPL
    requires an approved safeguard (SCC/BCR/adequacy/consent) per SDAIA's
    Transfer Regulation. This register does not assert any transfer is
    currently authorized — ``authorization_reference`` is blank until legal
    confirms it.
    """

    class Mechanism(models.TextChoices):
        SCC = "scc", "Standard Contractual Clauses"
        BCR = "bcr", "Binding Common Rules"
        ADEQUACY = "adequacy", "Adequacy decision"
        CONSENT = "consent", "Explicit data-subject consent"
        UNKNOWN = "unknown", "Not yet determined — REQUIRES LEGAL REVIEW"

    processor = models.ForeignKey(ProcessorRecord, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name="transfers")
    destination_country = models.CharField(max_length=80)
    data_categories = models.TextField(blank=True)
    mechanism = models.CharField(max_length=10, choices=Mechanism.choices, default=Mechanism.UNKNOWN)
    authorization_reference = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legal_data_transfer_record"
        ordering = ["destination_country"]

    def __str__(self):
        return f"-> {self.destination_country} ({self.mechanism})"


class JurisdictionPolicyProfile(UUIDModel):
    """Per-jurisdiction legal facts that drive SLAs/behavior elsewhere in the
    app (DSR due dates, breach notification windows). Values are seeded from
    officially-sourced research; anything not yet confirmed is left NULL with
    ``requires_legal_review=True`` rather than guessed.
    """

    jurisdiction = models.CharField(max_length=10, choices=Jurisdiction.choices, unique=True)
    regulator_name = models.CharField(max_length=160, blank=True)
    law_name = models.CharField(max_length=200, blank=True)
    dsr_sla_days = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Working/calendar days to respond to a data-subject rights request.",
    )
    breach_notification_hours = models.PositiveIntegerField(null=True, blank=True)
    minor_age_threshold = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Age below which guardian consent is required. Left NULL until "
                  "legal confirms a platform-applicable threshold — never invented.",
    )
    requires_legal_review = models.BooleanField(default=True)
    source_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legal_jurisdiction_profile"
        ordering = ["jurisdiction"]

    def __str__(self):
        return self.get_jurisdiction_display()


class IncidentReport(UUIDModel):
    """A security/privacy incident (breach) record and its notification
    workflow. Admin-only. No card data is ever stored here (payments app
    already guarantees PANs/CVVs never reach USAM at all).
    """

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CONTAINED = "contained", "Contained"
        REGULATOR_NOTIFIED = "regulator_notified", "Regulator notified"
        USERS_NOTIFIED = "users_notified", "Users notified"
        CLOSED = "closed", "Closed"

    reference = models.CharField(max_length=60, unique=True)
    summary = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.LOW)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OPEN, db_index=True)
    affected_data_categories = models.TextField(blank=True)
    affected_user_count = models.PositiveIntegerField(null=True, blank=True)
    detected_at = models.DateTimeField()
    regulator_notified_at = models.DateTimeField(null=True, blank=True)
    users_notified_at = models.DateTimeField(null=True, blank=True)
    remediation = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="legal_incidents_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legal_incident_report"
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.reference} [{self.severity}/{self.status}]"


class AIProcessingDisclosure(UUIDModel):
    """Admin-maintained register of AI touchpoints that process personal
    data (Rasheed chat, interview voice analysis, matching/scoring). Each
    entry documents what the feature does and the directive-mandated
    boundary that AI assists but does not make final hiring decisions —
    enforced here as DATA (so Legal/Admin can audit and update the wording),
    not as a hardcoded claim scattered across the frontend.
    """

    feature_key = models.SlugField(max_length=60, unique=True)
    feature_label = models.CharField(max_length=160)
    description = models.TextField()
    data_categories_used = models.TextField(blank=True)
    makes_final_decision = models.BooleanField(
        default=False,
        help_text="Must be False for hiring-adjacent features per directive — AI assists, humans decide.",
    )
    retention_note = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "legal_ai_processing_disclosure"
        ordering = ["feature_key"]

    def __str__(self):
        return self.feature_label


class LegalEntityConfig(UUIDModel):
    """Singleton: the real legal entity + contact info shown on invoices,
    the footer, and the Legal Center. Every field starts blank/unconfigured
    — the directive forbids inventing a company name, address, or VAT/tax
    ID. ``is_configured`` is a convenience flag the frontend/admin can check
    to show a 'REQUIRES LEGAL REVIEW / CONFIGURATION' banner instead of
    silently rendering blanks as if they were real.
    """

    legal_entity_name = models.CharField(max_length=200, blank=True)
    registered_address = models.TextField(blank=True)
    tax_or_registration_id = models.CharField(max_length=100, blank=True)
    dpo_name = models.CharField(max_length=160, blank=True)
    dpo_email = models.EmailField(blank=True)
    privacy_contact_email = models.EmailField(blank=True)
    support_contact_email = models.EmailField(blank=True)
    default_refund_window_days = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Configurable refund window shown in the Refund Policy. "
                  "NULL until a real policy figure is confirmed — never hardcode 14 days.",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="legal_entity_config_edits")

    class Meta:
        db_table = "legal_entity_config"
        verbose_name = "Legal Entity Configuration"
        verbose_name_plural = "Legal Entity Configuration"

    def __str__(self):
        return self.legal_entity_name or "Legal entity (not yet configured)"

    @property
    def is_configured(self) -> bool:
        return bool(self.legal_entity_name and self.registered_address and self.privacy_contact_email)

    @classmethod
    def load(cls) -> "LegalEntityConfig":
        """Return the singleton row, creating an empty (unconfigured) one if
        none exists yet. Never fabricates values — every field starts blank."""
        obj = cls.objects.order_by("created_at").first()
        if obj is None:
            obj = cls.objects.create()
        return obj
