"""
Celery configuration for background tasks.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('ecareer')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# Celery Beat schedule
app.conf.beat_schedule = {
    # Scraper tasks
    'scrape-all-sources': {
        'task': 'apps.scraper.tasks.scrape_all_sources',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'verify-apply-urls': {
        'task': 'apps.scraper.tasks.verify_apply_urls',
        'schedule': crontab(minute=0, hour=2),  # 2 AM daily
    },
    'expire-old-jobs': {
        'task': 'apps.scraper.tasks.expire_old_jobs',
        'schedule': crontab(minute=0, hour=3),  # 3 AM daily
    },
    # Email tasks
    'send-job-alerts': {
        'task': 'apps.emails.tasks.send_job_alerts',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
    'send-weekly-digest': {
        'task': 'apps.emails.tasks.send_weekly_digest',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Monday 8 AM
    },
    'reset-email-counters': {
        'task': 'apps.emails.tasks.reset_email_account_counters',
        'schedule': crontab(hour=0, minute=0),  # Midnight daily
    },
    'send-re-engagement': {
        'task': 'apps.emails.tasks.send_re_engagement_emails',
        'schedule': crontab(hour=10, minute=0, day_of_week=0),  # Sunday 10 AM
    },
    # Verification tasks
    'verify-employer-posted-jobs': {
        'task': 'apps.scraper.tasks.verify_employer_posted_job',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'daily-liveness-check': {
        'task': 'apps.verification.tasks.daily_liveness_check',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    },
    'weekly-reverification': {
        'task': 'apps.verification.tasks.weekly_reverification',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM weekly
    },
    # Talent score tasks
    'recalculate-all-talent-scores': {
        'task': 'apps.career.tasks.batch_recalculate_talent_scores',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM weekly
    },
    # GDPR tasks
    'cleanup-old-gdpr-exports': {
        'task': 'apps.core.tasks.cleanup_old_gdpr_exports',
        'schedule': crontab(hour=4, minute=0),  # 4 AM daily
    },
}
