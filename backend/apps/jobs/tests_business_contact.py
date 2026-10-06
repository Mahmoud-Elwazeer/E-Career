"""Tests for BusinessContactService (Task #14 — Business Contact model).

Covers: deterministic role-pattern generation, idempotency, the generic-
role-prefix invariant (never a personal address), domain-match enforcement
on manual entries, and suppression semantics.
"""
from django.test import TestCase

from apps.jobs.models import BusinessContact, Company
from apps.jobs.business_contact import BusinessContactService, GENERIC_ROLE_PREFIXES


class GenerateForCompanyTests(TestCase):
    def setUp(self):
        self.service = BusinessContactService()
        self.company = Company.objects.create(name="Acme Corp", slug="acme-corp", domain="acme.com")

    def test_generates_all_default_role_addresses(self):
        outcomes = self.service.generate_for_company(self.company)
        self.assertEqual(len(outcomes), len(GENERIC_ROLE_PREFIXES))
        self.assertTrue(all(o.created for o in outcomes))
        emails = {o.email for o in outcomes}
        self.assertIn("careers@acme.com", emails)
        self.assertIn("hr@acme.com", emails)

    def test_no_domain_means_no_generation(self):
        bare = Company.objects.create(name="No Domain Co", slug="no-domain-co")
        outcomes = self.service.generate_for_company(bare)
        self.assertEqual(outcomes, [])

    def test_generated_contacts_are_unverified_with_low_confidence(self):
        self.service.generate_for_company(self.company, roles=["careers"])
        contact = BusinessContact.objects.get(company=self.company, email="careers@acme.com")
        self.assertFalse(contact.verified)
        self.assertEqual(contact.confidence, 0.3)
        self.assertEqual(contact.source, BusinessContact.SOURCE_PATTERN_GUESS)
        self.assertFalse(contact.is_do_not_contact)

    def test_rerun_is_idempotent_not_duplicated(self):
        self.service.generate_for_company(self.company, roles=["careers"])
        outcomes = self.service.generate_for_company(self.company, roles=["careers"])
        self.assertFalse(outcomes[0].created)
        self.assertEqual(
            BusinessContact.objects.filter(company=self.company, email="careers@acme.com").count(), 1,
        )

    def test_scoped_roles_only_generates_requested(self):
        outcomes = self.service.generate_for_company(self.company, roles=["careers", "hr"])
        self.assertEqual(len(outcomes), 2)

    def test_unknown_role_prefix_silently_skipped(self):
        """Defensive: a caller cannot sneak a non-generic (e.g. a person's
        name) through the roles parameter."""
        outcomes = self.service.generate_for_company(self.company, roles=["careers", "john.smith"])
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0].role_prefix, "careers")


class AddManualTests(TestCase):
    def setUp(self):
        self.service = BusinessContactService()
        self.company = Company.objects.create(name="Beta Inc", slug="beta-inc", domain="beta.com")

    def test_admin_manual_entry_is_verified(self):
        contact = self.service.add_manual(self.company, email="careers@beta.com", role_prefix="careers")
        self.assertTrue(contact.verified)
        self.assertEqual(contact.source, BusinessContact.SOURCE_ADMIN_MANUAL)
        self.assertEqual(contact.confidence, 1.0)
        self.assertIsNotNone(contact.verified_at)

    def test_rejects_non_generic_role_prefix(self):
        """The hard invariant: BusinessContact is never for a named personal
        contact, even via the admin-manual path."""
        with self.assertRaises(ValueError):
            self.service.add_manual(self.company, email="john@beta.com", role_prefix="john")

    def test_rejects_mismatched_domain(self):
        with self.assertRaises(ValueError):
            self.service.add_manual(self.company, email="careers@different-domain.com", role_prefix="careers")

    def test_manual_entry_can_be_unverified(self):
        contact = self.service.add_manual(
            self.company, email="hr@beta.com", role_prefix="hr", verified=False,
        )
        self.assertFalse(contact.verified)
        self.assertEqual(contact.confidence, 0.5)


class SuppressionTests(TestCase):
    def setUp(self):
        self.service = BusinessContactService()
        self.company = Company.objects.create(name="Gamma LLC", slug="gamma-llc", domain="gamma.com")
        self.contact = self.service.add_manual(self.company, email="careers@gamma.com", role_prefix="careers")

    def test_suppress_sets_do_not_contact_flag_and_reason(self):
        self.service.suppress(self.contact, reason="Bounced 3 times")
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.is_do_not_contact)
        self.assertEqual(self.contact.do_not_contact_reason, "Bounced 3 times")

    def test_regeneration_does_not_unsuppress(self):
        """A suppressed contact must never be silently reactivated by a
        later generate_for_company() re-run - re-run finds the existing row
        (unique constraint) and leaves it as-is."""
        self.service.suppress(self.contact, reason="Opted out")
        BusinessContactService().generate_for_company(self.company, roles=["careers"])
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.is_do_not_contact)


class ModelConstraintTests(TestCase):
    def test_unique_together_company_email(self):
        from django.db import IntegrityError, transaction
        company = Company.objects.create(name="Delta Co", slug="delta-co", domain="delta.com")
        BusinessContact.objects.create(
            company=company, email="careers@delta.com", role_prefix="careers",
            source=BusinessContact.SOURCE_PATTERN_GUESS,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BusinessContact.objects.create(
                    company=company, email="careers@delta.com", role_prefix="careers",
                    source=BusinessContact.SOURCE_PATTERN_GUESS,
                )
