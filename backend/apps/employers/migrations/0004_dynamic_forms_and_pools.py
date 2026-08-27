from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employers', '0003_talentpool'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobposting',
            name='custom_form_fields',
            field=models.JSONField(blank=True, default=list, help_text='Custom application form fields as JSON schema'),
        ),
        migrations.AddField(
            model_name='jobapplication',
            name='custom_form_responses',
            field=models.JSONField(blank=True, default=dict, help_text='Candidate responses to custom application form fields'),
        ),
    ]
