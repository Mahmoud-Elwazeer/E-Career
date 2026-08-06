"""
Management command to run all scrapers via the orchestrator.

This command triggers the scraper orchestrator to fetch jobs from all
configured sources, with proper error handling and status tracking.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.scraper.orchestrator import orchestrator
from apps.scraper.tasks import scrape_all_sources
from apps.jobs.models import Source


class Command(BaseCommand):
    help = 'Run all scrapers via the orchestrator'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            dest='async_mode',
            help='Run as Celery task (asynchronous)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Show what would be scraped without actually scraping'
        )
        parser.add_argument(
            '--source',
            type=str,
            default=None,
            help='Scrape a specific source by slug'
        )
    
    def handle(self, *args, **options):
        async_mode = options['async_mode']
        dry_run = options['dry_run']
        source_slug = options['source']
        
        if dry_run:
            self.stdout.write("=== DRY RUN MODE ===")
            sources = Source.objects.filter(is_active=True)
            if source_slug:
                sources = sources.filter(slug=source_slug)
            
            self.stdout.write(f"Would scrape {sources.count()} active sources:")
            for source in sources:
                self.stdout.write(f"  - {source.name} ({source.slug})")
            return
        
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
                try:
                    jobs, added = orchestrator.scrape_source(source)
                    self.stdout.write(
                        self.style.SUCCESS(f"Found {len(jobs)} jobs, added {added}")
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error: {e}"))
        else:
            # Scrape all active sources
            sources = Source.objects.filter(is_active=True)
            self.stdout.write(f"Scraping {sources.count()} active sources...")
            
            if async_mode:
                result = scrape_all_sources.delay()
                self.stdout.write(f"Task queued: {result.id}")
            else:
                try:
                    # Use orchestrator for full run
                    result = orchestrator.scrape_all_sources()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Complete! Found {result.get('total_found', 0)} jobs, "
                            f"added {result.get('total_added', 0)}"
                        )
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error: {e}"))