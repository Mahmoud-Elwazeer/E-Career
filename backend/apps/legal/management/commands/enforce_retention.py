"""
Scheduled retention enforcement — safe by default.

Usage:
  python manage.py enforce_retention              # DRY_RUN report only, no writes
  python manage.py enforce_retention --execute     # actually enforce (still skips
                                                    # any category without a legally-
                                                    # confirmed retention_period_days)
  python manage.py enforce_retention --batch-size 100

This command is intended to be wired into Celery Beat / cron on a recurring
cadence (e.g. daily). It is deliberately NOT auto-registered as a periodic
task yet — the directive requires production to stay in DRY_RUN until
retention periods are legally/business confirmed for a given category (see
RetentionPolicy.requires_legal_review). Beat scheduling is a separate,
explicit go-live step for whoever operates the schedule.
"""
import json

from django.core.management.base import BaseCommand

from apps.legal.retention_service import run_retention_enforcement


class Command(BaseCommand):
    help = "Enforce (or dry-run report on) data retention per RetentionPolicy. DRY_RUN by default."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute", action="store_true",
            help="Actually delete/anonymize aged data. Without this flag, nothing is written.",
        )
        parser.add_argument(
            "--batch-size", type=int, default=500,
            help="Max rows processed per enforceable category in this run.",
        )
        parser.add_argument(
            "--json", action="store_true",
            help="Emit the report as JSON (for log aggregation) instead of a human table.",
        )

    def handle(self, *args, **options):
        dry_run = not options["execute"]
        report = run_retention_enforcement(dry_run=dry_run, batch_size=options["batch_size"])

        if options["json"]:
            payload = {
                "dry_run": report.dry_run,
                "started_at": report.started_at.isoformat(),
                "total_candidates": report.total_candidates,
                "total_affected": report.total_affected,
                "total_failed": report.total_failed,
                "categories": [
                    {
                        "category": r.category, "enforceable": r.enforceable,
                        "reason": r.reason, "candidates_found": r.candidates_found,
                        "excluded_by_legal_hold": r.excluded_by_legal_hold,
                        "affected": r.affected, "failed": r.failed, "error": r.error,
                    }
                    for r in report.results
                ],
            }
            self.stdout.write(json.dumps(payload, indent=2))
            return

        mode = "DRY RUN (no writes)" if dry_run else "EXECUTE (writes applied)"
        self.stdout.write(self.style.WARNING(f"Retention enforcement — {mode}"))
        self.stdout.write("")
        for r in report.results:
            if r.failed:
                self.stdout.write(self.style.ERROR(f"  FAIL  {r.category:28} — {r.error}"))
                continue
            if not r.enforceable:
                self.stdout.write(f"  SKIP  {r.category:28} — {r.reason}")
                continue
            verb = "would affect" if dry_run else "affected"
            self.stdout.write(
                f"  {'DRY' if dry_run else 'RUN':5} {r.category:28} — "
                f"found={r.candidates_found} excluded_by_hold={r.excluded_by_legal_hold} {verb}={r.affected}"
            )
        self.stdout.write("")
        summary_style = self.style.ERROR if report.total_failed else self.style.SUCCESS
        self.stdout.write(summary_style(
            f"Totals: {report.total_candidates} candidates, {report.total_affected} affected, "
            f"{report.total_failed} category failure(s)."
        ))
        if dry_run and report.total_candidates:
            self.stdout.write(self.style.WARNING(
                "This was a dry run — re-run with --execute to actually enforce."
            ))
