from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('employers', '0002_talentdiscovery_knockoutquestion_candidateranking'),
    ]

    operations = [
        migrations.CreateModel(
            name='TalentPool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('employer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='talent_pools', to='employers.employerprofile')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('employer', 'name')},
            },
        ),
        migrations.CreateModel(
            name='TalentPoolCandidate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tags', models.JSONField(default=list, help_text='Employer-defined tags')),
                ('notes', models.TextField(blank=True)),
                ('rating', models.IntegerField(blank=True, help_text='Employer rating 1-5', null=True)),
                ('source', models.CharField(choices=[('manual', 'Manual Add'), ('search', 'From Search'), ('application', 'From Application'), ('recommendation', 'AI Recommendation')], default='manual', max_length=30)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('pool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='candidates', to='employers.talentpool')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='talent_pool_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-added_at'],
                'unique_together': {('pool', 'user')},
            },
        ),
    ]
