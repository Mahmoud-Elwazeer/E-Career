"""Tests for rediscover_sources trigger selection + evidence recording.

Covers the directive's richer trigger set (§3): historically-productive
(ran before, zero errors, now returns 0) and repeated-errors, OR'd together
with the pre-existing degraded-only/min-zero-yield triggers. Also covers that
a MIGRATED verdict is now recorded as evidence even in DRY-RUN mode (visible
for review before --apply), where previously dry-run discarded it.
"""
import io
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import Source
from apps.scraper.pipeline.source_discovery import DiscoveryResult


class RediscoverTriggerSelectionTests(TestCase):
    def setUp(self):
        # A source that ran before, had zero errors, but now yields 0 jobs -
        # the "silent migration" signature.
        self.silent_migration = Source.objects.create(
            name="Acme", slug="acme-lever", url="https://jobs.lever.co/acme",
            ats_platform="lever", is_active=True,
            jobs_found_last_run=0, error_count=0,
            last_run_at=timezone.now(),
        )
        # A source repeatedly failing to fetch (e.g. dead endpoint).
        self.repeated_errors = Source.objects.create(
            name="Globex", slug="globex-ashby", url="https://jobs.ashbyhq.com/globex",
            ats_platform="ashby", is_active=True,
            error_count=5,
        )
        # A healthy source that should NOT be selected by either new trigger.
        self.healthy = Source.objects.create(
            name="Initech", slug="initech-greenhouse",
            url="https://boards.greenhouse.io/initech",
            ats_platform="greenhouse", is_active=True,
            jobs_found_last_run=42, error_count=0,
            last_run_at=timezone.now(),
        )

    def test_historically_productive_selects_only_the_silent_zero_yield_source(self):
        out = io.StringIO()
        with patch(
            "apps.scraper.management.commands.rediscover_sources._live_fetcher",
            return_value=(0, None),
        ):
            call_command("rediscover_sources", "--historically-productive", stdout=out)

        # Command selection is asserted via the queryset count line + which
        # source slug gets probed - the DB is intentionally untouched by a
        # dry-run (last_discovery_at is only persisted inside `if apply:`
        # branches), so stdout is the correct observable here, not the DB.
        output = out.getvalue()
        self.assertIn("rediscovering 1 source(s)", output)
        self.assertIn("acme-lever", output)
        self.assertNotIn("globex-ashby", output)
        self.assertNotIn("initech-greenhouse", output)

    def test_repeated_errors_selects_only_the_failing_source(self):
        out = io.StringIO()
        with patch(
            "apps.scraper.management.commands.rediscover_sources._live_fetcher",
            return_value=(0, None),
        ):
            call_command("rediscover_sources", "--repeated-errors", "3", stdout=out)

        output = out.getvalue()
        self.assertIn("rediscovering 1 source(s)", output)
        self.assertIn("globex-ashby", output)
        self.assertNotIn("initech-greenhouse", output)

    def test_no_trigger_flags_probes_all_active_sources(self):
        out = io.StringIO()
        with patch(
            "apps.scraper.management.commands.rediscover_sources._live_fetcher",
            return_value=(0, None),
        ):
            call_command("rediscover_sources", stdout=out)

        output = out.getvalue()
        self.assertIn("rediscovering 3 source(s)", output)


class RediscoverDryRunEvidenceTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="Notion", slug="notion-lever", url="https://jobs.lever.co/notion",
            ats_platform="lever", is_active=True,
        )

    def test_migrated_verdict_visible_in_dry_run_without_mutating_db(self):
        """Dry-run must surface full MIGRATED evidence (old/new provider, job
        count, successor slug) on stdout for review, while making NO
        database writes at all - consistent with the ACTIVE/INVALID
        branches, which also never persist in dry-run."""
        fake_discovery = DiscoveryResult(
            slug="notion", provider="ashby", tenant="notion",
            endpoint="https://api.ashbyhq.com/posting-api/job-board/notion",
            job_count=128, healthy=True,
        )
        out = io.StringIO()
        with patch(
            "apps.scraper.management.commands.rediscover_sources.discover_ats",
            return_value=fake_discovery,
        ):
            call_command("rediscover_sources", "--source", "notion-lever", stdout=out)

        output = out.getvalue()
        self.assertIn("MIGRATED", output)
        self.assertIn("lever -> ashby", output)
        self.assertIn("128 jobs at notion-ashby", output)

        self.source.refresh_from_db()
        self.assertTrue(self.source.is_active, "dry-run must NOT deactivate the source")
        self.assertEqual(self.source.lifecycle_state, "active", "dry-run must NOT mutate lifecycle_state")
        self.assertEqual(self.source.migration_history, [], "dry-run must NOT persist migration_history")
        self.assertFalse(Source.objects.filter(slug="notion-ashby").exists(),
                          "dry-run must NOT create the successor source")

    def test_apply_mode_marks_review_status_auto_applied(self):
        fake_discovery = DiscoveryResult(
            slug="notion", provider="ashby", tenant="notion",
            endpoint="https://api.ashbyhq.com/posting-api/job-board/notion",
            job_count=128, healthy=True,
        )
        with patch(
            "apps.scraper.management.commands.rediscover_sources.discover_ats",
            return_value=fake_discovery,
        ):
            call_command("rediscover_sources", "--source", "notion-lever", "--apply")

        self.source.refresh_from_db()
        self.assertEqual(self.source.lifecycle_state, "migrated")
        self.assertFalse(self.source.is_active)
        event = self.source.migration_history[0]
        self.assertEqual(event["review_status"], "auto_applied")
        successor = Source.objects.get(slug="notion-ashby")
        self.assertEqual(successor.ats_platform, "ashby")
