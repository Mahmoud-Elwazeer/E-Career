from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="JobView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(blank=True, db_index=True, max_length=64)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("viewed_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("job", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="views", to="jobs.job")),
                ("user", models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="job_views", to="accounts.user")),
            ],
            options={"db_table": "analytics_jobview", "ordering": ["-viewed_at"], "verbose_name": "Job View", "verbose_name_plural": "Job Views"},
        ),
        migrations.CreateModel(
            name="JobClick",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(blank=True, db_index=True, max_length=64)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("clicked_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("job", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="clicks", to="jobs.job")),
                ("source", models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="clicks", to="jobs.source")),
                ("user", models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="job_clicks", to="accounts.user")),
            ],
            options={"db_table": "analytics_jobclick", "ordering": ["-clicked_at"], "verbose_name": "Job Click", "verbose_name_plural": "Job Clicks"},
        ),
        migrations.CreateModel(
            name="SearchLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("query", models.CharField(blank=True, db_index=True, max_length=500)),
                ("filters", models.JSONField(blank=True, default=dict)),
                ("results_count", models.PositiveIntegerField(default=0)),
                ("session_key", models.CharField(blank=True, max_length=64)),
                ("searched_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="search_logs", to="accounts.user")),
            ],
            options={"db_table": "analytics_searchlog", "ordering": ["-searched_at"], "verbose_name": "Search Log", "verbose_name_plural": "Search Logs"},
        ),
    ]
