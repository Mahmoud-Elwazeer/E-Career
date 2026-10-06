"""Outreach domain models (Task #15).

Company -> BusinessContact (apps.jobs) -> Campaign -> Template -> Message ->
Response. DRY_RUN only: there is no model, service method, or admin action
anywhere in this app that performs a real SMTP/API send. Every "send" this
app can do stops at `OutreachMessage.status = "dry_run_logged"` — a row
describing exactly what WOULD have been sent, to whom, and whether it was
blocked by a compliance gate first. See apps/outreach/service.py for the
gate chain (suppression -> rate limit -> render -> log) every message goes
through, and its module docstring for why DRY_RUN is enforced as a hardcoded
code-path absence rather than a settings flag that could be flipped later
without a corresponding code change.
"""
from django.conf import settings
from django.db import models

from apps.core.models import UUIDModel


class OutreachTemplate(UUIDModel):
    """A reusable message template. `{{company_name}}` / `{{contact_role}}`
    are the only substitution variables rendered (see service.py) -
    deliberately not a general templating engine, to keep what a template
    CAN say auditable at a glance."""

    name = models.CharField(max_length=150, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField(help_text="Supports {{company_name}} and {{contact_role}} only")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "outreach_template"
        ordering = ["name"]
        verbose_name = "Outreach Template"
        verbose_name_plural = "Outreach Templates"

    def __str__(self):
        return self.name


class OutreachCampaign(UUIDModel):
    """A named outreach effort using one template, scoped by a rate limit.

    STATUS_DRY_RUN is the only status that actually permits
    `OutreachService.send_message()` to log anything — DRAFT and PAUSED
    campaigns produce no messages at all. There is no "live"/"active" status
    in this implementation; promoting beyond DRY_RUN would require a future,
    deliberate, separately-reviewed change (real send infrastructure,
    deliverability setup, legal/compliance sign-off) — not a status flip.
    """

    STATUS_DRAFT = "draft"
    STATUS_DRY_RUN = "dry_run"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_DRY_RUN, "Dry Run"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_COMPLETED, "Completed"),
    ]

    name = models.CharField(max_length=150)
    template = models.ForeignKey(OutreachTemplate, on_delete=models.PROTECT, related_name="campaigns")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    rate_limit_per_day = models.IntegerField(
        default=50,
        help_text="Max messages this campaign may LOG (dry-run) per day - a real-world sending courtesy limit, enforced even in dry-run mode so campaign behavior is representative of what a real send would respect.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="outreach_campaigns",
    )

    class Meta:
        db_table = "outreach_campaign"
        ordering = ["-created_at"]
        verbose_name = "Outreach Campaign"
        verbose_name_plural = "Outreach Campaigns"

    def __str__(self):
        return f"{self.name} ({self.status})"


class OutreachSuppression(UUIDModel):
    """A permanent, email-level suppression - survives even if the
    originating BusinessContact row is deleted or regenerated. This is
    DELIBERATELY a separate list from BusinessContact.is_do_not_contact:
    that flag lives on one contact row and would be lost if the row were
    ever deleted and a fresh pattern-guess regenerated the same address;
    an unsubscribe or hard bounce must never be forgotten that way. Both
    are checked by OutreachService before any message is logged.
    """

    REASON_UNSUBSCRIBE = "unsubscribe"
    REASON_BOUNCE = "bounce"
    REASON_MANUAL = "manual"
    REASON_CHOICES = [
        (REASON_UNSUBSCRIBE, "Unsubscribed"),
        (REASON_BOUNCE, "Hard Bounce"),
        (REASON_MANUAL, "Manual Suppression"),
    ]

    email = models.EmailField(unique=True, db_index=True)
    reason = models.CharField(max_length=15, choices=REASON_CHOICES)
    detail = models.TextField(blank=True)

    class Meta:
        db_table = "outreach_suppression"
        ordering = ["-created_at"]
        verbose_name = "Outreach Suppression"
        verbose_name_plural = "Outreach Suppressions"

    def __str__(self):
        return f"{self.email} ({self.reason})"


class OutreachMessage(UUIDModel):
    """One (campaign, contact) attempt. In this implementation, EVERY
    message ends in either SUPPRESSED, RATE_LIMITED, or DRY_RUN_LOGGED —
    there is no SENT status, because there is no send code path. The
    rendered subject/body are stored so a reviewer can see EXACTLY what
    would have gone out, not just that something was attempted.
    """

    STATUS_DRY_RUN_LOGGED = "dry_run_logged"
    STATUS_SUPPRESSED = "suppressed"
    STATUS_RATE_LIMITED = "rate_limited"
    STATUS_CHOICES = [
        (STATUS_DRY_RUN_LOGGED, "Dry Run Logged"),
        (STATUS_SUPPRESSED, "Suppressed"),
        (STATUS_RATE_LIMITED, "Rate Limited"),
    ]

    campaign = models.ForeignKey(OutreachCampaign, on_delete=models.CASCADE, related_name="messages")
    contact = models.ForeignKey("jobs.BusinessContact", on_delete=models.CASCADE, related_name="outreach_messages")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    suppression_reason = models.CharField(max_length=200, blank=True)
    rendered_subject = models.CharField(max_length=200, blank=True)
    rendered_body = models.TextField(blank=True)

    class Meta:
        db_table = "outreach_message"
        ordering = ["-created_at"]
        verbose_name = "Outreach Message"
        verbose_name_plural = "Outreach Messages"
        indexes = [
            models.Index(fields=["campaign", "status"], name="outreach_msg_campaign_status_idx"),
        ]

    def __str__(self):
        return f"{self.contact.email} <- {self.campaign.name} ({self.status})"


class OutreachResponse(UUIDModel):
    """A recorded response to a (hypothetically sent, actually dry-run-
    logged) message — modeled for completeness of the domain shape
    (Company -> Contact -> Campaign -> Template -> Message -> Delivery ->
    Response) even though no real delivery exists yet to generate one from.
    In DRY_RUN mode this is populated only via admin/test fixtures, never by
    a real inbound-email webhook (none exists in this codebase)."""

    REPLY = "reply"
    BOUNCE = "bounce"
    UNSUBSCRIBE = "unsubscribe"
    RESPONSE_TYPE_CHOICES = [
        (REPLY, "Reply"),
        (BOUNCE, "Bounce"),
        (UNSUBSCRIBE, "Unsubscribe"),
    ]

    message = models.ForeignKey(OutreachMessage, on_delete=models.CASCADE, related_name="responses")
    response_type = models.CharField(max_length=15, choices=RESPONSE_TYPE_CHOICES)
    detail = models.TextField(blank=True)

    class Meta:
        db_table = "outreach_response"
        ordering = ["-created_at"]
        verbose_name = "Outreach Response"
        verbose_name_plural = "Outreach Responses"

    def __str__(self):
        return f"{self.message.contact.email} - {self.response_type}"
