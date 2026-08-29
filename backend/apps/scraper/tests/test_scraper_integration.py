"""
End-to-end scraper integration test.

Tests the full pipeline: orchestrator → ATS fetch → pipeline stages → Job creation.
"""
import datetime
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import Job, Company, Source
from apps.scraper.orchestrator import ScraperOrchestrator


class TestScraperIntegration(TestCase):
    """Integration test covering the scraper pipeline end-to-end."""

    def setUp(self):
        self.company = Company.objects.create(
            name="TestCorp",
            slug="testcorp",
            domain="testcorp.com",
        )
        self.source = Source.objects.create(
            name="TestCorp Greenhouse",
            slug="testcorp-greenhouse",
            url="https://boards.greenhouse.io/testcorp",
            ats_platform="greenhouse",
            is_active=True,
            schedule_cron="0 */6 * * *",
        )

    @patch("apps.scraper.orchestrator.greenhouse.fetch_greenhouse_jobs")
    @patch("apps.scraper.orchestrator.verify_url_live")
    def test_full_pipeline_creates_job(self, mock_verify_url, mock_fetch):
        """A valid scraped job flows through all stages and creates a Job record."""
        mock_fetch.return_value = [
            {
                "title": "Senior Backend Engineer",
                "description": "Build scalable APIs with Python and Django. "
                               "Bachelor's degree required. Health insurance. 401k.",
                "location": "San Francisco, CA",
                "remote_type": "hybrid",
                "employment_type": "full_time",
                "experience_level": "senior",
                "salary_min": 150000,
                "salary_max": 200000,
                "salary_currency": "USD",
                "direct_apply_url": "https://boards.greenhouse.io/testcorp/jobs/123",
                "ats_platform": "greenhouse",
                "ats_job_id": "gh-123",
                "company_slug": "testcorp",
                "raw_data": {"id": "gh-123"},
            }
        ]
        mock_verify_url.return_value = True

        orchestrator = ScraperOrchestrator()
        jobs, added = orchestrator.scrape_source(self.source)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(added, 1)

        job = Job.objects.get(ats_job_id="gh-123", ats_platform="greenhouse")
        self.assertEqual(job.title, "Senior Backend Engineer")
        self.assertEqual(job.work_arrangement, "hybrid")
        self.assertEqual(job.company.slug, "testcorp")
        self.assertIsNotNone(job.legitimacy_score)

    @patch("apps.scraper.orchestrator.greenhouse.fetch_greenhouse_jobs")
    def test_blocked_aggregator_url_rejected(self, mock_fetch):
        """Jobs with aggregator apply URLs are filtered out."""
        mock_fetch.return_value = [
            {
                "title": "Software Engineer",
                "description": "A job listing.",
                "location": "Remote",
                "direct_apply_url": "https://www.linkedin.com/jobs/view/12345",
                "ats_platform": "greenhouse",
                "ats_job_id": "gh-blocked",
                "company_slug": "testcorp",
            }
        ]

        orchestrator = ScraperOrchestrator()
        jobs, added = orchestrator.scrape_source(self.source)

        self.assertEqual(added, 0)
        self.assertFalse(Job.objects.filter(ats_job_id="gh-blocked").exists())

    @patch("apps.scraper.orchestrator.greenhouse.fetch_greenhouse_jobs")
    @patch("apps.scraper.orchestrator.verify_url_live")
    def test_duplicate_job_not_re_added(self, mock_verify_url, mock_fetch):
        """A job with the same ats_job_id + platform is not duplicated."""
        Job.objects.create(
            company=self.company,
            title="Existing Job",
            slug="existing-job-gh-dup",
            location="Remote",
            location_type="remote",
            industry="technology",
            experience_level="mid",
            description="Already exists",
            source_url="https://testcorp.com/jobs/1",
            posted_at=datetime.date.today(),
            ats_job_id="gh-dup",
            ats_platform="greenhouse",
        )

        mock_fetch.return_value = [
            {
                "title": "Existing Job",
                "description": "Already exists",
                "location": "Remote",
                "direct_apply_url": "https://boards.greenhouse.io/testcorp/jobs/dup",
                "ats_platform": "greenhouse",
                "ats_job_id": "gh-dup",
                "company_slug": "testcorp",
            }
        ]
        mock_verify_url.return_value = True

        orchestrator = ScraperOrchestrator()
        jobs, added = orchestrator.scrape_source(self.source)

        self.assertEqual(added, 0)
        self.assertEqual(Job.objects.filter(ats_job_id="gh-dup").count(), 1)

    def test_scrape_all_sources_method_exists(self):
        """The scrape_all_sources method exists and returns expected dict shape."""
        orchestrator = ScraperOrchestrator()
        with patch.object(orchestrator, "scrape_source", return_value=([], 0)):
            result = orchestrator.scrape_all_sources()

        self.assertIn("total_found", result)
        self.assertIn("total_added", result)
