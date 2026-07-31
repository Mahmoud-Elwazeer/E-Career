"""
Management Command: setup_vector_collections

Set up Qdrant collections for jobs, users, and skills.

Usage:
    python manage.py setup_vector_collections
    python manage.py setup_vector_collections --rebuild  # Drop and recreate
"""

import logging
from django.core.management.base import BaseCommand, CommandError

from apps.vectors.service import get_vector_service, JOBS_COLLECTION, USERS_COLLECTION, SKILLS_COLLECTION, EMBED_DIMENSIONS

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Set up vector collections."""

    help = "Set up Qdrant collections for vectors"

    def add_arguments(self, parser):
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Drop and rebuild collections (WARNING: destructive)",
        )

    def handle(self, *args, **options):
        rebuild = options.get("rebuild", False)

        self.stdout.write(self.style.SUCCESS("Setting up vector collections"))

        vector_service = get_vector_service()

        collections = [
            (JOBS_COLLECTION, EMBED_DIMENSIONS, "Job listings with embeddings"),
            (USERS_COLLECTION, EMBED_DIMENSIONS, "User profiles with embeddings"),
            (SKILLS_COLLECTION, EMBED_DIMENSIONS, "ESCO skills with embeddings"),
        ]

        for collection, dimensions, description in collections:
            self.stdout.write(f"\n{description}: {collection}")

            if rebuild:
                if vector_service.vector_plugin.collection_exists(collection):
                    self.stdout.write(self.style.WARNING(f"  Deleting existing collection..."))
                    vector_service.vector_plugin.delete_collection(collection)

            exists = vector_service.vector_plugin.collection_exists(collection)

            if exists:
                count = vector_service.vector_plugin.count(collection)
                self.stdout.write(self.style.SUCCESS(f"  ✓ Collection exists ({count} vectors)"))
            else:
                self.stdout.write(f"  Creating collection...")
                success = vector_service.vector_plugin.create_collection(
                    name=collection,
                    vector_size=dimensions,
                    distance="cosine",
                )

                if success:
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Collection created"))
                else:
                    raise CommandError(f"Failed to create collection: {collection}")

        # Health check
        health = vector_service.health_check()
        self.stdout.write(f"\nHealth check:")
        self.stdout.write(f"  Vector DB: {health['vector']}")
        self.stdout.write(f"  Embedding: {health['embedding']}")

        self.stdout.write(self.style.SUCCESS("\n✓ Vector collections ready"))
