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
}