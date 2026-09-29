"""Connector matrix (§2/§19/§24): prove per-ATS END-TO-END ingestion.

Runs each active Source through the REAL ingestion funnel and prints a matrix
so we can see, per source, exactly where jobs are lost:

  FETCH -> NORMALIZE -> DIRECT APPLY -> QUALITY -> DEDUP -> PERSIST
        -> VERIFY -> PUBLISHABLE -> INDEX

Columns:
  fetched     raw postings returned by the connector
  norm        passed the NormalizedJob contract (§5)
  da_cand     had an apply url to check
  da_ok       apply url passed the direct/moat gate
  created     new Job rows persisted
  updated     existing jobs refreshed
  dupes       matched an existing job
  verified    verification engine confirmed
  publish     created AND verified (visible to users)
  indexed     pushed to the search backend
  errors      unexpected exceptions
  rejected    total clean rejects (breakdown printed below the row)

`--fetch-only` proves ONLY fetch capability (created=0 is expected then and is
NOT meaningful). Use write mode (default, or --write) for a true funnel.

Usage:
  python manage.py connector_matrix                 # all active sources (persists)
  python manage.py connector_matrix --platform greenhouse
  python manage.py connector_matrix --fetch-only    # NO persist, fetch counts only
  python manage.py connector_matrix --source stripe-greenhouse   # one source
  python manage.py connector_matrix --limit 5
"""
from django.core.management.base import BaseCommand

from apps.jobs.models import Source
from apps.scraper.orchestrator import ScraperOrchestrator


_EMPTY = {
    "fetched": 0, "normalized": 0, "created": 0, "updated": 0, "duplicates": 0,
    "verified": 0, "errors": 0, "direct_apply_candidate": 0,
    "direct_apply_verified": 0, "publishable": 0, "indexed": 0,
    "rejected_total": 0, "rejected": {}, "degraded": False,
}


class Command(BaseCommand):
    help = "Run each ATS source through the ingestion funnel and report a matrix."

    def add_arguments(self, parser):
        parser.add_argument("--platform", type=str, default="")
        parser.add_argument("--source", type=str, default="", help="Single source slug")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument(
            "--fetch-only", action="store_true",
            help="Fetch ONLY (no persist). created/verified/indexed will be 0.",
        )

    def handle(self, *args, **opts):
        qs = Source.objects.filter(is_active=True)
        if opts["source"]:
            qs = qs.filter(slug=opts["source"])
        if opts["platform"]:
            qs = qs.filter(ats_platform__iexact=opts["platform"])
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        orch = ScraperOrchestrator()
        cols = (
            f"{'source':26} {'plat':13} {'fetch':>6} {'norm':>5} {'da_ok':>6} "
            f"{'creat':>6} {'updt':>5} {'dupe':>5} {'verif':>6} {'pub':>5} "
            f"{'index':>6} {'err':>4} {'rej':>5}"
        )
        self.stdout.write(cols)
        self.stdout.write("-" * len(cols))

        totals = dict(_EMPTY)
        degraded_sources = []
        for src in qs:
            try:
                if opts["fetch_only"]:
                    jobs = orch.scrape_source_fetch_only(src) if hasattr(
                        orch, "scrape_source_fetch_only") else []
                    m = dict(_EMPTY, fetched=len(jobs))
                else:
                    orch.scrape_source(src)
                    m = dict(_EMPTY, **(getattr(orch, "_last_run_metrics", None) or {}))
            except Exception as e:
                self.stdout.write(
                    f"{src.slug:26} {(src.ats_platform or '?'):13} ERROR {type(e).__name__}: {e}"
                )
                continue

            self.stdout.write(
                f"{src.slug:26} {(src.ats_platform or '?'):13} "
                f"{m['fetched']:>6} {m['normalized']:>5} {m['direct_apply_verified']:>6} "
                f"{m['created']:>6} {m['updated']:>5} {m['duplicates']:>5} "
                f"{m['verified']:>6} {m['publishable']:>5} {m['indexed']:>6} "
                f"{m['errors']:>4} {m['rejected_total']:>5}"
                + ("  [DEGRADED]" if m.get("degraded") else "")
            )
            if m.get("rejected"):
                self.stdout.write(f"    rejections: {m['rejected']}")
            if m.get("degraded"):
                degraded_sources.append(src.slug)

            for k in ("fetched", "normalized", "created", "updated", "duplicates",
                      "verified", "errors", "direct_apply_candidate",
                      "direct_apply_verified", "publishable", "indexed",
                      "rejected_total"):
                totals[k] += m.get(k, 0)

        self.stdout.write("-" * len(cols))
        self.stdout.write(
            f"{'TOTAL':26} {'':13} "
            f"{totals['fetched']:>6} {totals['normalized']:>5} {totals['direct_apply_verified']:>6} "
            f"{totals['created']:>6} {totals['updated']:>5} {totals['duplicates']:>5} "
            f"{totals['verified']:>6} {totals['publishable']:>5} {totals['indexed']:>6} "
            f"{totals['errors']:>4} {totals['rejected_total']:>5}"
        )
        if opts["fetch_only"]:
            self.stdout.write(
                self.style.WARNING(
                    "\nFETCH-ONLY: created/verified/indexed are 0 by design. "
                    "Run without --fetch-only to prove persistence."
                )
            )
        if degraded_sources:
            self.stdout.write(
                self.style.WARNING(f"\nDEGRADED sources: {', '.join(degraded_sources)}")
            )
