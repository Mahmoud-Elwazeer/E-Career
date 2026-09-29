"""
Setup REAL, scrapable, moat-compliant job sources for USAM Career.

The previous version seeded aggregator/careers-landing URLs (LinkedIn, Bayt,
Indeed, Glassdoor, McKinsey…) with NO `ats_platform`. That was doubly broken:
  1. The orchestrator dispatches by `source.ats_platform`; with it blank every
     source hit the "Unknown platform -> return []" branch, so NOTHING scraped.
  2. Those aggregator domains are on the BlockedDomain list and violate the
     platform's direct-apply moat — they can never be a valid Apply source.

This version seeds employer-owned ATS boards (Greenhouse / Lever / Ashby) whose
PUBLIC JSON APIs the connectors already know how to read, with the correct
`ats_platform` and `type='scraper'`. The orchestrator derives the connector
`company_slug` from `source.slug` by stripping the trailing `-{platform}`.

Add/adjust the list as coverage grows. This is a seed of well-known public
boards to prove the pipeline end-to-end and give real, verifiable jobs; the
long-term source registry is admin-managed.
"""
from django.core.management.base import BaseCommand
from apps.jobs.models import Source


# (company_slug, display name, ats_platform)
# slug MUST end with -{ats_platform} so the orchestrator can derive the board id.
SOURCES = [
    # ── Greenhouse public boards (api.greenhouse.io/v1/boards/{slug}/jobs) ──
    ("stripe-greenhouse", "Stripe", "greenhouse"),
    ("airbnb-greenhouse", "Airbnb", "greenhouse"),
    ("gitlab-greenhouse", "GitLab", "greenhouse"),
    ("robinhood-greenhouse", "Robinhood", "greenhouse"),
    ("databricks-greenhouse", "Databricks", "greenhouse"),
    ("figma-greenhouse", "Figma", "greenhouse"),
    ("discord-greenhouse", "Discord", "greenhouse"),
    ("brex-greenhouse", "Brex", "greenhouse"),

    # ── Lever public boards (api.lever.co/v0/postings/{slug}) ──
    # Verified live 2026-09-21: the prior seed (netflix/plaid/ramp/notion) all
    # 404'd because those companies migrated OFF Lever (Notion+Plaid→Ashby,
    # Ramp→Ashby, Netflix→own Eightfold board with no public JSON API). The
    # connector code was fine; only the slugs were stale. Replaced with boards
    # confirmed to return real postings via api.lever.co.
    ("spotify-lever", "Spotify", "lever"),      # verified 80 jobs
    ("gopuff-lever", "Gopuff", "lever"),        # verified 788 jobs
    ("ro-lever", "Ro", "lever"),                # verified 54 jobs

    # ── Ashby public boards (api.ashbyhq.com/posting-api/job-board/{slug}) ──
    ("openai-ashby", "OpenAI", "ashby"),
    ("linear-ashby", "Linear", "ashby"),
    ("ramp-ashby", "Ramp (Ashby)", "ashby"),
    ("notion-ashby", "Notion", "ashby"),        # migrated off Lever; verified 128 jobs
    ("plaid-ashby", "Plaid", "ashby"),          # migrated off Lever; verified 121 jobs

    # ── Eightfold AI careers hubs (§10) ──
    # Netflix runs on Eightfold, not a classic ATS. Verified live 2026-09-29:
    # explore.jobs.netflix.net/api/apply/v2/jobs?domain=netflix.com -> 474
    # positions, each with a direct canonicalPositionUrl (moat-compliant).
    ("netflix-eightfold", "Netflix", "eightfold"),

    # ── Workday CXS public API (§11) — browser-free ──
    # Verified live 2026-09-29: nvidia.wd5.myworkdayjobs.com CXS API -> total
    # 2000, direct apply URLs on the employer's own Workday host. Tenant/site/
    # server resolved from WORKDAY_TENANTS in the connector.
    ("nvidia-workday", "NVIDIA", "workday"),
]


