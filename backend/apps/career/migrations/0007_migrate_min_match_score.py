"""
Copy min_match_score from UserProfile to CareerProfile where CareerProfile
still has the default (0.6) and UserProfile has a custom value.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    CareerProfile = apps.get_model('career', 'CareerProfile')

    for up in UserProfile.objects.filter(
        min_match_score__isnull=False
    ).exclude(min_match_score=0.7).select_related('user').iterator():
        CareerProfile.objects.filter(
            user=up.user,
            min_match_score=0.6,
        ).update(min_match_score=up.min_match_score)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('career', '0006_add_is_discoverable'),
        ('users', '0004_convert_min_match_score_to_float'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
