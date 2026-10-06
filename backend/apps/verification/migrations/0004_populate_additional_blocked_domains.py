"""Extend BlockedDomain with aggregator domains named explicitly in the
Master Resource Directive's Section S ("never mark these as verified direct
apply by default") and the discovery-only aggregator sections (C/D/E/F/G)
that were not yet in the DB-backed blocklist populated by migration 0003.

This is purely additive data (get_or_create, idempotent) — no code change,
no existing connector touched. closes a real gap: without these entries,
a job whose apply URL happened to resolve to one of these aggregators would
NOT be rejected by is_blocked_domain()/ATSFingerprintStage, even though the
directive explicitly says it must never be treated as a verified direct-apply
destination.
"""
from django.db import migrations

NEW_BLOCKED = [
    # Directive Section S explicit list, not already covered by migration 0003
    ("wellfound.com", "Wellfound internal apply is not a verified employer/ATS destination"),
    ("jooble.org", "Job aggregator (Master Resource Directive §E/§S)"),
    ("talent.com", "Job aggregator (Master Resource Directive §E/§S)"),
    ("careerjet.com", "Job aggregator (Master Resource Directive §E/§S)"),
    ("careerjet.com.eg", "Regional job aggregator (Master Resource Directive §E/§S)"),
    ("jobrapido.com", "Job aggregator (Master Resource Directive §E/§S)"),
    ("adzuna.com", "Job aggregator - discovery only (Master Resource Directive §E)"),
    ("reed.com", "Job aggregator (Master Resource Directive §E; reed.co.uk already blocked)"),
    # MENA aggregators (§F) not already covered
    ("forasna.com", "Regional aggregator (Master Resource Directive §F)"),
    ("mihnati.com", "Regional aggregator (Master Resource Directive §F)"),
    # Africa aggregators (§G)
    ("jobberman.com", "Regional aggregator (Master Resource Directive §G)"),
    ("brightermonday.com", "Regional aggregator (Master Resource Directive §G)"),
    ("myjobmag.com", "Regional aggregator (Master Resource Directive §G)"),
    ("careers24.com", "Regional aggregator (Master Resource Directive §G)"),
    ("pnet.co.za", "Regional aggregator (Master Resource Directive §G)"),
]


def forwards(apps, schema_editor):
    BlockedDomain = apps.get_model("verification", "BlockedDomain")
    for domain, reason in NEW_BLOCKED:
        BlockedDomain.objects.get_or_create(
            domain=domain, defaults={"reason": reason, "is_active": True},
        )


def backwards(apps, schema_editor):
    BlockedDomain = apps.get_model("verification", "BlockedDomain")
    domains = [d for d, _ in NEW_BLOCKED]
    BlockedDomain.objects.filter(domain__in=domains).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0003_populate_blocked_domains"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
