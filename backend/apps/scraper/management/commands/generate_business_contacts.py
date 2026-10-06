"""Generate role-based BusinessContact pattern guesses for companies with a
known domain (Task #14). Pure pattern generation, no network calls, no
personal-email harvesting - see apps/jobs/business_contact.py module
docstring for the invariants this enforces.

Usage:
  python manage.py generate_business_contacts                  # all companies with a domain
  python manage.py generate_business_contacts --company-id 5
  python manage.py generate_business_contacts --roles careers,hr
"""
from django.core.management.base import BaseCommand

from apps.jobs.models import Company
from apps.jobs.business_contact import business_contact_service, GENERIC_ROLE_PREFIXES


class Command(BaseCommand):
    help = "Generate role-based business contact pattern guesses (careers@, hr@, ...) for companies with a known domain (§14)."

    def add_arguments(self, parser):
        parser.add_argument("--company-id", type=int, default=0)
        parser.add_argument("--roles", type=str, default="",
                             help=f"Comma-separated subset of {GENERIC_ROLE_PREFIXES}; default is all.")

    def handle(self, *args, **options):
        qs = Company.objects.filter(is_active=True).exclude(domain="")
        if options["company_id"]:
            qs = qs.filter(id=options["company_id"])

        roles = None
        if options["roles"]:
            roles = [r.strip() for r in options["roles"].split(",") if r.strip()]

        total_created = 0
        companies = list(qs)
        for company in companies:
            outcomes = business_contact_service.generate_for_company(company, roles=roles)
            created = [o for o in outcomes if o.created]
            total_created += len(created)
            for o in created:
                self.stdout.write(f"  {company.name}: {o.email}")

        self.stdout.write(self.style.SUCCESS(
            f"\nGenerated {total_created} new business contact(s) across {len(companies)} companies with a known domain."
        ))
