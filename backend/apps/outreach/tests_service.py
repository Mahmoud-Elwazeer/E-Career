"""Tests for OutreachService (Task #15 — Outreach domain scaffolding).

Covers the full compliance gate chain in order (suppression -> do-not-
contact -> campaign status -> rate limit), proves NOTHING is ever sent for
real (every outcome lands in dry_run_logged/suppressed/rate_limited, never a
"sent" status - because that status does not exist in this implementation),
and template rendering.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.jobs.models import BusinessContact, Company
from apps.outreach.models import (
    OutreachCampaign, OutreachMessage, OutreachSuppression, OutreachTemplate,
)
from apps.outreach.service import OutreachService

User = get_user_model()


class OutreachServiceTests(TestCase):
    def setUp(self):
        self.service = OutreachService()
        self.company = Company.objects.create(name="Acme Corp", slug="acme-corp", domain="acme.com")
        self.contact = BusinessContact.objects.create(
            company=self.company, email="careers@acme.com", role_prefix="careers",
            source=BusinessContact.SOURCE_PATTERN_GUESS, confidence=0.3,
        )
        self.template = OutreachTemplate.objects.create(
            name="Intro", subject="Hello {{company_name}}",
            body="Hi {{contact_role}} team at {{company_name}}, ...",
        )
        self.campaign = OutreachCampaign.objects.create(
            name="Q4 Outreach", template=self.template,
            status=OutreachCampaign.STATUS_DRY_RUN, rate_limit_per_day=50,
        )

    def test_happy_path_logs_dry_run_with_rendered_content(self):
        outcome = self.service.send_message(campaign=self.campaign, contact=self.contact)
        self.assertEqual(outcome.status, OutreachMessage.STATUS_DRY_RUN_LOGGED)
        self.assertEqual(outcome.message.rendered_subject, "Hello Acme Corp")
        self.assertIn("careers team at Acme Corp", outcome.message.rendered_body)

    def test_no_sent_status_exists_anywhere_in_the_model(self):
        """Hard proof there is no 'sent' outcome possible - every valid
        status choice is dry_run_logged/suppressed/rate_limited."""
        valid_statuses = {s[0] for s in OutreachMessage.STATUS_CHOICES}
        self.assertEqual(valid_statuses, {"dry_run_logged", "suppressed", "rate_limited"})

    def test_gate1_permanent_suppression_blocks_before_rendering(self):
        OutreachSuppression.objects.create(email="careers@acme.com", reason=OutreachSuppression.REASON_UNSUBSCRIBE)
        outcome = self.service.send_message(campaign=self.campaign, contact=self.contact)
        self.assertEqual(outcome.status, OutreachMessage.STATUS_SUPPRESSED)
        self.assertIn("unsubscribed", outcome.reason.lower())
        self.assertEqual(outcome.message.rendered_subject, "")  # never rendered

    def test_gate2_do_not_contact_flag_blocks(self):
        self.contact.is_do_not_contact = True
        self.contact.do_not_contact_reason = "bounced 3 times"
        self.contact.save()
        outcome = self.service.send_message(campaign=self.campaign, contact=self.contact)
        self.assertEqual(outcome.status, OutreachMessage.STATUS_SUPPRESSED)
        self.assertEqual(outcome.reason, "bounced 3 times")

    def test_gate3_non_dry_run_campaign_status_blocks(self):
        self.campaign.status = OutreachCampaign.STATUS_DRAFT
        self.campaign.save()
        outcome = self.service.send_message(campaign=self.campaign, contact=self.contact)
        self.assertEqual(outcome.status, OutreachMessage.STATUS_SUPPRESSED)
        self.assertIn("Draft", outcome.reason)

    def test_paused_campaign_also_blocks(self):
        self.campaign.status = OutreachCampaign.STATUS_PAUSED
        self.campaign.save()
        outcome = self.service.send_message(campaign=self.campaign, contact=self.contact)
        self.assertEqual(outcome.status, OutreachMessage.STATUS_SUPPRESSED)

    def test_gate4_rate_limit_blocks_after_limit_reached(self):
        self.campaign.rate_limit_per_day = 1
        self.campaign.save()
        contact2 = BusinessContact.objects.create(
            company=self.company, email="hr@acme.com", role_prefix="hr",
            source=BusinessContact.SOURCE_PATTERN_GUESS,
        )
        first = self.service.send_message(campaign=self.campaign, contact=self.contact)
        second = self.service.send_message(campaign=self.campaign, contact=contact2)
        self.assertEqual(first.status, OutreachMessage.STATUS_DRY_RUN_LOGGED)
        self.assertEqual(second.status, OutreachMessage.STATUS_RATE_LIMITED)

    def test_every_attempt_is_persisted_even_when_blocked(self):
        """Every gate outcome - including a block - still creates a real,
        auditable OutreachMessage row."""
        OutreachSuppression.objects.create(email="careers@acme.com", reason=OutreachSuppression.REASON_BOUNCE)
        before = OutreachMessage.objects.count()
        self.service.send_message(campaign=self.campaign, contact=self.contact)
        self.assertEqual(OutreachMessage.objects.count(), before + 1)

    def test_run_campaign_evaluates_each_contact(self):
        contact2 = BusinessContact.objects.create(
            company=self.company, email="hr@acme.com", role_prefix="hr",
            source=BusinessContact.SOURCE_PATTERN_GUESS,
        )
        outcomes = self.service.run_campaign(self.campaign, [self.contact, contact2])
        self.assertEqual(len(outcomes), 2)
        self.assertTrue(all(o.status == OutreachMessage.STATUS_DRY_RUN_LOGGED for o in outcomes))

    def test_suppress_email_is_idempotent(self):
        self.service.suppress_email("test@example.com", reason=OutreachSuppression.REASON_MANUAL, detail="requested")
        self.service.suppress_email("test@example.com", reason=OutreachSuppression.REASON_BOUNCE, detail="updated")
        self.assertEqual(OutreachSuppression.objects.filter(email="test@example.com").count(), 1)
        suppression = OutreachSuppression.objects.get(email="test@example.com")
        self.assertEqual(suppression.reason, OutreachSuppression.REASON_BOUNCE)  # latest wins


class SuppressionIndependentOfContactRowTests(TestCase):
    """Proves OutreachSuppression survives even if the originating
    BusinessContact row is deleted and regenerated with the same email -
    the exact scenario the model docstring explains is why this is a
    separate list from BusinessContact.is_do_not_contact."""

    def test_suppression_blocks_a_freshly_regenerated_contact_with_same_email(self):
        service = OutreachService()
        company = Company.objects.create(name="Beta Inc", slug="beta-inc", domain="beta.com")
        old_contact = BusinessContact.objects.create(
            company=company, email="careers@beta.com", role_prefix="careers",
            source=BusinessContact.SOURCE_PATTERN_GUESS,
        )
        service.suppress_email("careers@beta.com", reason=OutreachSuppression.REASON_UNSUBSCRIBE)
        old_contact.delete()

        # Regenerate the exact same address as a brand-new row.
        new_contact = BusinessContact.objects.create(
            company=company, email="careers@beta.com", role_prefix="careers",
            source=BusinessContact.SOURCE_PATTERN_GUESS,
        )
        self.assertFalse(new_contact.is_do_not_contact)  # the NEW row knows nothing of the old suppression

        template = OutreachTemplate.objects.create(name="T", subject="S", body="B")
        campaign = OutreachCampaign.objects.create(
            name="C", template=template, status=OutreachCampaign.STATUS_DRY_RUN,
        )
        outcome = service.send_message(campaign=campaign, contact=new_contact)
        self.assertEqual(outcome.status, OutreachMessage.STATUS_SUPPRESSED)  # still blocked, via the email-level list
