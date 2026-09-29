"""Connector matrix (§19/§24): prove per-ATS ingestion, not just fetch().

Runs each active Source through the real ingestion funnel and prints a matrix:
provider | fetched | created | updated | rejected(by reason) | verified.

This generalizes the Greenhouse 154/0 fix across all connectors so we can see
which ATS truly ingest end-to-end vs. only fetch.

Usage:
  python manage.py connector_matrix                 # all active sources (persists)
  python manage.py connector_matrix --platform greenhouse
  python manage.py connector_matrix --fetch-only    # fetch + funnel dry-run, NO persist
  python manage.py connector_matrix --limit 5       # cap sources scanned
"""
from django.core.management.base import BaseCommand

from apps.jobs.models import Source
from apps.scraper.orchestrator import ScraperOrchestrator


class Command(BaseCommand):
    help = "Run each ATS source through the ingestion funnel and report a matrix."

    def add_arguments(self, parser):
        parser.add_argument("--platform", type=str, default="")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument(
            "--fetch-only", action="store_true",
            help="Fetch + run the funnel counters WITHOUT persisting jobs.",
        )

    def handle(self, *args, **opts):
        qs = Source.objects.filter(is_active=True)
        if opts["platform"]:
            qs = qs.filter(ats_platform__iexact=opts["platform"])
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        orch = ScraperOrchestrator()
        header = f"{'source':32} {'plat':14} {'fetched':>7} {'created':>7} {'updated':>7} {'rejected':>8}"
        self.stdout.write(header)
        self.stdout.write("-" * len(header))

        totals = {"fetched": 0, "created": 0, "updated": 0, "rejected": 0}
        for src in qs:
            try:
                if opts["fetch_only"]:
                    jobs = orch.scrape_source_fetch_only(src) if hasattr(
                        orch, "scrape_source_fetch_only") else []
                    metrics = {"fetched": len(jobs), "created": 0, "updated": 0,
                               "rejected_total": 0, "rejected": {}}
                else:
                    orch.scrape_source(src)
                    metrics = getattr(orch, "_last_run_metrics", None) or {
                        "fetched": 0, "created": 0, "updated": 0,
                        "rejected_total": 0, "rejected": {}}
            except Exception as e:
                self.stdout.write(
                    f"{src.slug:32} {(src.ats_platform or '?'):14} ERROR {type(e).__name__}: {e}"
                )
                continue

            self.stdout.write(
                f"{src.slug:32} {(src.ats_platform or '?'):14} "
                f"{metrics['fetched']:>7} {metrics['created']:>7} "
                f"{metrics['updated']:>7} {metrics['rejected_total']:>8}"
            )
            if metrics.get("rejected"):
                self.stdout.write(f"    rejections: {metrics['rejected']}")

            totals["fetched"] += metrics["fetched"]
            totals["created"] += metrics["created"]
            totals["updated"] += metrics["updated"]
            totals["rejected"] += metrics["rejected_total"]

        self.stdout.write("-" * len(header))
        self.stdout.write(
            f"{'TOTAL':32} {'':14} {totals['fetched']:>7} {totals['created']:>7} "
            f"{totals['updated']:>7} {totals['rejected']:>8}"
        )
