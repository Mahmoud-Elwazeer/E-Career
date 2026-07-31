"""
Celery Tasks for Search Sync

This module contains Celery tasks for syncing jobs to the search index.
"""

import logging
from celery import shared_task
from django.db.models import QuerySet

from apps.jobs.models import Job
from apps.search.services import search_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_job_to_search(self, job_id: str) -> bool:
    """
    Sync a single job to the search index.
    
    Args:
        job_id: UUID of the job to sync
        
    Returns:
        True if successful, False otherwise
    """
    try:
        job = Job.objects.get(id=job_id)
        result = search_service.sync_job(job)
        logger.info(f"Synced job {job_id} to search: {result}")
        return result
    except Job.DoesNotExist:
        logger.warning(f"Job {job_id} not found for sync")
        return False
    except Exception as e:
        logger.error(f"Failed to sync job {job_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def delete_job_from_search(self, job_id: str) -> bool:
    """
    Delete a job from the search index.
    
    Args:
        job_id: UUID of the job to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        result = search_service.delete_job(job_id)
        logger.info(f"Deleted job {job_id} from search: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to delete job {job_id} from search: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1, default_retry_delay=300)
def sync_all_jobs_to_search(self) -> tuple[int, int]:
    """
    Sync all active jobs to the search index.
    
    Returns:
        Tuple of (synced_count, failed_count)
    """
    try:
        queryset = Job.objects.filter(status="active")
        synced, failed = search_service.sync_all_jobs(queryset)
        logger.info(f"Synced {synced} jobs to search, {failed} failed")
        return synced, failed
    except Exception as e:
        logger.error(f"Failed to sync all jobs to search: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_job_with_facets(self, job_id: str) -> bool:
    """
    Sync a job to search and update related facets.
    
    Args:
        job_id: UUID of the job to sync
        
    Returns:
        True if successful, False otherwise
    """
    try:
        job = Job.objects.get(id=job_id)
        result = search_service.sync_job(job)
        
        # Update facets if successful
        if result:
            from apps.search.services import search_service
            facets = search_service.get_facets()
            logger.info(f"Updated facets for job {job_id}: {facets}")
        
        return result
    except Job.DoesNotExist:
        logger.warning(f"Job {job_id} not found for sync with facets")
        return False
    except Exception as e:
        logger.error(f"Failed to sync job {job_id} with facets: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True)
def bulk_sync_jobs_to_search(self, job_ids: list[str]) -> tuple[int, int]:
    """
    Sync multiple jobs to the search index in bulk.
    
    Args:
        job_ids: List of job UUIDs to sync
        
    Returns:
        Tuple of (synced_count, failed_count)
    """
    synced = 0
    failed = 0
    
    for job_id in job_ids:
        try:
            job = Job.objects.get(id=job_id)
            result = search_service.sync_job(job)
            if result:
                synced += 1
            else:
                failed += 1
        except Job.DoesNotExist:
            logger.warning(f"Job {job_id} not found for bulk sync")
            failed += 1
        except Exception as e:
            logger.error(f"Failed to bulk sync job {job_id}: {e}")
            failed += 1
    
    logger.info(f"Bulk synced {synced} jobs, {failed} failed")
    return synced, failed