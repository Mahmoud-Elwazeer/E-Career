"""
Data migration: convert min_match_score from int (0-100) to float (0-1).

Idempotent: values already in 0-1 range are left unchanged.
"""
from django.db import migrations, models


def convert_scores_forward(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    # Only convert values > 1 (i.e., still in 0-100 scale)
    profiles = UserProfile.objects.filter(min_match_score__gt=1)
    for profile in profiles.iterator(chunk_size=500):
        profile.min_match_score = profile.min_match_score / 100.0
        profile.save(update_fields=['min_match_score'])


def convert_scores_reverse(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    # Convert back: values in 0-1 range become 0-100
    profiles = UserProfile.objects.filter(min_match_score__lte=1)
    for profile in profiles.iterator(chunk_size=500):
        profile.min_match_score = int(profile.min_match_score * 100)
        profile.save(update_fields=['min_match_score'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_notification_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='min_match_score',
            field=models.FloatField(
                default=0.7,
                help_text='Only alert for jobs scoring above this threshold (0-1)',
            ),
        ),
        migrations.RunPython(
            convert_scores_forward,
            convert_scores_reverse,
        ),
    ]
