"""
Signals for Search Sync

This module contains Django signals for automatically syncing jobs to the search index.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.jobs.models import Job
from apps.search.services import search_service

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Job)
def job_saved(sender, instance, created, **kwargs):
    """
    Signal handler for job save.
    
    Syncs the job to the search index when a job is created or updated.
    """
    if instance.status == "active":
        try:
            search_service.sync_job(instance)
            logger.info(f"Synced job {instance.id} to search (created={created})")
        except Exception as e:
            logger.error(f"Failed to sync job {instance.id} to search: {e}")


@receiver(post_delete, sender=Job)
def job_deleted(sender, instance, **kwargs):
    """
    Signal handler for job delete.
    
    Deletes the job from the search index when a job is deleted.
    """
    try:
        search_service.delete_job(str(instance.id))
        logger.info(f"Deleted job {instance.id} from search")
    except Exception as e:
        logger.error(f"Failed to delete job {instance.id} from search: {e}")