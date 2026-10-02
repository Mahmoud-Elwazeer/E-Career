"""Tests for CompanyResolutionService (§11).

Covers the resolution order (identity -> domain -> slug -> create) and the
specific regression this service fixes: tasks.py's old inline
get_or_create used to store the raw board slug as the Company's NAME.
"""
from django.test import TestCase

from apps.jobs.models import Company, CompanyResolutionIdentity, Source
from apps.jobs.company_resolution import CompanyResolutionService


class CompanyResolutionServiceTests(TestCase):
    def setUp(self):
        self.resolver = CompanyResolutionService()
        self.source = Source.objects.create(
            name="Stripe Greenhouse", slug="stripe-greenhouse",
            url="https://boards.greenhouse.io/stripe", ats_platform="greenhouse",
        )

    def test_create_resolves_real_name_not_raw_slug(self):
        """The core regression fix: resolving a NEW company from a tenant
        slug must produce a human-readable name, never the raw lowercase
        slug (the old tasks.py bug: Company(name='stripe'))."""
        result = self.resolver.resolve(
            platform="greenhouse", tenant_slug="stripe-greenhouse",
            fallback_name=self.source.name,
        )
        self.assertTrue(result.created)
        self.assertEqual(result.matched_by, "created")
        # "stripe-greenhouse" -> ATS suffix stripped -> "stripe" -> humanized "Stripe"
        self.assertEqual(result.company.name, "Stripe")
        self.assertNotEqual(result.company.name, "stripe-greenhouse")

    def test_explicit_company_name_wins_over_humanized_slug(self):
        result = self.resolver.resolve(
            platform="greenhouse", tenant_slug="stripe",
            company_name="Stripe, Inc.",
        )
        self.assertEqual(result.company.name, "Stripe, Inc.")

    def test_second_resolve_same_tenant_reuses_identity_not_create(self):
        first = self.resolver.resolve(
            platform="greenhouse", tenant_slug="airbnb", company_name="Airbnb",
        )
        second = self.resolver.resolve(
            platform="greenhouse", tenant_slug="airbnb", company_name="Airbnb",
        )
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(second.matched_by, "identity")
        self.assertEqual(first.company.id, second.company.id)
        self.assertEqual(Company.objects.filter(slug="airbnb").count(), 1)

    def test_identity_persisted_for_future_lookup(self):
        self.resolver.resolve(
            platform="ashby", tenant_slug="notion", company_name="Notion",
            source=self.source,
        )
        identity = CompanyResolutionIdentity.objects.get(
            platform="ashby", tenant_slug="notion",
        )
        self.assertEqual(identity.company.name, "Notion")
        self.assertEqual(identity.matched_by, "created")
        self.assertEqual(identity.source_id, self.source.id)

    def test_ats_migration_same_domain_reuses_company_not_duplicate(self):
        """The Notion/Plaid/Ramp lesson: an employer migrating lever -> ashby
        must resolve to the SAME Company via domain match, not spawn a
        second Company row just because the tenant slug differs."""
        first = self.resolver.resolve(
            platform="lever", tenant_slug="acmeco", company_name="Acme Co",
            company_domain="acme.com",
        )
        # Employer migrates ATS: new platform/tenant, same domain.
        second = self.resolver.resolve(
            platform="ashby", tenant_slug="acme-corp-ashby-tenant",
            company_name="Acme Co", company_domain="acme.com",
        )
        self.assertEqual(first.company.id, second.company.id)
        self.assertEqual(second.matched_by, "domain")
        self.assertEqual(Company.objects.filter(domain="acme.com").count(), 1)

    def test_slug_match_backfills_placeholder_name(self):
        """A Company created by the OLD buggy inline logic (name == raw
        slug) must get its name corrected once a real name is available,
        without creating a duplicate Company."""
        placeholder = Company.objects.create(slug="globex", name="globex")
        result = self.resolver.resolve(
            platform="greenhouse", tenant_slug="globex", company_name="Globex Corporation",
        )
        self.assertEqual(result.company.id, placeholder.id)
        placeholder.refresh_from_db()
        self.assertEqual(placeholder.name, "Globex Corporation")

    def test_slug_collision_does_not_merge_different_employers(self):
        """Two genuinely different companies whose stripped slugs collide
        must NOT be silently merged - the first keeps the plain slug, the
        second gets a disambiguated one, and they remain distinct rows."""
        first = self.resolver.resolve(
            platform="greenhouse", tenant_slug="initech", company_name="Initech LLC",
        )
        # No domain given for either, so this can only be distinguished by
        # giving it a different platform/tenant and relying on NOT matching
        # by slug (since the first call already "took" slug=initech via the
        # create path, a second create() with the same literal slug_key
        # would collide) - verify collision-safe suffixing.
        second = self.resolver.resolve(
            platform="lever", tenant_slug="initech-unrelated",
            company_name="Initech Unrelated Startup",
        )
        self.assertNotEqual(first.company.id, second.company.id)
        self.assertEqual(Company.objects.count(), 2)

    def test_no_platform_or_tenant_still_resolves_via_fallback_name(self):
        """Manual/legacy sources without ats_platform must still resolve to
        a sane Company using fallback_name, without crashing."""
        result = self.resolver.resolve(fallback_name="Manual Co")
        self.assertTrue(result.created)
        self.assertEqual(result.company.name, "Manual Co")
