import uuid
import apps.core.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeatureFlag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("key", models.CharField(db_index=True, max_length=100, unique=True)),
                ("label", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, null=True)),
                ("is_enabled", models.BooleanField(default=False)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={"db_table": "core_featureflag", "ordering": ["key"], "verbose_name": "Feature Flag", "verbose_name_plural": "Feature Flags"},
        ),
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(db_index=True, max_length=200)),
                ("target_type", models.CharField(blank=True, db_index=True, max_length=100)),
                ("target_id", models.CharField(blank=True, max_length=100)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to="accounts.user")),
            ],
            options={"db_table": "core_activitylog", "ordering": ["-created_at"], "verbose_name": "Activity Log", "verbose_name_plural": "Activity Logs"},
        ),
        migrations.CreateModel(
            name="Media",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("filename", models.CharField(max_length=255)),
                ("file", models.FileField(upload_to=apps.core.models.media_upload_path)),
                ("size", models.PositiveIntegerField()),
                ("mime_type", models.CharField(max_length=100)),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="uploaded_media", to="accounts.user")),
            ],
            options={"db_table": "core_media", "ordering": ["-created_at"], "verbose_name": "Media", "verbose_name_plural": "Media"},
        ),
    ]
