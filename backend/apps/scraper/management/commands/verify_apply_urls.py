"""
Management command to verify apply URLs for all active jobs.
"""
from django.core.management.base import BaseCommand
from apps.scraper.tasks import verify_apply_urls


class Command(BaseCommand):
    help = 'Verify apply URLs for all active jobs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            dest='async_mode',
            help='Run as Celery task (asynchronous)'
        )
    
    def handle(self, *args, **options):
        async_mode = options['async_mode']
        
        self.stdout.write("Verifying apply URLs...")
        
        if async_mode:
            result = verify_apply_urls.delay()
            self.stdout.write(f"Task queued: {result.id}")
        else:
            result = verify_apply_urls()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Complete! Checked {result.get('checked', 0)} URLs, "
                    f"expired {result.get('expired', 0)} jobs"
                )
            )