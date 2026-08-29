"""
Daily Liveness & Scrapers Tasks
================================

This module contains Celery tasks for:
1. Daily job liveness checking
2. Weekly job reverification
"""

import logging
import time
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

from django.db.models import Q

from apps.core.safe_fetch import verify_url_is_live, SSRFBlockedError
from apps.jobs.models import Job

logger = logging.getLogger(__name__)


@shared_task
def daily_liveness_check():
    """
    Daily job liveness check task.

    - Gets all active jobs older than 7 days
    - For each job, sends HEAD request to direct_apply_url (or source_url fallback) via safe_fetch
    - If 404 or connection error: mark job as "expired"
    - If 200: update last_verified_at timestamp
    - Process in batches of 50 with 0.1s delay between requests
    """
    cutoff_date = timezone.now() - timedelta(days=7)

    jobs_to_check = Job.objects.filter(
        status='active',
        posted_at__lt=cutoff_date,
    ).filter(
        Q(direct_apply_url__isnull=False) & ~Q(direct_apply_url='') |
        Q(source_url__isnull=False) & ~Q(source_url='')
    )[:50]

    total_checked = 0
    expired_count = 0
    still_active_count = 0
    error_count = 0

    for job in jobs_to_check:
        try:
            check_url = job.direct_apply_url or job.source_url
            is_live, status_code = verify_url_is_live(
                check_url, timeout=10, allow_http=True
            )

            total_checked += 1

            if status_code == 404:
                job.status = 'expired'
                job.expired_reason = '404_not_found'
                job.last_verified_at = timezone.now()
                job.save(update_fields=['status', 'expired_reason', 'last_verified_at'])
                expired_count += 1
                logger.info(f"Job {job.id} ({job.title}) marked as expired (404)")

            elif is_live:
                job.last_verified_at = timezone.now()
                job.save(update_fields=['last_verified_at'])
                still_active_count += 1

            else:
                job.last_verified_at = timezone.now()
                job.save(update_fields=['last_verified_at'])
                still_active_count += 1

        except SSRFBlockedError:
            job.status = 'expired'
            job.expired_reason = 'ssrf_blocked'
            job.last_verified_at = timezone.now()
            job.save(update_fields=['status', 'expired_reason', 'last_verified_at'])
            expired_count += 1
            logger.warning(f"Job {job.id} ({job.title}) SSRF-blocked URL")

        except Exception as e:
            error_count += 1
            logger.error(f"Job {job.id} ({job.title}) - error: {str(e)}")

        time.sleep(0.1)

    logger.info(
        f"Daily liveness check completed: "
        f"Total checked: {total_checked}, "
        f"Expired: {expired_count}, "
        f"Still active: {still_active_count}, "
        f"Errors: {error_count}"
    )

    return {
        'total_checked': total_checked,
        'expired': expired_count,
        'still_active': still_active_count,
        'errors': error_count,
    }


@shared_task
def weekly_reverification():
    """
    Weekly job reverification task.

    - Re-verifies all "active" jobs
    - Sends notification if many jobs from one source are dead
    """
    active_jobs = Job.objects.filter(status='active')[:100]

    total_checked = 0
    expired_count = 0
    still_active_count = 0
    source_dead_counts = {}

    for job in active_jobs:
        try:
            check_url = job.direct_apply_url or job.source_url
            if not check_url:
                continue
            is_live, status_code = verify_url_is_live(
                check_url, timeout=10, allow_http=True
            )

            total_checked += 1

            if status_code == 404:
                job.status = 'expired'
                job.expired_reason = 'weekly_check_404'
                job.last_verified_at = timezone.now()
                job.save(update_fields=['status', 'expired_reason', 'last_verified_at'])
                expired_count += 1

                source_name = job.source.name if job.source else 'unknown'
                source_dead_counts[source_name] = source_dead_counts.get(source_name, 0) + 1

            elif is_live:
                job.last_verified_at = timezone.now()
                job.save(update_fields=['last_verified_at'])
                still_active_count += 1

            else:
                job.last_verified_at = timezone.now()
                job.save(update_fields=['last_verified_at'])
                still_active_count += 1

        except SSRFBlockedError:
            logger.warning(f"Job {job.id} ({job.title}) SSRF-blocked URL")

        except Exception as e:
            logger.error(f"Job {job.id} ({job.title}) - error: {str(e)}")

        time.sleep(0.1)

    for source_name, dead_count in source_dead_counts.items():
        if dead_count >= 10:
            logger.warning(
                f"High number of dead jobs from source '{source_name}': {dead_count} jobs"
            )

    logger.info(
        f"Weekly reverification completed: "
        f"Total checked: {total_checked}, "
        f"Expired: {expired_count}, "
        f"Still active: {still_active_count}"
    )

    return {
        'total_checked': total_checked,
        'expired': expired_count,
        'still_active': still_active_count,
    }


@shared_task
def verify_job_url(job_id: int):
    """
    Verify a single job's URL.

    Args:
        job_id: The ID of the job to verify
    """
    try:
        job = Job.objects.get(id=job_id)
        check_url = job.direct_apply_url or job.source_url

        is_live, status_code = verify_url_is_live(
            check_url, timeout=10, allow_http=True
        )

        if status_code == 404:
            job.status = 'expired'
            job.expired_reason = 'manual_check_404'
            job.last_verified_at = timezone.now()
            job.save(update_fields=['status', 'expired_reason', 'last_verified_at'])
            return {'status': 'expired', 'reason': '404_not_found'}
        else:
            job.last_verified_at = timezone.now()
            job.save(update_fields=['last_verified_at'])
            return {'status': 'active', 'reason': 'ok'}

    except Job.DoesNotExist:
        return {'error': 'Job not found'}
    except SSRFBlockedError:
        return {'error': 'URL blocked by SSRF protection'}
    except Exception as e:
        return {'error': str(e)}
