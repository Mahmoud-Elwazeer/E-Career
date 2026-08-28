"""
Management Command: embed_skills

Generate embeddings for all ESCO skills and index them via pgvector.

Usage:
    python manage.py embed_skills
    python manage.py embed_skills --limit 500  # Top 500 skills
"""

import logging
from django.core.management.base import BaseCommand
from django.db.models import Count

from apps.skills.models import Skill
from apps.vectors.service import get_vector_service, SKILLS_COLLECTION
from apps.vectors.plugins.vector_plugin import VectorDocument

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Bulk embed skills."""

    help = "Generate embeddings for skills and index in vector database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of skills to embed",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Batch size for embedding generation (default: 100)",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")
        batch_size = options.get("batch_size", 100)

        self.stdout.write(self.style.SUCCESS("Starting skill embedding"))

        vector_service = get_vector_service()

        # Ensure collection exists
        if not vector_service.vector_plugin.collection_exists(SKILLS_COLLECTION):
            self.stdout.write("Creating skills collection...")
            vector_service.vector_plugin.create_collection(
                name=SKILLS_COLLECTION,
                vector_size=1024,
                distance="cosine",
            )

        # Get skills ordered by usage (occupation count)
        queryset = Skill.objects.annotate(
            occupation_count=Count('occupations')
        ).order_by('-occupation_count', 'name')

        if limit:
            queryset = queryset[:limit]

        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("No skills to embed"))
            return

        self.stdout.write(f"Embedding {total_count} skills in batches of {batch_size}")

        embedded = 0
        failed = 0

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = list(queryset[i:i+batch_size])

            try:
                # Build embedding texts
                texts = []
                for skill in batch:
                    text = self._skill_to_text(skill)
                    texts.append(text)

                # Generate embeddings
                embeddings = vector_service.generate_embeddings(
                    texts=texts,
                    input_type="search_document",
                )

                # Build documents
                documents = []
                for skill, embedding in zip(batch, embeddings):
                    payload = {
                        "skill_id": str(skill.id),
                        "name": skill.name,
                        "name_ar": skill.name_ar or "",
                        "type": skill.type,
                        "category": skill.category,
                        "esco_uri": skill.esco_uri,
                        "description": skill.description[:500] if skill.description else "",
                    }

                    documents.append(
                        VectorDocument(
                            id=str(skill.id),
                            vector=embedding,
                            payload=payload,
                        )
                    )

                # Upsert to vector DB
                count = vector_service.vector_plugin.upsert(SKILLS_COLLECTION, documents)
                embedded += count

                self.stdout.write(f"  Embedded {embedded}/{total_count} skills")

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
        total_vectors = vector_service.vector_plugin.count(SKILLS_COLLECTION)
        self.stdout.write(f"Total vectors in collection: {total_vectors}")

    def _skill_to_text(self, skill) -> str:
        """Convert skill to embedding text."""
        parts = [
            f"Skill: {skill.name}",
            f"Type: {skill.type}",
        ]

        if skill.description:
            desc = skill.description[:500]
            parts.append(f"Description: {desc}")

        if skill.name_ar:
            parts.append(f"Arabic: {skill.name_ar}")

        return "\n".join(parts)
