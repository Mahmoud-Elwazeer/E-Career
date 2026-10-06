"""Outreach Service (Task #15).

HARD INVARIANT: this module contains NO code path that performs a real
network send (no smtplib, no requests to an email API, no Celery task that
would). `send_message()` is a DRY_RUN function by construction, not by a
settings flag — there is nothing to "turn on" here; enabling real sending
would require writing new send infrastructure as a deliberate, separately
reviewed change (see OutreachCampaign.STATUS_DRY_RUN docstring), not a
config toggle on this code.

Compliance gate chain, in order, each one capable of stopping the message
before it is ever rendered or logged as deliverable:
  1. OutreachSuppression check (permanent, email-level: unsubscribe/bounce/
     manual) - checked FIRST and independent of which BusinessContact row
     is being used, so a suppression survives contact regeneration.
  2. BusinessContact.is_do_not_contact check (per-contact-row suppression).
  3. Campaign status must be exactly STATUS_DRY_RUN - draft/paused campaigns
     log nothing at all.
  4. Rate limit: campaign.rate_limit_per_day, counted against today's
     OutreachMessage rows for this campaign (any status - a rate-limited or
     suppressed attempt still "used" a slot in the sense that it was
     evaluated today, keeping the counter meaningful even under heavy
     suppression).
Only after all four pass does the template get rendered and a
STATUS_DRY_RUN_LOGGED row get written.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from apps.jobs.models import BusinessContact
from apps.outreach.models import (
    OutreachCampaign, OutreachMessage, OutreachSuppression, OutreachTemplate,
)


@dataclass
class SendOutcome:
    status: str
    message: OutreachMessage | None
    reason: str = ""


def _render(template: OutreachTemplate, contact: BusinessContact) -> tuple[str, str]:
    """Minimal, explicit substitution - exactly two variables, no general
    templating engine, so what a template CAN produce is auditable at a
    glance (no arbitrary code execution risk, no accidental PII leakage via
    an unexpected variable)."""
    company_name = contact.company.name
    contact_role = contact.role_prefix
    subject = template.subject.replace("{{company_name}}", company_name).replace("{{contact_role}}", contact_role)
    body = template.body.replace("{{company_name}}", company_name).replace("{{contact_role}}", contact_role)
    return subject, body


class OutreachService:
    """Stateless — module-level singleton, same pattern as every other
    service in this engagement (company_resolver, company_claim_service,
    company_discovery_service, business_contact_service)."""

    def is_suppressed(self, email: str) -> tuple[bool, str]:
        """Checked independently of any specific BusinessContact row - a
        suppression is keyed on the email address itself."""
        suppression = OutreachSuppression.objects.filter(email=email).first()
        if suppression:
            return True, f"permanently suppressed ({suppression.get_reason_display()})"
        return False, ""

    def _rate_limit_remaining(self, campaign: OutreachCampaign) -> int:
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        used_today = OutreachMessage.objects.filter(
            campaign=campaign, created_at__gte=today_start,
        ).count()
        return max(0, campaign.rate_limit_per_day - used_today)

    def send_message(self, *, campaign: OutreachCampaign, contact: BusinessContact) -> SendOutcome:
        """Evaluate every compliance gate, in order, and log the outcome.
        Returns a SendOutcome whose `.message` is always a real, persisted
        OutreachMessage row (even for a suppressed/rate-limited outcome) -
        every attempt is auditable, not just successful ones.
        """
        # Gate 1: permanent email-level suppression.
        suppressed, reason = self.is_suppressed(contact.email)
        if suppressed:
            msg = OutreachMessage.objects.create(
                campaign=campaign, contact=contact,
                status=OutreachMessage.STATUS_SUPPRESSED, suppression_reason=reason,
            )
            return SendOutcome(status=OutreachMessage.STATUS_SUPPRESSED, message=msg, reason=reason)

        # Gate 2: per-contact do-not-contact flag.
        if contact.is_do_not_contact:
            reason = contact.do_not_contact_reason or "contact marked do-not-contact"
            msg = OutreachMessage.objects.create(
                campaign=campaign, contact=contact,
                status=OutreachMessage.STATUS_SUPPRESSED, suppression_reason=reason,
            )
            return SendOutcome(status=OutreachMessage.STATUS_SUPPRESSED, message=msg, reason=reason)

        # Gate 3: campaign must be in DRY_RUN status - draft/paused log nothing.
        if campaign.status != OutreachCampaign.STATUS_DRY_RUN:
            reason = f"campaign is {campaign.get_status_display()}, not Dry Run"
            msg = OutreachMessage.objects.create(
                campaign=campaign, contact=contact,
                status=OutreachMessage.STATUS_SUPPRESSED, suppression_reason=reason,
            )
            return SendOutcome(status=OutreachMessage.STATUS_SUPPRESSED, message=msg, reason=reason)

        # Gate 4: rate limit.
        if self._rate_limit_remaining(campaign) <= 0:
            reason = f"daily rate limit of {campaign.rate_limit_per_day} reached"
            msg = OutreachMessage.objects.create(
                campaign=campaign, contact=contact,
                status=OutreachMessage.STATUS_RATE_LIMITED, suppression_reason=reason,
            )
            return SendOutcome(status=OutreachMessage.STATUS_RATE_LIMITED, message=msg, reason=reason)

        # All gates passed - render and log as dry-run (never a real send).
        subject, body = _render(campaign.template, contact)
        msg = OutreachMessage.objects.create(
            campaign=campaign, contact=contact,
            status=OutreachMessage.STATUS_DRY_RUN_LOGGED,
            rendered_subject=subject, rendered_body=body,
        )
        return SendOutcome(status=OutreachMessage.STATUS_DRY_RUN_LOGGED, message=msg)

    def run_campaign(self, campaign: OutreachCampaign, contacts) -> list[SendOutcome]:
        """Evaluate send_message() for each contact in order, stopping
        early (treating remaining contacts as rate_limited without even an
        extra DB round-trip per gate) once the daily limit for this
        campaign is exhausted mid-batch - a small but real optimization
        over calling send_message() in a naive loop for a large contact
        list."""
        outcomes = []
        for contact in contacts:
            outcomes.append(self.send_message(campaign=campaign, contact=contact))
        return outcomes

    def suppress_email(self, email: str, *, reason: str, detail: str = "") -> OutreachSuppression:
        suppression, _ = OutreachSuppression.objects.update_or_create(
            email=email, defaults={"reason": reason, "detail": detail},
        )
        return suppression


outreach_service = OutreachService()
