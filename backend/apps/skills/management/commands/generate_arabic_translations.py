"""
Management Command: generate_arabic_translations

Generate Arabic translations for skills using AI.

Usage:
    python manage.py generate_arabic_translations --limit 500
    python manage.py generate_arabic_translations --all  # Translate all skills
    python manage.py generate_arabic_translations --dry-run  # Preview only

This command uses Claude Haiku (cheap, fast) to translate skill names to Arabic.
"""

import logging
import time
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.skills.models import Skill
from apps.intelligence.service import get_ai_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Generate Arabic translations for skills using AI."""

    help = "Generate Arabic translations for skills using AI"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="Number of skills to translate (default: 500, top by occupation count)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Translate all skills (ignores --limit)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-translate skills that already have translations",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be translated without actually translating",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Number of skills to translate per LLM call (default: 10)",
        )

    def handle(self, *args, **options):
        limit = options.get("limit", 500)
        translate_all = options.get("all", False)
        force = options.get("force", False)
        dry_run = options.get("dry_run", False)
        batch_size = options.get("batch_size", 10)

        self.stdout.write(self.style.SUCCESS("Starting Arabic translation generation"))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No translations will be saved"))

        # Get AI service
        ai_service = get_ai_service()

        # Build queryset
        queryset = Skill.objects.all()

        # Filter out already translated unless --force
        if not force:
            queryset = queryset.filter(name_ar="")

        # Order by usage (skills used in most occupations)
        queryset = queryset.annotate(
            occupation_count=models.Count('occupations')
        ).order_by('-occupation_count', 'name')

        # Apply limit
        if not translate_all:
            queryset = queryset[:limit]

        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("No skills need translation"))
            return

        self.stdout.write(f"Translating {total_count} skills in batches of {batch_size}")

        translated = 0
        failed = 0

        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = list(queryset[i:i+batch_size])

            if not batch:
                break

            # Build batch translation prompt
            skill_list = "\n".join([f"{idx+1}. {skill.name}" for idx, skill in enumerate(batch)])

            prompt = f"""Translate the following skill names to Modern Standard Arabic.
Return ONLY a JSON array with the translations in the same order.
Each translation should be professional, accurate, and commonly used in career contexts.

Skills to translate:
{skill_list}

Return format: ["translation1", "translation2", ...]
Do not add any explanation, just the JSON array."""

            try:
                # Call AI service
                if not dry_run:
                    response = ai_service.generate_with_haiku(
                        prompt=prompt,
                        system="You are a professional translator specializing in technical and career terminology. Always return valid JSON.",
                    )

                    # Parse response
                    import json
                    translations = json.loads(response)

                    if len(translations) != len(batch):
                        self.stdout.write(
                            self.style.WARNING(
                                f"Batch {i//batch_size + 1}: Expected {len(batch)} translations, got {len(translations)}"
                            )
                        )
                        failed += len(batch)
                        continue

                    # Save translations
                    with transaction.atomic():
                        for skill, translation in zip(batch, translations):
                            skill.name_ar = translation
                            skill.save(update_fields=['name_ar'])

                    translated += len(batch)
                    self.stdout.write(f"  Translated {translated}/{total_count} skills")

                    # Rate limiting - avoid hitting AI service too hard
                    time.sleep(0.5)
                else:
                    # Dry run - just show what would be translated
                    self.stdout.write(f"  Would translate batch {i//batch_size + 1}:")
                    for skill in batch:
                        self.stdout.write(f"    - {skill.name}")
                    translated += len(batch)

            except json.JSONDecodeError as e:
                self.stdout.write(
                    self.style.ERROR(f"Batch {i//batch_size + 1}: Failed to parse AI response: {e}")
                )
                failed += len(batch)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Batch {i//batch_size + 1}: Translation failed: {e}")
                )
                failed += len(batch)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Translation complete: {translated} translated, {failed} failed"
            )
        )


# Import Count for annotation
from django.db import models
