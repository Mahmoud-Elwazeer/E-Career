"""
Add fields to CareerProfile for UserProfile consolidation.

These fields previously existed only on the deprecated UserProfile model.
This migration adds them to CareerProfile so it becomes the single source
of truth for all user profile data.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('career', '0002_careergoal_alter_interviewsession_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='careerprofile',
            name='skills',
            field=models.JSONField(default=list, help_text='Flat skill name list extracted from CV'),
        ),
        migrations.AddField(
            model_name='careerprofile',
            name='education',
            field=models.JSONField(default=list, help_text='Education entries [{degree, institution, year}]'),
        ),
        migrations.AddField(
            model_name='careerprofile',
            name='languages',
            field=models.JSONField(default=list, help_text='Languages spoken [{language, level}]'),
        ),
        migrations.AddField(
            model_name='careerprofile',
            name='certifications',
            field=models.JSONField(default=list, help_text='Professional certifications [{name, issuer, year}]'),
        ),
        migrations.AddField(
            model_name='careerprofile',
            name='preferred_type',
            field=models.CharField(blank=True, help_text='full-time, part-time, contract, freelance', max_length=20),
        ),
        migrations.AddField(
            model_name='careerprofile',
            name='email_alerts',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='careerprofile',
            name='cv_uploaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
