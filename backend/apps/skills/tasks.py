"""Celery tasks for the Skills app."""
from celery import shared_task


@shared_task
def compute_esco_embeddings():
    """
    Compute vector embeddings for all ESCO skills that don't have one yet.
    Run weekly to keep embeddings up to date with new skills.
    """
    from .esco_embeddings import get_esco_matcher

    matcher = get_esco_matcher()
    computed = matcher.compute_all_embeddings()
    return {'computed': computed}


@shared_task
def extract_skills_for_recent_jobs(days: int = 1):
    """Extract skills from jobs posted in the last N days."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.jobs.models import Job
    from .extraction import skill_extractor

    cutoff = timezone.now() - timedelta(days=days)
    jobs = Job.objects.filter(
        created_at__gte=cutoff,
        is_expired=False,
    ).exclude(description='')

    processed = 0
    for job in jobs.iterator():
        result = skill_extractor.process_job(job)
        if result['status'] == 'success':
            processed += 1

    return {'processed': processed, 'total': jobs.count()}
