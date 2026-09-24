"""
Seed real, sellable Packages for the Career platform.

Prices are in MINOR units (piastres) EGP. Employer packages link to the
existing `core.SubscriptionPlan` entitlement so a purchase grants real feature
access. Individual packages are defined for future individual entitlements.

This is real product data, not a fixture mock — the billing UI reads these.
"""
from django.core.management.base import BaseCommand

from apps.core.models import SubscriptionPlan
from apps.payments.models import Package
from apps.payments.references import Platform


# (slug, name, audience, price EGP minor units, interval, entitlement plan name)
PACKAGES = [
    # Individuals
    ("individual-free", "Free", "individual", 0, "one_time", None),
    ("individual-pro-monthly", "Pro (Monthly)", "individual", 9900, "month", None),
    ("individual-pro-yearly", "Pro (Yearly)", "individual", 99000, "year", None),
    # Employers — linked to entitlement plans
    ("employer-starter", "Starter", "employer", 49900, "month", "Starter"),
    ("employer-growth", "Growth", "employer", 149900, "month", "Growth"),
    ("employer-scale", "Scale", "employer", 499900, "month", "Scale"),
]

# Entitlement plans employer packages unlock (created if absent).
PLANS = {
    "Starter": {"job_posting_limit": 5, "candidate_search_limit": 100, "ai_features_enabled": False},
    "Growth": {"job_posting_limit": 25, "candidate_search_limit": 1000, "ai_features_enabled": True},
    "Scale": {"job_posting_limit": 0, "candidate_search_limit": 0, "ai_features_enabled": True},  # 0 = unlimited
}


class Command(BaseCommand):
    help = "Seed real Career packages (individual + employer) and their entitlement plans."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if options["dry_run"]:
            for slug, name, aud, price, interval, plan in PACKAGES:
                self.stdout.write(f"  - {name} [{aud}] {price/100:.2f} EGP / {interval}")
            return

        # Ensure entitlement plans exist.
        plan_objs = {}
        for plan_name, cfg in PLANS.items():
            plan, _ = SubscriptionPlan.objects.get_or_create(name=plan_name, defaults=cfg)
            plan_objs[plan_name] = plan

        created = 0
        for slug, name, aud, price, interval, plan_name in PACKAGES:
            _, is_new = Package.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name, "audience": aud, "platform_code": Platform.CAREER,
                    "price_amount": price, "currency": "EGP", "interval": interval,
                    "entitlement_plan": plan_objs.get(plan_name) if plan_name else None,
                    "is_active": True,
                },
            )
            if is_new:
                created += 1
                self.stdout.write(f"Created: {name} [{aud}]")
            else:
                self.stdout.write(f"Exists:  {name} [{aud}]")

        self.stdout.write(self.style.SUCCESS(f"\nSeeded packages. {created} new."))
