"""Tests for CompanyDiscoveryService (Task #13 — Company Discovery Engine).

Covers: additive-only application (never overwrite a non-blank field),
conflict detection + flagging (never auto-resolve), confidence scoring, and
each of the four discovery methods (domain, careers_page_url, industry,
headquarters) using only data this platform already has (no network calls).
"""
from datetime import date

from django.test import TestCase

from apps.jobs.models import Company, CompanyEnrichment, CompanyResolutionIdentity, Job, Source
from apps.jobs.company_discovery import CompanyDiscoveryService


class DomainDiscoveryTests(TestCase):
    def setUp(self):
        self.service = CompanyDiscoveryService()
        self.company = Company.objects.create(name="Acme Corp", slug="acme-corp")

    def test_applies_domain_from_resolution_identity_when_blank(self):
        CompanyResolutionIdentity.objects.create(
            company=self.company, platform="greenhouse", tenant_slug="acme",
            domain="acme.com", matched_by="created", confidence=1.0,
        )
        outcomes = self.service.discover(self.company)
        self.company.refresh_from_db()
        self.assertEqual(self.company.domain, "acme.com")
        domain_outcome = next(o for o in outcomes if o.field_name == "domain")
        self.assertTrue(domain_outcome.applied)
        self.assertFalse(domain_outcome.conflict)

    def test_does_not_overwrite_existing_domain(self):
        self.company.domain = "acme-real.com"
        self.company.save(update_fields=["domain"])
        CompanyResolutionIdentity.objects.create(
            company=self.company, platform="greenhouse", tenant_slug="acme",
            domain="acme-different.com", matched_by="created", confidence=1.0,
        )
        self.service.discover(self.company)
        self.company.refresh_from_db()
        self.assertEqual(self.company.domain, "acme-real.com")  # unchanged

    def test_flags_conflict_when_evidence_disagrees_with_existing_value(self):
        self.company.domain = "acme-real.com"
        self.company.save(update_fields=["domain"])
        CompanyResolutionIdentity.objects.create(
            company=self.company, platform="greenhouse", tenant_slug="acme",
            domain="acme-different.com", matched_by="created", confidence=1.0,
        )
        outcomes = self.service.discover(self.company)
        domain_outcome = next(o for o in outcomes if o.field_name == "domain")
        self.assertFalse(domain_outcome.applied)
        self.assertTrue(domain_outcome.conflict)
        self.assertEqual(domain_outcome.evidence["existing_value"], "acme-real.com")

    def test_no_identity_means_no_outcome(self):
        outcomes = self.service.discover(self.company)
        self.assertEqual([o for o in outcomes if o.field_name == "domain"], [])

    def test_records_enrichment_row_even_when_not_applied(self):
        self.company.domain = "acme-real.com"
        self.company.save(update_fields=["domain"])
        CompanyResolutionIdentity.objects.create(
            company=self.company, platform="greenhouse", tenant_slug="acme",
            domain="acme-different.com", matched_by="created", confidence=1.0,
        )
        self.service.discover(self.company)
        rows = CompanyEnrichment.objects.filter(company=self.company, field_name="domain")
        self.assertEqual(rows.count(), 1)
        self.assertFalse(rows.first().applied)
        self.assertTrue(rows.first().conflict)


class CareersPageUrlDiscoveryTests(TestCase):
    def setUp(self):
        self.service = CompanyDiscoveryService()
        self.company = Company.objects.create(name="Beta Inc", slug="beta-inc")

    def test_derives_url_from_known_ats_template(self):
        CompanyResolutionIdentity.objects.create(
            company=self.company, platform="greenhouse", tenant_slug="beta",
            matched_by="created", confidence=1.0,
        )
        outcomes = self.service.discover(self.company)
        self.company.refresh_from_db()
        self.assertEqual(self.company.careers_page_url, "https://boards.greenhouse.io/beta")
        outcome = next(o for o in outcomes if o.field_name == "careers_page_url")
        self.assertTrue(outcome.applied)

    def test_unsupported_platform_produces_no_outcome(self):
        """workday/eightfold/jobvite/oracle/sap are per-tenant resolved, not
        slug-derivable - no URL guess should ever be fabricated for them."""
        CompanyResolutionIdentity.objects.create(
            company=self.company, platform="workday", tenant_slug="beta",
            matched_by="created", confidence=1.0,
        )
        outcomes = self.service.discover(self.company)
        self.assertEqual([o for o in outcomes if o.field_name == "careers_page_url"], [])


