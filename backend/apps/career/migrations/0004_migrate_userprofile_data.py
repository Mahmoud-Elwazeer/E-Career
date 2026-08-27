"""
Copy data from deprecated UserProfile into CareerProfile.

For users that have data in both models, CareerProfile takes precedence
for fields it already has populated. Only empty CareerProfile fields get
filled from UserProfile.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    CareerProfile = apps.get_model('career', 'CareerProfile')

    for up in UserProfile.objects.select_related('user').iterator():
        cp, created = CareerProfile.objects.get_or_create(user=up.user)

        changed = False

        # CV file — only if CareerProfile has none
        if up.cv_file and not cp.cv_file:
            cp.cv_file = up.cv_file
            cp.cv_uploaded_at = up.cv_uploaded_at
            cp.cv_parse_status = 'completed' if up.cv_parse_status == 'done' else up.cv_parse_status
            changed = True

        # Skills (flat list)
        if up.skills and not cp.skills:
            cp.skills = up.skills
            changed = True

        # Education
        if up.education and not cp.education:
            cp.education = up.education
            changed = True

        # Languages
        if up.languages and not cp.languages:
            cp.languages = up.languages
            changed = True

        # Certifications
        if up.certifications and not cp.certifications:
            cp.certifications = up.certifications
            changed = True

        # Experience
        if up.experience_years and not cp.experience_years:
            cp.experience_years = up.experience_years
            changed = True

        # Current role
        if up.current_role and not cp.current_role:
            cp.current_role = up.current_role
            changed = True

        # Portfolio
        if up.portfolio_url and not cp.portfolio_url:
            cp.portfolio_url = up.portfolio_url
            changed = True

        # Target roles (convert simple list to structured list)
        if up.desired_roles and not cp.target_roles:
            cp.target_roles = [{'role': r, 'priority': 'medium'} for r in up.desired_roles]
            changed = True

        # Target locations
        if up.desired_locations and not cp.target_locations:
            cp.target_locations = [{'city': loc, 'country': ''} for loc in up.desired_locations]
            changed = True

        # Salary
        if up.min_salary and not cp.target_salary_min:
            cp.target_salary_min = up.min_salary
            cp.target_salary_currency = up.salary_currency or 'EGP'
            changed = True

        # Remote preference
        if not created and up.open_to_remote != cp.open_to_remote:
            pass  # Don't override — CareerProfile value takes precedence
        elif created:
            cp.open_to_remote = up.open_to_remote
            changed = True

        # Alert preferences
        if up.alert_frequency and cp.alert_frequency == 'instant':
            cp.alert_frequency = up.alert_frequency
            changed = True

        cp.email_alerts = up.email_alerts

        # Preferred type
        if up.preferred_type and not cp.preferred_type:
            cp.preferred_type = up.preferred_type
            changed = True

        if changed:
            cp.save()


def backwards(apps, schema_editor):
    pass  # No reverse — data stays in CareerProfile


class Migration(migrations.Migration):

    dependencies = [
        ('career', '0003_careerprofile_consolidation_fields'),
        ('users', '0002_userprofile_jobmatchscore'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
