"""Rediscover ATS for failing/degraded sources and apply migration verdicts.

§9/§10: static seed lists rot (Notion/Plaid/Ramp all migrated Lever -> Ashby).
This command re-fingerprints a source's company against known ATS endpoints and,
when it finds the employer moved providers, records a MIGRATED verdict with
evidence — optionally creating the successor source and retiring the old one.

Usage:
  python manage.py rediscover_sources --degraded-only        # only sources flagged degraded/zero-yield
  python manage.py rediscover_sources --source notion-lever  # one source
  python manage.py rediscover_sources --apply                # actually create/retire (default: dry-run)
  python manage.py rediscover_sources --min-zero-yield 2     # only sources with >=N zero-yield runs
"""
import requests
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
        if opts["degraded_only"]:
            qs = qs.filter(lifecycle_state="degraded")
        if opts["min_zero_yield"]:
            qs = qs.filter(consecutive_zero_yield_runs__gte=opts["min_zero_yield"])

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

            event = {
                "at": src.last_discovery_at.isoformat(),
                "old_provider": old_provider,
                "verdict": verdict["verdict"],
                "reason": verdict.get("reason", ""),
                "evidence": verdict.get("evidence", []),
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
            self.stdout.write(self.style.SUCCESS(
                f"    MIGRATED {old_provider} -> {new_provider} "
                f"({verdict['job_count']} jobs at {new_slug})"))
            if not apply:
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
            src.record_migration_event({**event, "successor_slug": new_slug})
            src.save(update_fields=["lifecycle_state", "is_active", "migrated_to",
                                    "migration_history", "last_discovery_at"])
            self.stdout.write(
                f"    {'created' if created else 'reused'} successor {new_slug}; "
                f"old source retired (MIGRATED)")
