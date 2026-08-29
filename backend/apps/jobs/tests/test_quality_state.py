"""Tests for the Job quality_state field and related machinery."""
import datetime
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import Job, Company


class TestQualityStateField(TestCase):
    """Test quality_state field definition and choices."""

    def setUp(self):
        self.company = Company.objects.create(name="TestCo", slug="testco-qs")

    def _make_job(self, **kwargs):
        defaults = {
            "company": self.company,
            "title": "Engineer",
            "slug": f"qs-test-{timezone.now().timestamp():.0f}",
            "location": "Remote",
            "location_type": "remote",
            "industry": "technology",
            "experience_level": "mid",
            "description": "Test",
            "source_url": "https://example.com/job",
            "posted_at": datetime.date.today(),
        }
        defaults.update(kwargs)
        return Job.objects.create(**defaults)

    def test_default_quality_state(self):
        job = self._make_job()
        self.assertEqual(job.quality_state, "needs_verification")

    def test_all_nine_states_are_valid(self):
        states = [c[0] for c in Job.QUALITY_STATE_CHOICES]
        self.assertEqual(len(states), 9)
        expected = {
            "active", "probably_active", "needs_verification",
            "expired", "archived", "broken", "duplicate",
            "rejected", "direct_verified",
        }
        self.assertEqual(set(states), expected)

    def test_expired_now_in_status_choices(self):
        values = [c[0] for c in Job.STATUS_CHOICES]
        self.assertIn("expired", values)

    def test_quality_active_states(self):
        self.assertEqual(
            Job.QUALITY_ACTIVE_STATES,
            ("active", "probably_active", "direct_verified"),
        )

    def test_quality_visible_states(self):
        self.assertEqual(
            Job.QUALITY_VISIBLE_STATES,
            ("active", "probably_active", "direct_verified", "needs_verification"),
        )


class TestJobQuerySet(TestCase):
    """Test custom JobManager / JobQuerySet."""

    def setUp(self):
        self.company = Company.objects.create(name="QSCo", slug="qsco-mgr")

    def _make(self, quality_state, slug_suffix):
        return Job.objects.create(
            company=self.company,
            title="Eng",
            slug=f"mgr-{slug_suffix}",
            location="Remote",
            location_type="remote",
            industry="technology",
            experience_level="mid",
            description="Test",
            source_url="https://example.com/job",
            posted_at=datetime.date.today(),
            quality_state=quality_state,
        )

    def test_active_returns_active_states_only(self):
        j1 = self._make("active", "a")
        j2 = self._make("probably_active", "pa")
        j3 = self._make("direct_verified", "dv")
        self._make("expired", "exp")
        self._make("needs_verification", "nv")
        self._make("rejected", "rej")

        active = set(Job.objects.active().values_list("pk", flat=True))
        self.assertEqual(active, {j1.pk, j2.pk, j3.pk})

    def test_visible_returns_visible_states_only(self):
        j1 = self._make("active", "a2")
        j2 = self._make("probably_active", "pa2")
        j3 = self._make("direct_verified", "dv2")
        j4 = self._make("needs_verification", "nv2")
        self._make("expired", "exp2")
        self._make("rejected", "rej2")
        self._make("archived", "arc2")

        visible = set(Job.objects.visible().values_list("pk", flat=True))
        self.assertEqual(visible, {j1.pk, j2.pk, j3.pk, j4.pk})

    def test_active_is_chainable(self):
        self._make("active", "chain1")
        self._make("active", "chain2")
        self._make("expired", "chain3")
        count = Job.objects.active().filter(title="Eng").count()
        self.assertEqual(count, 2)


