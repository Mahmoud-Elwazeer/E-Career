"""
Populate BlockedDomain table from the union of all three hardcoded blocklists.
"""
from django.db import migrations

BLOCKED = [
    ("linkedin.com", "Job aggregator"),
    ("indeed.com", "Job aggregator"),
    ("glassdoor.com", "Job aggregator"),
    ("ziprecruiter.com", "Job aggregator"),
    ("monster.com", "Job aggregator"),
    ("careerbuilder.com", "Job aggregator"),
    ("dice.com", "Job aggregator"),
    ("simplyhired.com", "Job aggregator"),
    ("snagajob.com", "Job aggregator"),
    ("bayt.com", "Regional aggregator"),
    ("wuzzuf.net", "Regional aggregator"),
    ("wuzzuf.com", "Regional aggregator"),
    ("gulftalent.com", "Regional aggregator"),
    ("naukri.com", "Regional aggregator"),
    ("naukrigulf.com", "Regional aggregator"),
    ("seek.com.au", "Regional aggregator"),
    ("seek.com", "Regional aggregator"),
    ("reed.co.uk", "Regional aggregator"),
    ("akhtaboot.com", "Regional aggregator"),
    ("tanqeeb.com", "Regional aggregator"),
    ("dubizzle.com", "Regional aggregator"),
    ("jobgenie.com", "Job aggregator"),
    ("facebook.com", "Social media"),
    ("twitter.com", "Social media"),
    ("instagram.com", "Social media"),
]


def forwards(apps, schema_editor):
    BlockedDomain = apps.get_model('verification', 'BlockedDomain')
    for domain, reason in BLOCKED:
        BlockedDomain.objects.get_or_create(
            domain=domain,
            defaults={'reason': reason, 'is_active': True},
        )


def backwards(apps, schema_editor):
    BlockedDomain = apps.get_model('verification', 'BlockedDomain')
    domains = [d for d, _ in BLOCKED]
    BlockedDomain.objects.filter(domain__in=domains).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0002_verificationresult_admin_override_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
