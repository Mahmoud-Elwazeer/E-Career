"""Controlled test of the Tier-3 (ADAPTIVE_PARSER) extraction path (§15).

Wires the EXISTING OutOfProcessBackend contract (apps/scraper/pipeline/
extraction_adapter.py) to the Scrapling runner (apps/scraper/
extraction_runners/scrapling_runner.py) for a real, bounded, read-only test
against ONE url. This is the first time this contract has an actual runner
configured - previously `OutOfProcessBackend.available()` was always False
(no runner_cmd ever set anywhere in the codebase).

Does NOT persist anything to the database. Does NOT install Scrapling into
the main Django venv - it must already be installed in a SEPARATE,
isolated venv (see apps/scraper/extraction_runners/scrapling_runner.py's
module docstring for setup instructions), and that venv's python path is
passed via --runner-python.

Usage:
  python manage.py test_adaptive_extraction --url https://example.com/careers \\
      --runner-python /opt/scrapling-runner-venv/bin/python

If --runner-python is omitted, defaults to SCRAPLING_RUNNER_PYTHON from
settings/env (not required to be set - the command will clearly report
"not configured" rather than silently doing nothing).
"""
from __future__ import annotations

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.scraper.pipeline.extraction_adapter import (
    ExtractionTier,
    ExtractionRouter,
    OutOfProcessBackend,
)


class Command(BaseCommand):
    help = "Test the Tier-3 adaptive (Scrapling) extraction path against one real URL."

    def add_arguments(self, parser):
        parser.add_argument("--url", required=True, help="Careers/job-listing URL to test")
        parser.add_argument(
            "--runner-python",
            default=getattr(settings, "SCRAPLING_RUNNER_PYTHON", "") or os.environ.get("SCRAPLING_RUNNER_PYTHON", ""),
            help="Path to the python executable inside the isolated Scrapling venv",
        )
        parser.add_argument(
            "--runner-cmd",
            default="",
            help=(
                "Comma-separated full command for the runner, e.g. "
                "'docker,run,--rm,-i,usam-scrapling-runner:0.4.15' "
                "(see apps/scraper/extraction_runners/Dockerfile). "
                "Takes priority over --runner-python when set."
            ),
        )

    def handle(self, *args, **opts):
        url = opts["url"]
        runner_python = opts["runner_python"]
        runner_cmd_opt = opts["runner_cmd"]

        if runner_cmd_opt:
            runner_cmd = [p for p in runner_cmd_opt.split(",") if p]
        elif runner_python:
            runner_script = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "..", "extraction_runners", "scrapling_runner.py",
            )
            runner_cmd = [runner_python, os.path.normpath(runner_script)]
        else:
            self.stdout.write(self.style.ERROR(
                "No runner configured. Either:\n"
                "  python manage.py test_adaptive_extraction --url <url> "
                "--runner-cmd docker,run,--rm,-i,usam-scrapling-runner:0.4.15\n"
                "or:\n"
                "  python manage.py test_adaptive_extraction --url <url> "
                "--runner-python /opt/scrapling-runner-venv/bin/python\n"
                "(see apps/scraper/extraction_runners/Dockerfile and "
                "scrapling_runner.py for setup.)"
            ))
            return

        backend = OutOfProcessBackend(
            name="scrapling",
            tier=ExtractionTier.ADAPTIVE_PARSER,
            runner_cmd=runner_cmd,
        )

        self.stdout.write(f"Backend available: {backend.available()}")
        if not backend.available():
            self.stdout.write(self.style.ERROR("Backend reports unavailable - check runner_cmd."))
            return

        router = ExtractionRouter([backend], max_tier=ExtractionTier.ADAPTIVE_PARSER)
        result = router.extract(url)

        self.stdout.write(f"\nURL: {url}")
        self.stdout.write(f"ok: {result.ok}")
        self.stdout.write(f"tier: {result.tier.name}")
        self.stdout.write(f"jobs found: {len(result.jobs)}")
        if result.error:
            self.stdout.write(self.style.WARNING(f"error: {result.error}"))
        self.stdout.write(f"evidence: {result.evidence}")

        for i, job in enumerate(result.jobs[:5], 1):
            self.stdout.write(
                f"  [{i}] {job.get('title', '?')} @ {job.get('company', '?')} "
                f"({job.get('raw_data', {}).get('extraction_method', '?')})"
            )

        if not result.jobs:
            self.stdout.write(self.style.WARNING(
                "\nNo jobs extracted. This is often CORRECT, not a failure - "
                "many real careers pages (confirmed live: notion.com/careers) "
                "render listings in plain HTML with no schema.org JSON-LD or "
                "microdata markup at all. This adapter deliberately does not "
                "guess from hashed/unstable CSS class names. A page with 0 "
                "extracted jobs should be routed to Tier 1 (DETERMINISTIC_HTTP) "
                "with a hand-written selector, not retried here."
            ))