class TestVerificationTasksQualityState(TestCase):
    """Test that verification tasks write quality_state correctly."""

    def setUp(self):
        self.company = Company.objects.create(
            name="VerifCo", slug="verifco-qs", domain="verifco.com"
        )

    def _make_active_job(self, slug_suffix):
        return Job.objects.create(
            company=self.company,
            title="Eng",
            slug=f"verif-{slug_suffix}",
            location="Remote",
            location_type="remote",
            industry="technology",
            experience_level="mid",
            description="Test",
            source_url="https://verifco.com/job",
            direct_apply_url="https://verifco.com/job",
            posted_at=datetime.date.today() - datetime.timedelta(days=10),
            status="active",
            quality_state="active",
        )

    @patch("apps.verification.tasks.verify_url_is_live")
    def test_daily_liveness_marks_404_as_expired(self, mock_verify):
        mock_verify.return_value = (False, 404)
        job = self._make_active_job("404test")

        from apps.verification.tasks import daily_liveness_check
        daily_liveness_check()

        job.refresh_from_db()
        self.assertEqual(job.quality_state, "expired")
        self.assertTrue(job.is_expired)
        self.assertEqual(job.expired_reason, "404_not_found")
        self.assertIsNotNone(job.last_verified_at)

    @patch("apps.verification.tasks.verify_url_is_live")
    def test_daily_liveness_ssrf_marks_broken(self, mock_verify):
        from apps.core.safe_fetch import SSRFBlockedError
        mock_verify.side_effect = SSRFBlockedError("https://verifco.com/job", "blocked")
        job = self._make_active_job("ssrftest")

        from apps.verification.tasks import daily_liveness_check
        daily_liveness_check()

        job.refresh_from_db()
        self.assertEqual(job.quality_state, "broken")
        self.assertEqual(job.expired_reason, "ssrf_blocked")

    @patch("apps.verification.tasks.verify_url_is_live")
    def test_verify_single_job_404(self, mock_verify):
        mock_verify.return_value = (False, 404)
        job = self._make_active_job("single404")

        from apps.verification.tasks import verify_job_url
        result = verify_job_url(job.id)

        job.refresh_from_db()
        self.assertEqual(job.quality_state, "expired")
        self.assertEqual(result["status"], "expired")


class TestDataMigrationMapping(TestCase):
    """Verify the data-migration mapping logic matches expectations."""

    def setUp(self):
        self.company = Company.objects.create(name="MigCo", slug="migco-qs")

    def _make(self, status, is_expired, slug_suffix):
        return Job.objects.create(
            company=self.company,
            title="Eng",
            slug=f"mig-{slug_suffix}",
            location="Remote",
            location_type="remote",
            industry="technology",
            experience_level="mid",
            description="Test",
            source_url="https://example.com/job",
            posted_at=datetime.date.today(),
            status=status,
            is_expired=is_expired,
            quality_state="needs_verification",
        )

    def test_mapping_active_not_expired(self):
        """status=active + is_expired=False should map to quality_state=active."""
        job = self._make("active", False, "anf")
        Job.objects.filter(pk=job.pk, status="active", is_expired=False).update(quality_state="active")
        job.refresh_from_db()
        self.assertEqual(job.quality_state, "active")

    def test_mapping_active_but_expired(self):
        """status=active + is_expired=True should map to quality_state=expired."""
        job = self._make("active", True, "ae")
        Job.objects.filter(pk=job.pk, status="active", is_expired=True).update(quality_state="expired")
        job.refresh_from_db()
        self.assertEqual(job.quality_state, "expired")

    def test_mapping_pending(self):
        job = self._make("pending", False, "pend")
        Job.objects.filter(pk=job.pk, status="pending").update(quality_state="needs_verification")
        job.refresh_from_db()
        self.assertEqual(job.quality_state, "needs_verification")

    def test_mapping_rejected(self):
        job = self._make("rejected", False, "rej")
        Job.objects.filter(pk=job.pk, status="rejected").update(quality_state="rejected")
        job.refresh_from_db()
        self.assertEqual(job.quality_state, "rejected")

    def test_mapping_archived(self):
        job = self._make("archived", False, "arch")
        Job.objects.filter(pk=job.pk, status="archived").update(quality_state="archived")
        job.refresh_from_db()
        self.assertEqual(job.quality_state, "archived")
