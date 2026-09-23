"""
Seed the ApprovedATS allow-list.

The direct-apply moat has two halves:
  - BlockedDomain (seeded via migration 0003) — aggregators that must NEVER be
    the final Apply destination (LinkedIn, Indeed, Bayt, Wuzzuf, Tanqeeb, …).
  - ApprovedATS (this command) — employer-owned ATS platforms whose apply URLs
    are trusted direct-source destinations.

Without ApprovedATS rows, the allow-list side of the moat is inert (every
non-blocked domain falls through as "maybe ok"), so trust scores stay low and
nothing gets auto-verified. This command populates the well-known employer ATS
providers the scraper connectors target.
"""
from django.core.management.base import BaseCommand
from apps.verification.models import ApprovedATS


# (domain, display name, optional url_pattern)
APPROVED_ATS = [
    ("greenhouse.io", "Greenhouse", "boards.greenhouse.io/*"),
    ("boards.greenhouse.io", "Greenhouse", "boards.greenhouse.io/*"),
    ("job-boards.greenhouse.io", "Greenhouse", ""),
    ("lever.co", "Lever", "jobs.lever.co/*"),
    ("jobs.lever.co", "Lever", "jobs.lever.co/*"),
    ("ashbyhq.com", "Ashby", "jobs.ashbyhq.com/*"),
    ("jobs.ashbyhq.com", "Ashby", "jobs.ashbyhq.com/*"),
    ("myworkdayjobs.com", "Workday", "*.myworkdayjobs.com/*"),
    ("smartrecruiters.com", "SmartRecruiters", "jobs.smartrecruiters.com/*"),
    ("jobs.smartrecruiters.com", "SmartRecruiters", ""),
    ("workable.com", "Workable", "apply.workable.com/*"),
    ("apply.workable.com", "Workable", ""),
    ("teamtailor.com", "Teamtailor", "*.teamtailor.com/*"),
    ("recruitee.com", "Recruitee", "*.recruitee.com/*"),
    ("bamboohr.com", "BambooHR", "*.bamboohr.com/*"),
    ("jobvite.com", "Jobvite", "jobs.jobvite.com/*"),
    ("personio.com", "Personio", ""),
    ("personio.de", "Personio", ""),
    ("icims.com", "iCIMS", "*.icims.com/*"),
    ("oraclecloud.com", "Oracle Cloud Recruiting", ""),
    ("successfactors.com", "SAP SuccessFactors", ""),
    ("breezy.hr", "Breezy HR", ""),
    ("workataable.com", "Workable (legacy)", ""),
]


class Command(BaseCommand):
    help = "Seed the ApprovedATS allow-list of trusted employer ATS domains."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would be created")

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write("=== DRY RUN ===")
            for domain, name, _ in APPROVED_ATS:
                self.stdout.write(f"  - {name}: {domain}")
            self.stdout.write(f"Would ensure {len(APPROVED_ATS)} approved ATS domains.")
            return

        created = 0
        for domain, name, pattern in APPROVED_ATS:
            _, is_new = ApprovedATS.objects.get_or_create(
                domain=domain,
                defaults={"name": name, "url_pattern": pattern, "is_active": True},
            )
            if is_new:
                created += 1
                self.stdout.write(f"Created: {name} ({domain})")
            else:
                self.stdout.write(f"Exists:  {name} ({domain})")

        self.stdout.write(self.style.SUCCESS(f"\nApprovedATS seeded. {created} new, {len(APPROVED_ATS) - created} existing."))
