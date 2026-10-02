"""Rediscover ATS for failing/degraded sources and apply migration verdicts.

§9/§10: static seed lists rot (Notion/Plaid/Ramp all migrated Lever -> Ashby).
This command re-fingerprints a source's company against known ATS endpoints and,
when it finds the employer moved providers, records a MIGRATED verdict with
evidence — optionally creating the successor source and retiring the old one.

TRIGGER SELECTION (§3 of the production-scale directive) — a source qualifies
for rediscovery if ANY of these hold, not just "is already flagged degraded":
  1. --degraded-only: lifecycle_state == "degraded" (existing signal, fetched
     volume but persisted nothing — see Source.consecutive_zero_yield_runs).
  2. --min-zero-yield N: consecutive_zero_yield_runs >= N.
  3. --historically-productive: jobs_found_last_run == 0 on a source whose
     error_count is 0 (so it's not just a transient network blip) AND which
     has run at least once before (last_run_at is set) — i.e. "this used to
     return results and now silently returns zero", the exact pattern the
     Notion/Plaid/Ramp Lever->Ashby migration produced before anyone noticed.
  4. --repeated-errors N: error_count >= N (repeated fetch failures, which on
     a dead/retired board often manifest as HTTP 404/410 inside the
     connector's own exception handling rather than a clean empty list).
These are OR'd together (a source matching ANY selected trigger is probed);
omit all trigger flags to fall back to the original "all active sources"
behavior.

Usage:
  python manage.py rediscover_sources --degraded-only        # only sources flagged degraded/zero-yield
  python manage.py rediscover_sources --source notion-lever  # one source
  python manage.py rediscover_sources --apply                # actually create/retire (default: dry-run)
  python manage.py rediscover_sources --min-zero-yield 2     # only sources with >=N zero-yield runs
  python manage.py rediscover_sources --historically-productive  # ran before, now zero, no fetch errors
  python manage.py rediscover_sources --repeated-errors 3    # sources that have failed to fetch 3+ times in a row
"""
import requests
from django.db.models import Q
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.jobs.models import Source
from apps.scraper.pipeline.source_discovery import discover_ats, compare_for_migration


def _live_fetcher(url):
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "usam-source-discovery/1.0"})
        try:
            payload = r.json()
        except ValueError:
            payload = None
        return r.status_code, payload
    except requests.RequestException:
        return 0, None