class IndustryDiscoveryTests(TestCase):
    def setUp(self):
        self.service = CompanyDiscoveryService()
        self.company = Company.objects.create(name="Gamma LLC", slug="gamma-llc")
        self.source = Source.objects.create(
            name="Gamma Greenhouse", slug="gamma-greenhouse",
            url="https://boards.greenhouse.io/gamma", ats_platform="greenhouse",
            industry="finance",
        )

    def _make_job(self, n):
        return Job.objects.create(
            title=f"Job {n}", slug=f"job-{n}-{self.company.slug}", company=self.company,
            location="Remote", location_type="remote", industry="technology",
            experience_level="mid", description="desc", source_url="https://x.com",
            source=self.source, posted_at=date.today(),
        )

    def test_backfills_industry_from_source_metadata(self):
        self._make_job(1)
        outcomes = self.service.discover(self.company)
        self.company.refresh_from_db()
        self.assertEqual(self.company.industry, "finance")
        outcome = next(o for o in outcomes if o.field_name == "industry")
        self.assertTrue(outcome.applied)

    def test_no_jobs_means_no_outcome(self):
        outcomes = self.service.discover(self.company)
        self.assertEqual([o for o in outcomes if o.field_name == "industry"], [])

    def test_blank_source_industry_excluded_from_vote(self):
        blank_source = Source.objects.create(
            name="No Industry Source", slug="no-industry-source",
            url="https://x.com", ats_platform="greenhouse", industry="",
        )
        Job.objects.create(
            title="Job X", slug=f"job-x-{self.company.slug}", company=self.company,
            location="Remote", location_type="remote", industry="technology",
            experience_level="mid", description="desc", source_url="https://x.com",
            source=blank_source, posted_at=date.today(),
        )
        outcomes = self.service.discover(self.company)
        self.assertEqual([o for o in outcomes if o.field_name == "industry"], [])


class HeadquartersDiscoveryTests(TestCase):
    def setUp(self):
        self.service = CompanyDiscoveryService()
        self.company = Company.objects.create(name="Delta Co", slug="delta-co")

    def _make_job(self, n, location):
        return Job.objects.create(
            title=f"Job {n}", slug=f"job-{n}-{self.company.slug}", company=self.company,
            location=location, location_type="onsite", industry="technology",
            experience_level="mid", description="desc", source_url="https://x.com",
            posted_at=date.today(),
        )

    def test_requires_minimum_sample_size(self):
        """Fewer than 3 jobs is too little evidence for a majority vote to
        mean anything - must decline rather than confidently guess."""
        self._make_job(1, "San Francisco, CA")
        self._make_job(2, "San Francisco, CA")
        outcomes = self.service.discover(self.company)
        self.assertEqual([o for o in outcomes if o.field_name == "headquarters"], [])

    def test_applies_true_majority_location(self):
        for i in range(4):
            self._make_job(i, "San Francisco, CA")
        self._make_job(5, "New York, NY")
        outcomes = self.service.discover(self.company)
        self.company.refresh_from_db()
        self.assertEqual(self.company.headquarters, "San Francisco, CA")
        outcome = next(o for o in outcomes if o.field_name == "headquarters")
        self.assertTrue(outcome.applied)
        self.assertLessEqual(outcome.confidence, 0.5)  # capped - weakest signal

    def test_no_true_majority_declines(self):
        """3-way split with no location holding >=50% - evidence too weak
        even to log as a weak signal."""
        self._make_job(1, "San Francisco, CA")
        self._make_job(2, "New York, NY")
        self._make_job(3, "Austin, TX")
        outcomes = self.service.discover(self.company)
        self.assertEqual([o for o in outcomes if o.field_name == "headquarters"], [])

    def test_confidence_always_capped_at_point_five(self):
        for i in range(10):
            self._make_job(i, "San Francisco, CA")
        outcomes = self.service.discover(self.company)
        outcome = next(o for o in outcomes if o.field_name == "headquarters")
        self.assertLessEqual(outcome.confidence, 0.5)


class DiscoveryEnrichmentPersistenceTests(TestCase):
    def test_discover_creates_one_enrichment_row_per_outcome(self):
        service = CompanyDiscoveryService()
        company = Company.objects.create(name="Epsilon", slug="epsilon")
        CompanyResolutionIdentity.objects.create(
            company=company, platform="greenhouse", tenant_slug="epsilon",
            domain="epsilon.com", matched_by="created", confidence=1.0,
        )
        service.discover(company)
        # domain + careers_page_url both resolve from this one identity
        self.assertEqual(CompanyEnrichment.objects.filter(company=company).count(), 2)

    def test_running_twice_is_idempotent_on_the_company_fields(self):
        """Re-running discovery after a field was already applied should not
        change it again (it's no longer blank) - though a fresh evidence row
        is still logged each run for audit purposes."""
        service = CompanyDiscoveryService()
        company = Company.objects.create(name="Zeta", slug="zeta")
        CompanyResolutionIdentity.objects.create(
            company=company, platform="greenhouse", tenant_slug="zeta",
            domain="zeta.com", matched_by="created", confidence=1.0,
        )
        service.discover(company)
        company.refresh_from_db()
        self.assertEqual(company.domain, "zeta.com")

        service.discover(company)  # second run
        company.refresh_from_db()
        self.assertEqual(company.domain, "zeta.com")  # still correct, not blanked/changed
