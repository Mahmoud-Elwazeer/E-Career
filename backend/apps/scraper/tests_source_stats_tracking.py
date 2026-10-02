"""Tests for the §4 source-registry stat fields wired into
tasks.py::scrape_all_sources (last_success_at, last_failure_at,
last_nonzero_at, historical_average_jobs EMA update).

Uses a real DB-backed Source (TestCase) since scrape_all_sources queries
Source.objects.filter(is_active=True) directly rather than taking a source
list as an argument.
"""
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import Source
from apps.scraper import tasks


class SourceStatsTrackingTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="Acme", slug="acme-greenhouse", url="https://boards.greenhouse.io/acme",
            ats_platform="greenhouse", is_active=True,
        )

    def test_successful_run_sets_last_success_and_last_nonzero(self):
        with patch("apps.scraper.tasks.scrape_source", return_value=[{"title": "A"}]), \
             patch("apps.scraper.tasks.process_and_store_jobs", return_value=1):
            tasks.scrape_all_sources.run()

        self.source.refresh_from_db()
        self.assertIsNotNone(self.source.last_success_at)
        self.assertIsNotNone(self.source.last_nonzero_at)
        self.assertEqual(self.source.last_run_status, "success")

    def test_zero_yield_run_sets_last_success_but_not_last_nonzero(self):
        with patch("apps.scraper.tasks.scrape_source", return_value=[]), \
             patch("apps.scraper.tasks.process_and_store_jobs", return_value=0):
            tasks.scrape_all_sources.run()

        self.source.refresh_from_db()
        self.assertIsNotNone(self.source.last_success_at)
        self.assertIsNone(self.source.last_nonzero_at)

    def test_historical_average_updates_as_ema(self):
        with patch("apps.scraper.tasks.scrape_source", return_value=[{"title": "A"}] * 100), \
             patch("apps.scraper.tasks.process_and_store_jobs", return_value=100):
            tasks.scrape_all_sources.run()
        self.source.refresh_from_db()
        self.assertEqual(self.source.historical_average_jobs, 100.0)  # first run = seed value

        with patch("apps.scraper.tasks.scrape_source", return_value=[{"title": "A"}] * 50), \
             patch("apps.scraper.tasks.process_and_store_jobs", return_value=50):
            tasks.scrape_all_sources.run()
        self.source.refresh_from_db()
        # EMA(alpha=0.3): 0.3*50 + 0.7*100 = 85.0
        self.assertEqual(self.source.historical_average_jobs, 85.0)

    def test_failed_run_sets_last_failure_at(self):
        with patch("apps.scraper.tasks.scrape_source", side_effect=RuntimeError("boom")):
            tasks.scrape_all_sources.run()

        self.source.refresh_from_db()
        self.assertIsNotNone(self.source.last_failure_at)
        self.assertEqual(self.source.last_run_status, "failed")
