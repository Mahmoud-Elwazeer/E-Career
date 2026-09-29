# Generated for §9/§10 Source lifecycle state + migration tracking.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0008_job_field_provenance"),
    ]

    operations = [
        migrations.AddField(
            model_name="source",
            name="lifecycle_state",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("degraded", "Degraded"),
                    ("migrated", "Migrated"),
                    ("disabled", "Disabled"),
                    ("invalid", "Invalid"),
                ],
                db_index=True,
                default="active",
                help_text="Source health lifecycle (distinct from is_active on/off flag)",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="source",
            name="consecutive_zero_yield_runs",
            field=models.IntegerField(
                default=0,
                help_text="Runs in a row that fetched volume but persisted nothing new; "
                          "drives auto-DEGRADED and rediscovery triggers",
            ),
        ),
        migrations.AddField(
            model_name="source",
            name="migrated_to",
            field=models.ForeignKey(
                blank=True,
                help_text="Successor source after ATS migration",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="migrated_from",
                to="jobs.source",
            ),
        ),
        migrations.AddField(
            model_name="source",
            name="migration_history",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Append-only list of migration/rediscovery events with evidence",
            ),
        ),
        migrations.AddField(
            model_name="source",
            name="last_discovery_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="source",
            index=models.Index(
                fields=["lifecycle_state"], name="jobs_source_lifecycle_idx"
            ),
        ),
    ]
