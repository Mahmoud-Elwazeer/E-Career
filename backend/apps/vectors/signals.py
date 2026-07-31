"""
Vector Signals

Real-time embedding synchronization when jobs/skills are created/updated.
"""

import structlog
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.jobs.models import Job
from apps.skills.models import Skill
from apps.vectors.tasks import embed_job_task, remove_job_from_vectors_task, embed_skill_task

logger = structlog.get_logger(__name__)


@receiver(post_save, sender=Job)
def job_saved_handler(sender, instance, created, **kwargs):
    """When a job is created or updated, embed it."""
    # Only embed if verified
    if hasattr(instance, "verification") and instance.verification.status == "verified":
        if instance.verification.trust_score >= 0.4:
            embed_job_task.delay(str(instance.id))
            logger.info("job_embed_queued", job_id=str(instance.id), created=created)


@receiver(post_delete, sender=Job)
def job_deleted_handler(sender, instance, **kwargs):
    """When a job is deleted, remove from vectors."""
    remove_job_from_vectors_task.delay(str(instance.id))
    logger.info("job_remove_queued", job_id=str(instance.id))


@receiver(post_save, sender=Skill)
def skill_saved_handler(sender, instance, created, **kwargs):
    """When a skill is created or updated, embed it."""
    if created:
        embed_skill_task.delay(str(instance.id))
        logger.info("skill_embed_queued", skill_id=str(instance.id))
