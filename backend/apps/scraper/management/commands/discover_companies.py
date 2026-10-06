"""Run the Company Discovery Engine (Task #13) across Company rows.

Enriches domain / careers_page_url / industry / headquarters using evidence
already captured by CompanyResolutionIdentity + Source + Job (see
apps/jobs/company_discovery.py for the full method). No network calls - this
is pure DB read + write, safe to run repeatedly (additive-only, never
overwrites a non-blank field).

Usage:
  python manage.py discover_companies                  # all active companies
  python manage.py discover_companies --company-id 5   # one company
  python manage.py discover_companies --dry-run         # report only, no writes
"""
from django.core.management.base import BaseCommand

from apps.jobs.models import Company
from apps.jobs.company_discovery import company_discovery_service


class Command(BaseCommand):
    help = "Enrich Company rows (domain/careers_page_url/industry/headquarters) from existing evidence (§13)."

    def add_arguments(self, parser):
        parser.add_argument("--company-id", type=int, default=0)
        parser.add_argument("--dry-run", action="store_true",
                             help="Report what WOULD be applied/flagged, without writing")

    def handle(self, *args, **options):
        qs = Company.objects.filter(is_active=True)
        if options["company_id"]:
            qs = qs.filter(id=options["company_id"])

        total_applied = 0
        total_conflicts = 0
        companies = list(qs)

        for company in companies:
            if options["dry_run"]:
                # Reuse the real evaluation logic without persisting - call
                # the private evaluators directly rather than .discover(),
                # since .discover() writes CompanyEnrichment rows + saves.
                svc = company_discovery_service
                outcomes = (
                    svc._discover_domain(company)
                    + svc._discover_careers_page_url(company)
                    + svc._discover_industry(company)
                    + svc._discover_headquarters(company)
                )
            else:
                outcomes = company_discovery_service.discover(company)

            for o in outcomes:
                if o.applied:
                    total_applied += 1
                    self.stdout.write(f"  {company.name}: {o.field_name} = {o.value!r} "
                                       f"(method={o.method}, confidence={o.confidence:.2f})")
                elif o.conflict:
                    total_conflicts += 1
                    self.stdout.write(self.style.WARNING(
                        f"  {company.name}: {o.field_name} CONFLICT - evidence suggests "
                        f"{o.value!r} but existing value is {o.evidence.get('existing_value')!r}"
                    ))

        label = "Would apply" if options["dry_run"] else "Applied"
        self.stdout.write(self.style.SUCCESS(
            f"\n{label} {total_applied} field(s) across {len(companies)} companies; "
            f"{total_conflicts} conflict(s) flagged for review."
        ))