class Command(BaseCommand):
    help = "Re-fingerprint failing sources and detect ATS migrations (§9/§10)."

    def add_arguments(self, parser):
        parser.add_argument("--source", type=str, default="")
        parser.add_argument("--degraded-only", action="store_true")
        parser.add_argument("--min-zero-yield", type=int, default=0)
        parser.add_argument(
            "--historically-productive", action="store_true",
            help=("Probe sources that have run before, had zero fetch errors, "
                  "but returned 0 jobs on their last run - the silent-migration "
                  "signature (e.g. Notion/Plaid/Ramp moving off Lever) rather "
                  "than a transient failure."),
        )
        parser.add_argument(
            "--repeated-errors", type=int, default=0,
            help="Probe sources with error_count >= N (repeated fetch failures, "
                 "e.g. a board returning HTTP 404/410 on every run).",
        )
        parser.add_argument("--apply", action="store_true",
                            help="Create successor + retire old source (default: dry-run)")

    def _company_slug(self, src):
        platform = (src.ats_platform or "").lower()
        slug = src.slug
        if platform and slug.endswith(f"-{platform}"):
            slug = slug[: -len(f"-{platform}")]
        return slug

    def handle(self, *args, **opts):
        qs = Source.objects.all()
        if opts["source"]:
            qs = qs.filter(slug=opts["source"])
        else:
            qs = qs.filter(is_active=True)

            # Trigger selection: OR together whichever flags were passed.
            # If none were passed, keep the original "probe everything active"
            # behavior (back-compat).
            triggers = Q()
            any_trigger = False
            if opts["degraded_only"]:
                triggers |= Q(lifecycle_state="degraded")
                any_trigger = True
            if opts["min_zero_yield"]:
                triggers |= Q(consecutive_zero_yield_runs__gte=opts["min_zero_yield"])
                any_trigger = True
            if opts["historically_productive"]:
                triggers |= (
                    Q(jobs_found_last_run=0)
                    & Q(error_count=0)
                    & Q(last_run_at__isnull=False)
                )
                any_trigger = True
            if opts["repeated_errors"]:
                triggers |= Q(error_count__gte=opts["repeated_errors"])
                any_trigger = True
            if any_trigger:
                qs = qs.filter(triggers)

        apply = opts["apply"]
        self.stdout.write(f"{'DRY-RUN' if not apply else 'APPLY'}: rediscovering {qs.count()} source(s)\n")

        for src in qs:
            company = self._company_slug(src)
            old_provider = (src.ats_platform or "").lower()
            result = discover_ats(company, fetcher=_live_fetcher)
            verdict = compare_for_migration(old_provider, result)

            src.last_discovery_at = timezone.now()
            self.stdout.write(
                f"{src.slug:28} {old_provider:14} -> {verdict['verdict']:8} "
                f"({verdict.get('reason', '')})"
            )

            # Evidence event — field names deliberately match the directive's
            # requested migration-record vocabulary (previous_source/
            # previous_provider/new_source/new_provider/evidence/confidence/
            # detected_at/review_status/migration_reason), persisted into the
            # EXISTING Source.migration_history JSONField rather than a new
            # table — this is append-only history on the record it concerns,
            # which is exactly what that field already exists for.
            event = {
                "detected_at": src.last_discovery_at.isoformat(),
                "previous_source": src.slug,
                "previous_provider": old_provider,
                "verdict": verdict["verdict"],
                "migration_reason": verdict.get("reason", ""),
                "evidence": verdict.get("evidence", []),
                "confidence": 1.0 if verdict["verdict"] == "MIGRATED" else 0.0,
                "review_status": "auto_applied" if apply else "pending_review",
            }

            if verdict["verdict"] == "ACTIVE":
                src.lifecycle_state = "active"
                src.consecutive_zero_yield_runs = 0
                src.record_migration_event(event)
                if apply:
                    src.save(update_fields=["lifecycle_state", "consecutive_zero_yield_runs",
                                            "migration_history", "last_discovery_at"])
                continue

            if verdict["verdict"] == "INVALID":
                src.lifecycle_state = "invalid"
                src.record_migration_event(event)
                if apply:
                    src.is_active = False
                    src.save(update_fields=["lifecycle_state", "is_active",
                                            "migration_history", "last_discovery_at"])
                self.stdout.write(self.style.WARNING(
                    f"    no ATS found; marked INVALID (kept for history)"))
                continue

            # MIGRATED — create successor, retire old, link + record evidence.
            new_provider = verdict["new_provider"]
            new_slug = f"{company}-{new_provider}"
            event["new_source"] = new_slug
            event["new_provider"] = new_provider
            self.stdout.write(self.style.SUCCESS(
                f"    MIGRATED {old_provider} -> {new_provider} "
                f"({verdict['job_count']} jobs at {new_slug})"))
            if not apply:
                # DRY-RUN: evidence is already fully visible on stdout above
                # (verdict, old/new provider, job count, successor slug) for
                # review before deciding to --apply. Consistent with the
                # ACTIVE/INVALID branches above, dry-run performs NO database
                # writes at all - record_migration_event() mutates the
                # in-memory object only and is intentionally not saved here.
                continue

            successor, created = Source.objects.get_or_create(
                slug=new_slug,
                defaults={
                    "name": src.name,
                    "url": verdict["new_endpoint"],
                    "type": "scraper",
                    "ats_platform": new_provider,
                    "is_active": True,
                    "lifecycle_state": "active",
                    "schedule_cron": src.schedule_cron or "0 */6 * * *",
                },
            )
            src.lifecycle_state = "migrated"
            src.is_active = False
            src.migrated_to = successor
            src.record_migration_event(event)
            src.save(update_fields=["lifecycle_state", "is_active", "migrated_to",
                                    "migration_history", "last_discovery_at"])
            self.stdout.write(
                f"    {'created' if created else 'reused'} successor {new_slug}; "
                f"old source retired (MIGRATED)")
