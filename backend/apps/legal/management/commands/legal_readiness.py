"""
Report overall Legal/Privacy launch readiness.

Usage:
  python manage.py legal_readiness             # human-readable report
  python manage.py legal_readiness --json      # machine-readable (CI/ops)

Exit code is always 0 (this is a reporting command, not a gate) — ops
tooling that wants to gate a deploy on this should parse the JSON
`overall_state` field itself and decide what to do with BLOCKED.

This command NEVER mutates data and NEVER prints secrets — it only reads
apps.legal domain tables and the non-sensitive PLATFORM_BASE_CURRENCY
setting. It does not and cannot claim "fully compliant"; READY only means
the specific, enumerated checks below have passed.
"""
import json

from django.core.management.base import BaseCommand

from apps.legal.readiness_service import check_legal_readiness

_STATE_STYLE = {
    "READY": "SUCCESS",
    "LEGAL_REVIEW_REQUIRED": "WARNING",
    "CONFIGURATION_REQUIRED": "WARNING",
    "BLOCKED": "ERROR",
}


class Command(BaseCommand):
    help = (
        "Report Legal/Privacy launch readiness: READY, CONFIGURATION_REQUIRED, "
        "LEGAL_REVIEW_REQUIRED, or BLOCKED, with a specific reason for every "
        "check that isn't READY. Read-only; never exposes secrets."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--json", action="store_true",
            help="Emit the report as JSON instead of a human-readable table.",
        )

    def handle(self, *args, **options):
        report = check_legal_readiness()

        if options["json"]:
            payload = {
                "overall_state": report.overall_state,
                "checks": [
                    {"key": c.key, "state": c.state, "message": c.message}
                    for c in report.checks
                ],
            }
            self.stdout.write(json.dumps(payload, indent=2))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("Legal/Privacy Readiness Report"))
        self.stdout.write("")
        for c in report.checks:
            style_name = _STATE_STYLE.get(c.state, "NOTICE")
            style = getattr(self.style, style_name, self.style.NOTICE)
            self.stdout.write(f"  [{c.state:24}] {c.key:30} {c.message}")
        self.stdout.write("")
        overall_style = getattr(self.style, _STATE_STYLE.get(report.overall_state, "NOTICE"))
        self.stdout.write(overall_style(f"OVERALL: {report.overall_state}"))
        if report.overall_state == "READY":
            self.stdout.write(
                "Note: READY means every known, checkable gap tracked by this command "
                "is closed. It is NOT a claim of full legal compliance or a substitute "
                "for legal counsel sign-off."
            )
