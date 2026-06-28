"""
Management command to run job scraping manually.
"""
from django.core.management.base import BaseCommand
from apps.jobs.models import Source
from apps.scraper.tasks import scrape_all_sources, scrape_source, process_and_store_jobs


class Command(BaseCommand):
    help = 'Run job scraping manually'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default=None,
            help='Scrape a specific source by slug'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='async_mode',
            help='Run as Celery task (asynchronous)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of sources to scrape'
        )
    
    def handle(self, *args, **options):
        source_slug = options['source']
        async_mode = options['async_mode']
        limit = options['limit']
        
        if source_slug:
            # Scrape a specific source
            try:
                source = Source.objects.get(slug=source_slug)
            except Source.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Source '{source_slug}' not found"))
                return
            
            self.stdout.write(f"Scraping source: {source.name}...")
            
            if async_mode:
                from apps.scraper.tasks import scrape_single_source
                result = scrape_single_source.delay(str(source.id))
                self.stdout.write(f"Task queued: {result.id}")
            else:
                jobs = scrape_source(source)
                added = process_and_store_jobs(jobs, source)
                self.stdout.write(
                    self.style.SUCCESS(f"Found {len(jobs)} jobs, added {added}")
                )
        
        else:
            # Scrape all active sources
            sources = Source.objects.filter(is_active=True)
            
            if limit:
                sources = sources[:limit]
            
            self.stdout.write(f"Scraping {sources.count()} active sources...")
            
            if async_mode:
                result = scrape_all_sources.delay()
                self.stdout.write(f"Task queued: {result.id}")
            else:
                result = scrape_all_sources()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Complete! Found {result.get('total_found', 0)} jobs, "
                        f"added {result.get('total_added', 0)} jobs"
                    )
                )