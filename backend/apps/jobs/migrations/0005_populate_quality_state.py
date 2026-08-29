"""
Data migration: populate quality_state from existing status + is_expired.

Mapping:
  status='active'  + is_expired=False  → 'active'
  status='active'  + is_expired=True   → 'expired'
  status='pending'                     → 'needs_verification'
  status='rejected'                    → 'rejected'
  status='archived'                    → 'archived'
  status='expired'  (invalid legacy)   → 'expired'
  anything else                        → 'needs_verification'
"""

from django.db import migrations


def populate_quality_state(apps, schema_editor):
    Job = apps.get_model("jobs", "Job")

    Job.objects.filter(status="active", is_expired=False).update(quality_state="active")
    Job.objects.filter(status="active", is_expired=True).update(quality_state="expired")
    Job.objects.filter(status="pending").update(quality_state="needs_verification")
    Job.objects.filter(status="rejected").update(quality_state="rejected")
    Job.objects.filter(status="archived").update(quality_state="archived")
    Job.objects.filter(status="expired").update(quality_state="expired")


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0004_add_quality_state"),
    ]

    operations = [
        migrations.RunPython(populate_quality_state, migrations.RunPython.noop),
    ]
