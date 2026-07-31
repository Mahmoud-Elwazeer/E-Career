"""
Management Command: sync_search

Sync all jobs from PostgreSQL to Typesense search index.

Usage:
    python manage.py sync_search [--batch-size N] [--dry-run]
"""

import logging
from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from apps.jobs.models import Job
from apps.search.services import search_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Sync all jobs to the search index."""
    
    help = "Sync all jobs from PostgreSQL to Typesense search index"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of jobs to process in each batch (default: 100)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing",
        )
        parser.add_argument(
            "--status",
            type=str,
            default="active",
            help="Job status to sync (default: active)",
        )
    
    def handle(self, *args, **options):
        batch_size = options.get("batch_size", 100)
        dry_run = options.get("dry_run", False)
        status = options.get("status", "active")
        
        self.stdout.write(self.style.SUCCESS(f"Starting search sync (status={status}, batch_size={batch_size})"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Get jobs to sync
        queryset = Job.objects.filter(status=status)
        total_jobs = queryset.count()
        
        self.stdout.write(f"Found {total_jobs} jobs to sync")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Would sync {total_jobs} jobs to search index"))
            return
        
        # Sync jobs
        synced = 0
        failed = 0
        
        try:
            for job in queryset.iterator(chunk_size=batch_size):
                try:
                    result = search_service.sync_job(job)
                    if result:
                        synced += 1
                    else:
                        failed += 1
                        logger.warning(f"Failed to sync job {job.id}")
                except Exception as e:
                    failed += 1
                    logger.error(f"Error syncing job {job.id}: {e}")
                
                # Progress indicator
                if synced % batch_size == 0:
                    self.stdout.write(f"  Synced {synced}/{total_jobs} jobs...")
            
            self.stdout.write(self.style.SUCCESS(f"\nSync complete: {synced} synced, {failed} failed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Sync failed: {e}"))
            raise