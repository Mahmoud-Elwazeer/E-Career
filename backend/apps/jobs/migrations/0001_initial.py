import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(db_index=True, max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("logo_url", models.URLField(blank=True, max_length=500)),
                ("snippet", models.CharField(blank=True, max_length=300)),
                ("about", models.TextField(blank=True)),
                ("industry", models.CharField(choices=[("technology","Technology"),("finance","Finance"),("healthcare","Healthcare"),("education","Education"),("marketing","Marketing"),("engineering","Engineering"),("design","Design"),("sales","Sales"),("other","Other")], db_index=True, default="other", max_length=50)),
                ("website", models.URLField(blank=True, max_length=300)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
            options={"db_table": "jobs_company", "ordering": ["name"], "verbose_name": "Company", "verbose_name_plural": "Companies"},
        ),
        migrations.CreateModel(
            name="Source",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(db_index=True, max_length=100)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("url", models.URLField(max_length=300)),
                ("logo_url", models.URLField(blank=True, max_length=500)),
                ("type", models.CharField(choices=[("manual","Manual"),("scraper","Scraper"),("api","API")], default="manual", max_length=20)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
            options={"db_table": "jobs_source", "ordering": ["name"], "verbose_name": "Source", "verbose_name_plural": "Sources"},
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(db_index=True, max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("category", models.CharField(choices=[("skill","Skill"),("tool","Tool"),("language","Language"),("framework","Framework"),("general","General")], db_index=True, default="general", max_length=20)),
            ],
            options={"db_table": "jobs_tag", "ordering": ["name"], "verbose_name": "Tag", "verbose_name_plural": "Tags"},
        ),
        migrations.CreateModel(
            name="Job",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("title", models.CharField(db_index=True, max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("location", models.CharField(db_index=True, max_length=200)),
                ("location_type", models.CharField(choices=[("remote","Remote"),("onsite","On-Site"),("hybrid","Hybrid")], db_index=True, max_length=20)),
                ("industry", models.CharField(choices=[("technology","Technology"),("finance","Finance"),("healthcare","Healthcare"),("education","Education"),("marketing","Marketing"),("engineering","Engineering"),("design","Design"),("sales","Sales"),("other","Other")], db_index=True, max_length=50)),
                ("experience_level", models.CharField(choices=[("entry","Entry"),("mid","Mid"),("senior","Senior"),("lead","Lead")], db_index=True, max_length=20)),
                ("description", models.TextField()),
                ("salary_min", models.PositiveIntegerField(blank=True, null=True)),
                ("salary_max", models.PositiveIntegerField(blank=True, null=True)),
                ("salary_currency", models.CharField(blank=True, default="USD", max_length=10)),
                ("source_url", models.URLField(max_length=500)),
                ("posted_at", models.DateField(db_index=True)),
                ("deadline", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("active","Active"),("pending","Pending Review"),("archived","Archived")], db_index=True, default="active", max_length=20)),
                ("view_count", models.PositiveIntegerField(default=0)),
                ("click_count", models.PositiveIntegerField(default=0)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jobs", to="jobs.company")),
                ("source", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="jobs", to="jobs.source")),
            ],
            options={"db_table": "jobs_job", "ordering": ["-posted_at","-created_at"], "verbose_name": "Job", "verbose_name_plural": "Jobs"},
        ),
        migrations.CreateModel(
            name="JobTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="jobs.job")),
                ("tag", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="jobs.tag")),
            ],
            options={"db_table": "jobs_jobtag", "unique_together": {("job","tag")}},
        ),
        migrations.CreateModel(
            name="JobAlsoOnSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="jobs.job")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="jobs.source")),
            ],
            options={"db_table": "jobs_jobalsoonsource", "unique_together": {("job","source")}},
        ),
        migrations.AddField(
            model_name="job",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="jobs", through="jobs.JobTag", to="jobs.tag"),
        ),
        migrations.AddField(
            model_name="job",
            name="also_on_sources",
            field=models.ManyToManyField(blank=True, related_name="also_on_jobs", through="jobs.JobAlsoOnSource", to="jobs.source"),
        ),
    ]