class Command(BaseCommand):
    help = "Setup real, moat-compliant ATS scraping sources (Greenhouse/Lever/Ashby)."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing sources first")
        parser.add_argument(
            "--purge-aggregators",
            action="store_true",
            help="Deactivate legacy aggregator sources (no ats_platform) instead of scraping them",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
        parser.add_argument(
            "--deactivate-stale",
            action="store_true",
            help=(
                "Deactivate scraper sources whose slug is no longer in the seed "
                "list (e.g. boards that migrated ATS and now 404). Keeps the DB "
                "aligned with verified-live boards instead of running dead slugs."
            ),
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Source.objects.all().delete()
            self.stdout.write("Cleared existing sources")

        if options["purge_aggregators"]:
            # Anything without an ats_platform can't be scraped and is likely a
            # blocklisted aggregator — deactivate so it never runs or misleads.
            n = Source.objects.filter(ats_platform="").update(is_active=False)
            self.stdout.write(self.style.WARNING(f"Deactivated {n} legacy source(s) without an ATS platform"))

        if options["dry_run"]:
            self.stdout.write("=== DRY RUN ===")
            for slug, name, platform in SOURCES:
                self.stdout.write(f"  - {name}: {slug} [{platform}]")
            self.stdout.write(f"Would ensure {len(SOURCES)} scraper sources.")
            return

        created = 0
        for slug, name, platform in SOURCES:
            source, is_new = Source.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "url": _board_url(slug, platform),
                    "type": "scraper",
                    "ats_platform": platform,
                    "is_active": True,
                    "schedule_cron": "0 */6 * * *",
                },
            )
            if is_new:
                created += 1
                self.stdout.write(f"Created: {name} [{platform}]")
            else:
                # Backfill platform/type on pre-existing rows so they actually scrape.
                changed = False
                if not source.ats_platform:
                    source.ats_platform = platform
                    changed = True
                if source.type != "scraper":
                    source.type = "scraper"
                    changed = True
                if changed:
                    source.save(update_fields=["ats_platform", "type"])
                    self.stdout.write(f"Updated: {name} [{platform}]")
                else:
                    self.stdout.write(f"Exists:  {name} [{platform}]")

        if options["deactivate_stale"]:
            seed_slugs = {slug for slug, _, _ in SOURCES}
            stale = Source.objects.filter(type="scraper", is_active=True).exclude(slug__in=seed_slugs)
            stale_list = list(stale.values_list("slug", flat=True))
            n = stale.update(is_active=False)
            if n:
                self.stdout.write(self.style.WARNING(f"Deactivated {n} stale scraper source(s): {', '.join(stale_list)}"))
            else:
                self.stdout.write("No stale scraper sources to deactivate.")

        self.stdout.write(self.style.SUCCESS(f"\nSetup complete! {created} new scraper source(s)."))
        self.stdout.write("Next: run `python manage.py run_scrapers` to ingest + verify jobs.")


def _board_url(slug: str, platform: str) -> str:
    company = slug.rsplit(f"-{platform}", 1)[0]
    if platform == "greenhouse":
        return f"https://boards.greenhouse.io/{company}"
    if platform == "lever":
        return f"https://jobs.lever.co/{company}"
    if platform == "ashby":
        return f"https://jobs.ashbyhq.com/{company}"
    if platform == "eightfold":
        # Eightfold careers hubs are per-tenant; the connector resolves the
        # exact host/domain from its registry. Use a stable landing URL.
        return f"https://explore.jobs.{company}.net/careers"
    if platform == "workday":
        # Workday host (tenant.wdN.myworkdayjobs.com) + site are resolved from
        # WORKDAY_TENANTS in the connector; use a generic landing URL here.
        return f"https://{company}.myworkdayjobs.com/"
    return f"https://{company}.com/careers"
