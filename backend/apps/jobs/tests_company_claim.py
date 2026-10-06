"""Tests for CompanyClaimService (Task #12 — Company Claim workflow).

Covers evidence evaluation (corporate_email, dns_txt), state transitions
(approve/reject/revoke), and the side effects of approval (EmployerProfile +
EmployerTeamMember creation on the SAME Company, idempotent, conflict-safe).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.jobs.models import Company, CompanyClaim, CompanyResolutionIdentity
from apps.jobs.company_claim import (
    CompanyClaimService, FREE_MAIL_DOMAINS, email_domain,
)

User = get_user_model()


class EmailDomainHelperTests(TestCase):
    def test_extracts_domain_lowercased(self):
        self.assertEqual(email_domain("Alice@Example.COM"), "example.com")

    def test_no_at_sign_returns_empty(self):
        self.assertEqual(email_domain("not-an-email"), "")

    def test_empty_input_returns_empty(self):
        self.assertEqual(email_domain(""), "")
        self.assertEqual(email_domain(None), "")


class CorporateEmailEvidenceTests(TestCase):
    def setUp(self):
        self.service = CompanyClaimService()
        self.company = Company.objects.create(
            name="Acme Corp", slug="acme-corp", domain="acme.com",
        )

    def test_exact_domain_match_lands_under_review_not_auto_approved(self):
        """Even a strong corporate_email match never auto-approves - admin
        review is always the final gate in this implementation."""
        result = self.service.evaluate_corporate_email(
            company=self.company, claimant_email="jane@acme.com",
        )
        self.assertEqual(result.recommended_status, CompanyClaim.STATUS_UNDER_REVIEW)
        self.assertGreaterEqual(result.confidence, 0.8)
        self.assertTrue(result.evidence["exact_match"])
        self.assertFalse(result.is_free_mail_domain)

    def test_free_mail_domain_never_sufficient_even_if_company_has_no_domain(self):
        """A gmail.com claimant can never get past verification_required,
        regardless of anything else - this is the directive's explicit
        'same-name or free-mail claims are never sufficient' rule."""
        result = self.service.evaluate_corporate_email(
            company=self.company, claimant_email="jane.doe@gmail.com",
        )
        self.assertTrue(result.is_free_mail_domain)
        self.assertEqual(result.recommended_status, CompanyClaim.STATUS_VERIFICATION_REQUIRED)
        self.assertLess(result.confidence, 0.5)

    def test_known_free_mail_domains_sample(self):
        for domain in ("gmail.com", "yahoo.com", "outlook.com", "icloud.com"):
            self.assertIn(domain, FREE_MAIL_DOMAINS)

    def test_non_matching_corporate_domain_requires_more_evidence(self):
        result = self.service.evaluate_corporate_email(
            company=self.company, claimant_email="bob@someother-company.com",
        )
        self.assertFalse(result.evidence["exact_match"])
        self.assertEqual(result.recommended_status, CompanyClaim.STATUS_VERIFICATION_REQUIRED)

    def test_company_with_no_domain_on_record_requires_more_evidence(self):
        bare_company = Company.objects.create(name="No Domain Co", slug="no-domain-co")
        result = self.service.evaluate_corporate_email(
            company=bare_company, claimant_email="anyone@no-domain-co.com",
        )
        self.assertEqual(result.recommended_status, CompanyClaim.STATUS_VERIFICATION_REQUIRED)

    def test_domain_recorded_via_resolution_identity_also_counts(self):
        """A domain observed via CompanyResolutionIdentity (even if
        Company.domain itself is still blank) is valid evidence too."""
        bare_company = Company.objects.create(name="ATS Only Co", slug="ats-only-co")
        CompanyResolutionIdentity.objects.create(
            company=bare_company, platform="greenhouse", tenant_slug="ats-only-co",
            domain="atsonly.io", matched_by="created", confidence=1.0,
        )
        result = self.service.evaluate_corporate_email(
            company=bare_company, claimant_email="jane@atsonly.io",
        )
        self.assertTrue(result.evidence["exact_match"])
        self.assertEqual(result.recommended_status, CompanyClaim.STATUS_UNDER_REVIEW)


class DnsTxtEvidenceTests(TestCase):
    def setUp(self):
        self.service = CompanyClaimService()
        self.company = Company.objects.create(
            name="DnsCo", slug="dnsco", domain="dnsco.example",
        )

    def test_matching_txt_record_lands_under_review(self):
        token = "abc123token"
        result = self.service.check_dns_txt(
            domain="dnsco.example", expected_token=token,
            resolver=lambda name: [f"usam-verify={token}"],
        )
        self.assertTrue(result.evidence["token_matched"])
        self.assertEqual(result.recommended_status, CompanyClaim.STATUS_UNDER_REVIEW)
        self.assertGreaterEqual(result.confidence, 0.8)

    def test_non_matching_txt_record_requires_more_evidence(self):
        result = self.service.check_dns_txt(
            domain="dnsco.example", expected_token="expected-token",
            resolver=lambda name: ["some-other-value"],
        )
        self.assertFalse(result.evidence["token_matched"])
        self.assertEqual(result.recommended_status, CompanyClaim.STATUS_VERIFICATION_REQUIRED)

    def test_no_txt_records_at_all_requires_more_evidence(self):
        result = self.service.check_dns_txt(
            domain="dnsco.example", expected_token="expected-token",
            resolver=lambda name: [],
        )
        self.assertFalse(result.evidence["token_matched"])
        self.assertEqual(result.recommended_status, CompanyClaim.STATUS_VERIFICATION_REQUIRED)

    def test_resolver_raising_is_handled_gracefully_not_crashed(self):
        def failing_resolver(name):
            raise Exception("NXDOMAIN")
        result = self.service.check_dns_txt(
            domain="dnsco.example", expected_token="t", resolver=failing_resolver,
        )
        self.assertEqual(result.confidence, 0.0)
        self.assertIn("error", result.evidence)

    def test_queries_the_correct_record_name(self):
        seen = {}
        def spy_resolver(name):
            seen["name"] = name
            return []
        self.service.check_dns_txt(domain="dnsco.example", expected_token="t", resolver=spy_resolver)
        self.assertEqual(seen["name"], "_usam-verify.dnsco.example")

    def test_missing_domain_or_token_short_circuits(self):
        result = self.service.check_dns_txt(domain="", expected_token="t")
        self.assertEqual(result.confidence, 0.0)
        result2 = self.service.check_dns_txt(domain="dnsco.example", expected_token="")
        self.assertEqual(result2.confidence, 0.0)

    def test_no_dns_library_available_is_unverifiable_not_fake_success(self):
        """Without dnspython installed, the DEFAULT resolver must honestly
        report unverifiable rather than ever claiming success it can't
        prove. We don't install dnspython as a dependency, so this exercises
        the real default path."""
        result = self.service.check_dns_txt(
            domain="dnsco.example", expected_token="t", resolver=None,
        )
        self.assertEqual(result.confidence, 0.0)
        self.assertTrue(result.evidence.get("unverifiable") or "error" in result.evidence)


class ClaimApprovalWorkflowTests(TestCase):
    def setUp(self):
        self.service = CompanyClaimService()
        self.admin = User.objects.create_user(
            email="admin@usam.dev", password="x", first_name="Admin", last_name="User", role="admin",
        )
        self.claimant = User.objects.create_user(
            email="jane@acme.com", password="x", first_name="Jane", last_name="Doe",
        )
        self.company = Company.objects.create(name="Acme Corp", slug="acme-corp-2", domain="acme.com")
        self.claim = CompanyClaim.objects.create(
            company=self.company, claimant=self.claimant,
            evidence_type=CompanyClaim.EVIDENCE_CORPORATE_EMAIL,
            claimant_email_domain="acme.com", status=CompanyClaim.STATUS_UNDER_REVIEW,
            confidence=0.8,
        )

    def test_approve_creates_owner_employer_profile_and_team_membership(self):
        from apps.employers.models import EmployerProfile, EmployerTeamMember

        self.service.approve(self.claim, reviewed_by=self.admin, note="looks good")
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, CompanyClaim.STATUS_APPROVED)
        self.assertEqual(self.claim.reviewed_by, self.admin)

        profile = EmployerProfile.objects.get(user=self.claimant)
        self.assertEqual(profile.company_id, self.company.id)
        self.assertTrue(profile.is_verified)

        membership = EmployerTeamMember.objects.get(user=self.claimant, company=self.company)
        self.assertEqual(membership.role, "owner")
        self.assertTrue(membership.is_active)

        self.claimant.refresh_from_db()
        self.assertEqual(self.claimant.role, "employer")

    def test_approve_is_idempotent(self):
        self.service.approve(self.claim, reviewed_by=self.admin)
        self.service.approve(self.claim, reviewed_by=self.admin)  # must not crash or duplicate
        from apps.employers.models import EmployerTeamMember
        self.assertEqual(
            EmployerTeamMember.objects.filter(user=self.claimant, company=self.company).count(), 1,
        )

    def test_approve_rejects_when_claimant_already_owns_a_different_company(self):
        from apps.employers.models import EmployerProfile
        other_company = Company.objects.create(name="Other Co", slug="other-co")
        EmployerProfile.objects.create(user=self.claimant, company=other_company, job_title="Owner")

        with self.assertRaises(ValueError):
            self.service.approve(self.claim, reviewed_by=self.admin)

        self.claim.refresh_from_db()
        self.assertNotEqual(self.claim.status, CompanyClaim.STATUS_APPROVED)

    def test_reject_sets_status_and_reviewer(self):
        self.service.reject(self.claim, reviewed_by=self.admin, note="not enough evidence")
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, CompanyClaim.STATUS_REJECTED)
        self.assertEqual(self.claim.review_note, "not enough evidence")

    def test_revoke_requires_approved_status(self):
        with self.assertRaises(ValueError):
            self.service.revoke(self.claim, reviewed_by=self.admin)

    def test_revoke_after_approve_sets_revoked_status(self):
        self.service.approve(self.claim, reviewed_by=self.admin)
        self.service.revoke(self.claim, reviewed_by=self.admin, note="fraud discovered")
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, CompanyClaim.STATUS_REVOKED)

    def test_active_claim_uniqueness_constraint(self):
        """Only one ACTIVE claim per (company, claimant) is allowed; a second
        pending claim for the same pair must fail at the DB level."""
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CompanyClaim.objects.create(
                    company=self.company, claimant=self.claimant,
                    evidence_type=CompanyClaim.EVIDENCE_DNS_TXT,
                    status=CompanyClaim.STATUS_PENDING,
                )

    def test_rejected_claim_does_not_block_resubmission(self):
        """A terminal (rejected) claim does NOT count toward the active-claim
        uniqueness constraint, so the claimant can submit a new one."""
        self.service.reject(self.claim, reviewed_by=self.admin)
        # Should not raise - rejected is terminal, not active.
        new_claim = CompanyClaim.objects.create(
            company=self.company, claimant=self.claimant,
            evidence_type=CompanyClaim.EVIDENCE_DNS_TXT,
            status=CompanyClaim.STATUS_PENDING,
        )
        self.assertIsNotNone(new_claim.pk)
