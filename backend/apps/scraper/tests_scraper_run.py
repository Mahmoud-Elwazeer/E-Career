"""Tests for ScraperRun (§5/§8/§10) - persisted per-run Direct-Apply
resolution metrics, and its wiring into orchestrator._process_jobs.
"""
from unittest.mock import patch

from django.test import TestCase

from apps.jobs.models import Source
from apps.scraper.models import ScraperRun
from apps.scraper.orchestrator import ScraperOrchestrator


class ScraperRunModelTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="Acme", slug="acme-greenhouse", url="https://boards.greenhouse.io/acme",
            ats_platform="greenhouse",
        )

    def test_record_persists_direct_apply_metrics(self):
        metrics_dict = {
            "provider": "greenhouse", "fetched": 100, "normalized": 90,
            "created": 40, "updated": 10, "duplicates": 40, "verified": 40,
            "errors": 0, "publishable": 40, "indexed": 38,
            "direct_apply_candidate": 90, "direct_apply_verified": 85,
            "rejected_total": 10, "rejected": {"LOW_LEGITIMACY": 10},
            "degraded": False, "zero_yield_anomaly": False,
        }
        run = ScraperRun.record(self.source, metrics_dict, strategy_tier="STRUCTURED")

        self.assertEqual(run.fetched, 100)
        self.assertEqual(run.direct_apply_candidates, 90)
        self.assertEqual(run.direct_apply_verified, 85)
        self.assertEqual(run.strategy_tier, "STRUCTURED")
        self.assertEqual(run.rejected_breakdown, {"LOW_LEGITIMACY": 10})

    def test_resolution_rate_computed_correctly(self):
        run = ScraperRun.record(self.source, {
            "direct_apply_candidate": 100, "direct_apply_verified": 75,
        })
        self.assertEqual(run.direct_apply_resolution_rate, 0.75)

    def test_resolution_rate_zero_candidates_does_not_crash(self):
        run = ScraperRun.record(self.source, {
            "direct_apply_candidate": 0, "direct_apply_verified": 0,
        })
        self.assertEqual(run.direct_apply_resolution_rate, 0.0)

    def test_which_source_has_most_verified_direct_apply_is_a_real_query(self):
        """The directive's explicit question: 'which source produces the
        most VERIFIED DIRECT APPLY jobs?' must be answerable with ORM, not a
        log grep."""
        other = Source.objects.create(
            name="Globex", slug="globex-ashby", url="https://jobs.ashbyhq.com/globex",
            ats_platform="ashby",
        )
        ScraperRun.record(self.source, {"fetched": 1000, "direct_apply_verified": 5})
        ScraperRun.record(other, {"fetched": 50, "direct_apply_verified": 48})

        top_by_fetched = ScraperRun.objects.order_by("-fetched").first()
        top_by_verified_direct_apply = ScraperRun.objects.order_by("-direct_apply_verified").first()

        self.assertEqual(top_by_fetched.source, self.source)       # most jobs
        self.assertEqual(top_by_verified_direct_apply.source, other)  # most VERIFIED direct apply


class ScraperRunOrchestratorWiringTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="TestCorp", slug="testcorp-greenhouse",
            url="https://boards.greenhouse.io/testcorp",
            ats_platform="greenhouse", is_active=True,
        )

    @patch("apps.scraper.orchestrator.greenhouse.fetch_greenhouse_jobs")
    @patch("apps.scraper.orchestrator.verify_url_live")
    def test_real_scrape_run_persists_a_scraper_run_row(self, mock_verify_url, mock_fetch):
        mock_fetch.return_value = [
            {
                "title": "Backend Engineer",
                "description": "A real job description that is long enough "
                               "to clear the legitimacy content check here.",
                "location": "Remote",
                "direct_apply_url": "https://boards.greenhouse.io/testcorp/jobs/1",
                "ats_platform": "greenhouse",
                "ats_job_id": "gh-run-1",
                "company_slug": "testcorp",
            }
        ]
        mock_verify_url.return_value = True

        self.assertEqual(ScraperRun.objects.count(), 0)
        orchestrator = ScraperOrchestrator()
        orchestrator.scrape_source(self.source)

        self.assertEqual(ScraperRun.objects.count(), 1)
        run = ScraperRun.objects.first()
        self.assertEqual(run.source, self.source)
        self.assertEqual(run.fetched, 1)
        self.assertEqual(run.direct_apply_candidates, 1)
        self.assertEqual(run.direct_apply_verified, 1)
        self.assertEqual(run.strategy_tier, "STRUCTURED")

    @patch("apps.scraper.orchestrator.greenhouse.fetch_greenhouse_jobs")
    def test_scraper_run_persist_failure_does_not_break_the_scrape(self, mock_fetch):
        """A ScraperRun.record() failure must be caught and logged, never
        propagate and break the actual ingestion run that already
        succeeded."""
        mock_fetch.return_value = []
        with patch("apps.scraper.models.ScraperRun.record", side_effect=RuntimeError("db boom")):
            orchestrator = ScraperOrchestrator()
            # Must not raise.
            jobs, added = orchestrator.scrape_source(self.source)
        self.assertEqual(jobs, [])
        self.assertEqual(added, 0)
