"""Tests for the verification engine and all 6 stages."""
import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.jobs.models import Job, Company
from apps.verification.engine import VerificationEngine
from apps.verification.stages import (
    ATSFingerprintStage,
    RedirectResolverStage,
    DomainVerifierStage,
    LegitimacyScorerStage,
    FreshnessCheckerStage,
    DeduplicatorStage,
)
from apps.verification.stages.ats_fingerprint import BLOCKED_DOMAINS


User = get_user_model()


class TestATSFingerprintStage(TestCase):
    """Test Stage 1: ATS Fingerprinting."""
    
    def setUp(self):
        self.stage = ATSFingerprintStage()
    
    def test_greenhouse_url_detection(self):
        """Test detection of Greenhouse ATS platform."""
        url = "https://boards.greenhouse.io/google/jobs/12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "greenhouse")
        self.assertGreater(result.confidence, 0.9)
    
    def test_lever_url_detection(self):
        """Test detection of Lever ATS platform."""
        url = "https://jobs.lever.co/google/12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "lever")
        self.assertGreater(result.confidence, 0.9)
    
    def test_ashby_url_detection(self):
        """Test detection of Ashby ATS platform."""
        url = "https://jobs.ashbyhq.com/google/12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "ashby")
        self.assertGreater(result.confidence, 0.9)
    
    def test_workday_url_detection(self):
        """Test detection of Workday ATS platform."""
        url = "https://myworkdayjobs.com/google/jobs/12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "workday")
        self.assertGreater(result.confidence, 0.9)
    
    def test_blocked_aggregator_linkedin(self):
        """Test that LinkedIn is blocked as aggregator."""
        url = "https://www.linkedin.com/jobs/view/12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
        self.assertEqual(result.confidence, 1.0)
    
    def test_blocked_aggregator_indeed(self):
        """Test that Indeed is blocked as aggregator."""
        url = "https://www.indeed.com/viewjob?jk=12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_glassdoor(self):
        """Test that Glassdoor is blocked as aggregator."""
        url = "https://www.glassdoor.com/Job/google-jobs-EI_IE0.0,6_KO7,10.htm"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_ziprecruiter(self):
        """Test that ZipRecruiter is blocked as aggregator."""
        url = "https://www.ziprecruiter.com/jobs/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_monster(self):
        """Test that Monster is blocked as aggregator."""
        url = "https://www.monster.com/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_careerbuilder(self):
        """Test that CareerBuilder is blocked as aggregator."""
        url = "https://www.careerbuilder.com/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_dice(self):
        """Test that Dice is blocked as aggregator."""
        url = "https://www.dice.com/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_simplyhired(self):
        """Test that SimplyHired is blocked as aggregator."""
        url = "https://www.simplyhired.com/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_snagajob(self):
        """Test that Snagajob is blocked as aggregator."""
        url = "https://www.snagajob.com/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_bayt(self):
        """Test that Bayt is blocked as aggregator."""
        url = "https://www.bayt.com/en/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_wuzzuf(self):
        """Test that Wuzzuf is blocked as aggregator."""
        url = "https://www.wuzzuf.net/jobs/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_gulftalent(self):
        """Test that GulfTalent is blocked as aggregator."""
        url = "https://www.gulftalent.com/jobs/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_naukri(self):
        """Test that Naukri is blocked as aggregator."""
        url = "https://www.naukri.com/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_seek(self):
        """Test that Seek is blocked as aggregator."""
        url = "https://www.seek.com.au/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_blocked_aggregator_reed(self):
        """Test that Reed is blocked as aggregator."""
        url = "https://www.reed.co.uk/job/google-12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "BLOCKED_AGGREGATOR")
    
    def test_unknown_platform(self):
        """Test detection of unknown platform."""
        url = "https://example.com/careers/job/12345"
        result = self.stage.run(url)
        
        self.assertEqual(result.platform, "unknown")
        self.assertEqual(result.confidence, 0.3)
    
    def test_is_blocked_method(self):
        """Test the is_blocked helper method."""
        self.assertTrue(self.stage.is_blocked("https://linkedin.com/jobs/123"))
        self.assertFalse(self.stage.is_blocked("https://google.com/careers"))


