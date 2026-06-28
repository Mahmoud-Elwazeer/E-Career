"""
Management command to expire old jobs.
"""
from django.core.management.base import BaseCommand
from apps.scraper.tasks import expire_old_jobs


class Command(BaseCommand):
    help = 'Expire jobs older than max_job_age_days'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            dest='async_mode',
            help='Run as Celery task (asynchronous)'
        )
    
    def handle(self, *args, **options):
        async_mode = options['async_mode']
        
        self.stdout.write("Expiring old jobs...")
        
        if async_mode:
            result = expire_old_jobs.delay()
            self.stdout.write(f"Task queued: {result.id}")
        else:
            result = expire_old_jobs()
            self.stdout.write(
                self.style.SUCCESS(f"Complete! Expired {result.get('expired', 0)} jobs")
            )