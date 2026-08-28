"""
Management Command: embed_jobs

Generate embeddings for all jobs and index them via pgvector.

Usage:
    python manage.py embed_jobs
    python manage.py embed_jobs --limit 100  # Test with first 100
    python manage.py embed_jobs --force  # Re-embed existing
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.jobs.models import Job
from apps.vectors.service import get_vector_service, JOBS_COLLECTION
from apps.vectors.plugins.vector_plugin import VectorDocument

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Bulk embed jobs."""

    help = "Generate embeddings for jobs and index in vector database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of jobs to embed (for testing)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-embed jobs that are already indexed",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Batch size for embedding generation (default: 50)",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")
        force = options.get("force", False)
        batch_size = options.get("batch_size", 50)

        self.stdout.write(self.style.SUCCESS("Starting job embedding"))

        vector_service = get_vector_service()

        # Ensure collection exists
        if not vector_service.vector_plugin.collection_exists(JOBS_COLLECTION):
            self.stdout.write("Creating jobs collection...")
            vector_service.vector_plugin.create_collection(
                name=JOBS_COLLECTION,
                vector_size=1024,
                distance="cosine",
            )

        # Get jobs to embed
        queryset = Job.objects.filter(
            verification__status="verified",
            verification__trust_score__gte=0.4,
        ).select_related("company", "verification")

        if limit:
            queryset = queryset[:limit]

        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("No jobs to embed"))
            return

        self.stdout.write(f"Embedding {total_count} jobs in batches of {batch_size}")

        embedded = 0
        failed = 0

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = list(queryset[i:i+batch_size])

            try:
                # Build embedding texts
                texts = []
                for job in batch:
                    text = self._job_to_text(job)
                    texts.append(text)

                # Generate embeddings
                embeddings = vector_service.generate_embeddings(
                    texts=texts,
                    input_type="search_document",
                )

                # Build documents
                documents = []
                for job, embedding in zip(batch, embeddings):
                    payload = {
                        "job_id": str(job.id),
                        "title": job.title,
                        "company": job.company.name if job.company else "",
                        "location": job.location or "",
                        "salary_min": job.salary_min or 0,
                        "salary_max": job.salary_max or 0,
                        "employment_type": job.employment_type or "",
                        "experience_level": job.experience_level or "",
                        "trust_score": job.verification.trust_score if hasattr(job, "verification") else 0.0,
                    }

                    documents.append(
                        VectorDocument(
                            id=str(job.id),
                            vector=embedding,
                            payload=payload,
                        )
                    )

                # Upsert to vector DB
                count = vector_service.vector_plugin.upsert(JOBS_COLLECTION, documents)
                embedded += count

                self.stdout.write(f"  Embedded {embedded}/{total_count} jobs")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Batch {i//batch_size + 1} failed: {e}")
                )
                failed += len(batch)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Embedding complete: {embedded} embedded, {failed} failed"
            )
        )

        # Show collection stats
        total_vectors = vector_service.vector_plugin.count(JOBS_COLLECTION)
        self.stdout.write(f"Total vectors in collection: {total_vectors}")

    def _job_to_text(self, job) -> str:
        """Convert job to embedding text."""
        parts = [
            f"Title: {job.title}",
            f"Company: {job.company.name if job.company else 'Unknown'}",
        ]

        if job.description:
            # Truncate description to avoid token limits
            desc = job.description[:2000]
            parts.append(f"Description: {desc}")

        if job.location:
            parts.append(f"Location: {job.location}")

        if job.employment_type:
            parts.append(f"Type: {job.employment_type}")

        if job.experience_level:
            parts.append(f"Experience: {job.experience_level}")

        return "\n".join(parts)