class TestRedirectResolverStage(TestCase):
    """Test Stage 2: Redirect Resolution."""
    
    def setUp(self):
        self.stage = RedirectResolverStage()
    
    def test_empty_url(self):
        """Test handling of empty URL."""
        result = self.stage.run("")
        self.assertEqual(result.error, "empty_url")
    
    def test_no_redirect(self):
        """Test URL with no redirects."""
        from unittest.mock import patch, MagicMock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/jobs/123"
        mock_response.history = []
        with patch('apps.verification.stages.freshness_checker.safe_fetch', return_value=mock_response):
            result = self.stage.run("https://example.com/jobs/123")
        self.assertEqual(result.redirect_count, 0)
        self.assertIn("example.com", result.final_url)


class TestDomainVerifierStage(TestCase):
    """Test Stage 3: Domain Verification."""
    
    def setUp(self):
        self.stage = DomainVerifierStage()
    
    def test_empty_url(self):
        """Test handling of empty URL."""
        result = self.stage.run("", "", "")
        self.assertEqual(result.domain_trust, 0.0)
    
    def test_known_ats_domain(self):
        """Test known ATS domain detection."""
        result = self.stage.run("https://boards.greenhouse.io/google/jobs/123", "", "")
        self.assertGreater(result.domain_trust, 0.0)
    
    def test_domain_matches_company(self):
        """Test domain matching with company domain."""
        result = self.stage.run("https://careers.google.com/jobs/123", "google.com", "")
        self.assertTrue(result.domain_matches_company)
    
    def test_ssl_validation(self):
        """Test SSL validation."""
        result = self.stage.run("https://google.com", "", "")
        self.assertTrue(result.ssl_valid)


class TestLegitimacyScorerStage(TestCase):
    """Test Stage 4: Legitimacy Scoring."""
    
    def setUp(self):
        self.stage = LegitimacyScorerStage()
    
    def test_scam_indicators(self):
        """Test detection of scam indicators."""
        description = "Work from home, earn $5000 per day, no experience needed"
        result = self.stage.run(description, "", None)
        
        self.assertLess(result.score, 0.5)
        self.assertIn("scam_language", result.flags)
    
    def test_quality_indicators(self):
        """Test detection of quality indicators."""
        description = "Bachelor's degree required, 401k, health insurance, equal opportunity employer"
        result = self.stage.run(description, "", None)
        
        self.assertGreater(result.score, 0.5)
    
    def test_unrealistic_salary(self):
        """Test detection of unrealistic salary."""
        result = self.stage.run("Description", "https://example.com", 1000000)
        self.assertIn("unrealistic_salary", result.flags)
    
    def test_short_description(self):
        """Test detection of short description."""
        result = self.stage.run("Short", "https://example.com", None)
        self.assertIn("description_too_short", result.flags)


class TestFreshnessCheckerStage(TestCase):
    """Test Stage 5: Freshness & Liveness."""
    
    def setUp(self):
        self.stage = FreshnessCheckerStage()
    
    def test_empty_url(self):
        """Test handling of empty URL."""
        result = self.stage.run("")
        self.assertFalse(result.is_accessible)
    
    def test_timeout(self):
        """Test timeout handling."""
        from unittest.mock import patch
        import httpx
        with patch('apps.verification.stages.freshness_checker.safe_fetch', side_effect=httpx.TimeoutException("timed out")):
            result = self.stage.run("https://example.com/slow")
        self.assertFalse(result.is_accessible)


