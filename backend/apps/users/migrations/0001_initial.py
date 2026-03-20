import uuid
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
            name="SavedJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("saved_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="saved_jobs", to="accounts.user")),
                ("job", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="saves", to="jobs.job")),
            ],
            options={"db_table": "users_savedjob", "ordering": ["-saved_at"], "unique_together": {("user","job")}, "verbose_name": "Saved Job", "verbose_name_plural": "Saved Jobs"},
        ),
        migrations.CreateModel(
            name="Alert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("keyword", models.CharField(blank=True, max_length=200)),
                ("work_mode", models.CharField(blank=True, max_length=20)),
                ("industry", models.CharField(blank=True, max_length=50)),
                ("frequency", models.CharField(choices=[("instant","Instant"),("daily","Daily"),("weekly","Weekly")], db_index=True, default="daily", max_length=20)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="alerts", to="accounts.user")),
            ],
            options={"db_table": "users_alert", "ordering": ["-created_at"], "verbose_name": "Alert", "verbose_name_plural": "Alerts"},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("title", models.CharField(max_length=300)),
                ("body", models.TextField(blank=True, null=True)),
                ("type", models.CharField(blank=True, choices=[("alert_match","Alert Match"),("system","System"),("welcome","Welcome")], db_index=True, max_length=50, null=True)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("metadata", models.JSONField(blank=True, default=dict, null=True)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="accounts.user")),
            ],
            options={"db_table": "users_notification", "ordering": ["-created_at"], "verbose_name": "Notification", "verbose_name_plural": "Notifications"},
        ),
    ]
