from __future__ import annotations

import time
import structlog
from django.core.management.base import BaseCommand

from apps.jobs.models import Job
from apps.search.service import get_search_service
from apps.search.document import job_to_search_document

logger = structlog.get_logger()

BATCH_SIZE = 250


class Command(BaseCommand):
    help = "Sync all active jobs to Typesense search index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--recreate",
            action="store_true",
            help="Drop and recreate the collection before syncing",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=BATCH_SIZE,
            help="Number of documents per batch",
        )

    def handle(self, *args, **options):
        service = get_search_service()

        if options["recreate"]:
            self.stdout.write("Dropping and recreating jobs collection...")
            service.recreate_collection()
        else:
            service.ensure_collection()

        batch_size = options["batch_size"]
        # Filter on quality_state (QUALITY_VISIBLE_STATES), NOT status="active".
        # Job.status is set once by VerificationEngine's first verification
        # pass and is never corrected afterward - a job whose trust_score was
        # briefly low right after creation gets status="rejected" permanently,
        # even after later re-scrapes/re-verification mark it
        # quality_state="probably_active" or "direct_verified" (confirmed
        # live: 3572 jobs were probably_active+rejected, 246 were
        # direct_verified+rejected). quality_state is the field the rest of
        # the platform (Job.objects.visible(), verify_pipeline_e2e) treats as
        # authoritative for visibility - sync_typesense must match that or it
        # silently excludes the vast majority of real scraped jobs.
        jobs_qs = (
            Job.objects.visible()
            .select_related("company")
            .prefetch_related("tags")
            .order_by("id")
        )

        total = jobs_qs.count()
        self.stdout.write(f"Syncing {total} jobs to Typesense (batch size: {batch_size})...")

        indexed = 0
        start_time = time.time()

        for offset in range(0, total, batch_size):
            batch = jobs_qs[offset : offset + batch_size]
            documents = [job_to_search_document(job) for job in batch]
            count = service.index_jobs_batch(documents)
            indexed += count
            self.stdout.write(f"  Indexed {indexed}/{total} ({indexed * 100 // total}%)")

        elapsed = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Indexed {indexed}/{total} jobs in {elapsed:.1f}s"
            )
        )
        logger.info(
            "typesense_full_sync_complete",
            total=total,
            indexed=indexed,
            duration_seconds=round(elapsed, 1),
        )