class TestDeduplicatorStage(TestCase):
    """Test Stage 6: Deduplication."""
    
    def setUp(self):
        self.stage = DeduplicatorStage()
    
    def test_hash_computation(self):
        """Test content hash computation."""
        hash1 = self.stage._compute_hash("Google", "Software Engineer", "Remote")
        hash2 = self.stage._compute_hash("Google", "Software Engineer", "Remote")
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 hex digest
    
    def test_duplicate_detection(self):
        """Test duplicate job detection."""
        from apps.verification.models import VerificationResult

        company = Company.objects.create(name="Google", slug="google-dedup")
        job1 = Job.objects.create(
            company=company,
            title="Software Engineer",
            slug="dedup-test-job",
            location="Remote",
            location_type="remote",
            industry="technology",
            experience_level="mid",
            description="Test job",
            source_url="https://google.com/jobs/1",
            direct_apply_url="https://google.com/jobs/1",
            posted_at=datetime.date.today(),
        )

        content_hash = self.stage._compute_hash("Google", "Software Engineer", "Remote")
        VerificationResult.objects.create(
            job=job1,
            status="verified",
            content_hash=content_hash,
            trust_score=0.9,
        )

        result = self.stage.run("Google", "Software Engineer", "Remote")

        self.assertTrue(result.is_duplicate)
        self.assertEqual(result.duplicate_of_id, job1.id)


class TestVerificationEngine(TestCase):
    """Test the full verification engine."""

    def setUp(self):
        self.engine = VerificationEngine()
        self.company = Company.objects.create(name="Google", slug="google-engine", domain="google.com")
        self._job_counter = 0

    def _make_job(self, **kwargs):
        """Helper to create a Job with all required fields."""
        self._job_counter += 1
        defaults = {
            "company": self.company,
            "title": "Software Engineer",
            "slug": f"verify-engine-job-{self._job_counter}",
            "location": "Remote",
            "location_type": "remote",
            "industry": "technology",
            "experience_level": "mid",
            "description": "Test job for verification",
            "source_url": "https://google.com/careers/job/test",
            "posted_at": datetime.date.today(),
        }
        defaults.update(kwargs)
        return Job.objects.create(**defaults)

    def test_verify_blocked_aggregator(self):
        """Test that blocked aggregator jobs are rejected."""
        job = self._make_job(direct_apply_url="https://linkedin.com/jobs/123")

        result = self.engine.verify_job(job)

        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.trust_score, 0.0)
        self.assertIn("BLOCKED", result.notes)

    def test_verify_employer_posted_verified(self):
        """Test auto-verification for verified employer."""
        self.company.is_verified = True
        self.company.save()

        job = self._make_job(
            direct_apply_url="https://google.com/jobs/1",
            source_type="employer_posted",
        )

        result = self.engine.verify_employer_posted_job(job)

        self.assertEqual(result.status, "verified")
        self.assertGreater(result.trust_score, 0.8)

    def test_trust_score_calculation(self):
        """Test trust score is within valid range."""
        job = self._make_job(direct_apply_url="https://google.com/careers/job/123")

        result = self.engine.verify_job(job)

        self.assertGreaterEqual(result.trust_score, 0.0)
        self.assertLessEqual(result.trust_score, 1.0)

    def test_verification_result_created(self):
        """Test that VerificationResult is created."""
        job = self._make_job(direct_apply_url="https://google.com/careers/job/123")

        result = self.engine.verify_job(job)

        self.assertIsNotNone(result.id)
        self.assertEqual(result.job, job)

    def test_job_model_updated(self):
        """Test that job model is updated with verification results."""
        job = self._make_job(direct_apply_url="https://google.com/careers/job/123")

        result = self.engine.verify_job(job)

        # Refresh from database
        job.refresh_from_db()

        self.assertIsNotNone(job.legitimacy_score)
        self.assertIsNotNone(job.apply_url_checked_at)
        self.assertIn(job.ats_platform, ["google", "unknown", ""])


class TestBlockedDomainsList(TestCase):
    """Test that BLOCKED_DOMAINS contains expected domains."""
    
    def test_blocked_domains_count(self):
        """Test that we have at least 15 blocked domains."""
        self.assertGreaterEqual(len(BLOCKED_DOMAINS), 15)
    
    def test_expected_blocked_domains(self):
        """Test that expected aggregator domains are blocked."""
        expected = {
            "linkedin.com",
            "indeed.com",
            "glassdoor.com",
            "ziprecruiter.com",
            "monster.com",
            "careerbuilder.com",
            "dice.com",
            "simplyhired.com",
            "snagajob.com",
            "bayt.com",
            "wuzzuf.net",
            "gulftalent.com",
            "naukri.com",
            "seek.com.au",
            "reed.co.uk",
        }
        
        self.assertTrue(expected.issubset(BLOCKED_DOMAINS))