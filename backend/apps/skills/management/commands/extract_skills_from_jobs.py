"""
Management command: extract_skills_from_jobs

Extract skills from existing job descriptions using AI, populate Skill model.
This is a workaround when ESCO dataset is unavailable.

Usage:
    python manage.py extract_skills_from_jobs --limit 100
"""
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.jobs.models import Job
from apps.skills.models import Skill
from apps.intelligence.career_ai import career_ai_service as bedrock_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Extract skills from job descriptions and populate Skill model"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of jobs to process (default: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be extracted without saving'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']

        self.stdout.write(f"Extracting skills from {limit} jobs...")

        # Get jobs with descriptions
        jobs = Job.objects.filter(
            status='active'
        ).exclude(
            description__isnull=True
        ).exclude(
            description=''
        )[:limit]

        if not jobs:
            self.stdout.write(self.style.WARNING("No jobs found with descriptions"))
            return

        # Collect unique skills
        all_skills = set()

        for i, job in enumerate(jobs, 1):
            self.stdout.write(f"Processing {i}/{len(jobs)}: {job.title}...")

            try:
                # Extract skills using AI
                prompt = f"""Extract technical and professional skills from this job description.
Return ONLY a comma-separated list of skills (no explanations).

Job Title: {job.title}
Description: {job.description[:1000]}

Skills (comma-separated):"""

                response = bedrock_service.invoke_model(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.3
                )

                # Parse skills
                if isinstance(response, str):
                    skills_text = response
                else:
                    skills_text = response.get('text', '')

                # Split and clean
                skills = [
                    s.strip()
                    for s in skills_text.split(',')
                    if s.strip() and len(s.strip()) > 2
                ]

                all_skills.update(skills[:15])  # Max 15 skills per job

                self.stdout.write(f"  Found {len(skills)} skills: {', '.join(skills[:5])}...")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))
                continue

        self.stdout.write(f"\nTotal unique skills extracted: {len(all_skills)}")

        if dry_run:
            self.stdout.write("\n=== DRY RUN - Would create these skills ===")
            for skill in sorted(all_skills)[:50]:
                self.stdout.write(f"  - {skill}")
            return

        # Save skills to database
        created = 0
        with transaction.atomic():
            for skill_name in all_skills:
                skill, is_created = Skill.objects.get_or_create(
                    name=skill_name,
                    defaults={
                        'description': f'Skill extracted from job descriptions',
                        'skill_type': 'technical'
                    }
                )
                if is_created:
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Created {created} new skills, {len(all_skills) - created} already existed")
        )
        self.stdout.write(f"Total skills in database: {Skill.objects.count()}")
