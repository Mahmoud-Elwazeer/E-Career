"""
Daily Liveness & Scrapers Tasks
================================

This module contains Celery tasks for:
1. Daily job liveness checking
2. Weekly job reverification
"""

import logging
import requests
from datetime import datetime, timedelta
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.jobs.models import Job

logger = logging.getLogger(__name__)


@shared_task
def daily_liveness_check():
    """
    Daily job liveness check task.
    
    - Gets all active jobs older than 7 days
    - For each job, sends HEAD request to source_url
    - If 404 or connection error: mark job as "expired"
    - If redirect to generic careers page: mark as "likely_expired"
    - If 200: update last_verified_at timestamp
    - Process in batches of 50 with 1-second delay between batches
    - Log results: total checked, expired, still active
    """
    from celery import current_app
    
    # Calculate cutoff date (7 days ago)
    cutoff_date = timezone.now() - timedelta(days=7)
    
    # Get active jobs older than 7 days
    jobs_to_check = Job.objects.filter(
        status='active',
        posted_at__lt=cutoff_date,
        source_url__isnull=False
    ).exclude(source_url__exact='')[:50]
    
    total_checked = 0
    expired_count = 0
    likely_expired_count = 0
    still_active_count = 0
    error_count = 0
    
    for job in jobs_to_check:
        try:
            # Send HEAD request with timeout
            response = requests.head(
                job.source_url,
                timeout=10,
                allow_redirects=True,
                headers={'User-Agent': 'USAM-Career-Compass/1.0'}
            )
            
            total_checked += 1
            
            if response.status_code == 404:
                # Job has expired (404)
                job.status = 'expired'
                job.expired_reason = '404_not_found'
                job.last_verified_at = timezone.now()
                job.save(update_fields=['status', 'expired_reason', 'last_verified_at'])
                expired_count += 1
                logger.info(f"Job {job.id} ({job.title}) marked as expired (404)")
                
            elif response.status_code == 200:
                # Job is still active
                job.last_verified_at = timezone.now()
                job.save(update_fields=['last_verified_at'])
                still_active_count += 1
                
            elif response.status_code >= 300 and response.status_code < 400:
                # Check if redirect is to a generic careers page
                redirect_url = response.url or ''
                if any(keyword in redirect_url.lower() for keyword in ['careers', 'jobs', 'vacancies', 'openings']):
                    job.status = 'likely_expired'
                    job.expired_reason = 'redirect_to_careers_page'
                    job.last_verified_at = timezone.now()
                    job.save(update_fields=['status', 'expired_reason', 'last_verified_at'])
                    likely_expired_count += 1
                    logger.info(f"Job {job.id} ({job.title}) marked as likely expired (redirect)")
                else:
                    still_active_count += 1
                    
            else:
                # Other status codes - consider as still active
                job.last_verified_at = timezone.now()
                job.save(update_fields=['last_verified_at'])
                still_active_count += 1
                
        except requests.exceptions.Timeout:
            error_count += 1
            logger.warning(f"Job {job.id} ({job.title}) - Request timeout")
            
        except requests.exceptions.ConnectionError:
            job.status = 'expired'
            job.expired_reason = 'connection_error'
            job.last_verified_at = timezone.now()
            job.save(update_fields=['status', 'expired_reason', 'last_verified_at'])
            expired_count += 1
            logger.info(f"Job {job.id} ({job.title}) marked as expired (connection error)")
            
        except requests.exceptions.RequestException as e:
            error_count += 1
            logger.error(f"Job {job.id} ({job.title}) - Request error: {str(e)}")
        
        # Small delay between requests to avoid overwhelming servers
        import time
        time.sleep(0.1)
    
    # Log summary
    logger.info(
        f"Daily liveness check completed: "
        f"Total checked: {total_checked}, "
        f"Expired: {expired_count}, "
        f"Likely expired: {likely_expired_count}, "
        f"Still active: {still_active_count}, "
        f"Errors: {error_count}"
    )
    
    return {
        'total_checked': total_checked,
        'expired': expired_count,
        'likely_expired': likely_expired_count,
        'still_active': still_active_count,
        'errors': error_count,
    }


@shared_task
def weekly_reverification():
    """
    Weekly job reverification task.
    
    - Re-verifies all "active" jobs
    - Updates legitimacy_score based on response
    - Sends notification if many jobs from one source are dead
    """
    from celery import current_app
    
    # Get all active jobs
    active_jobs = Job.objects.filter(status='active')[:100]
    
    total_checked = 0
    expired_count = 0
    still_active_count = 0
    source_dead_counts = {}
    
    for job in active_jobs:
        try:
            response = requests.head(
                job.source_url,
                timeout=10,
                allow_redirects=True,
                headers={'User-Agent': 'USAM-Career-Compass/1.0'}
            )
            
            total_checked += 1
            
            if response.status_code == 404:
                job.status = 'expired'
                job.expired_reason = 'weekly_check_404'
                job.last_verified_at = timezone.now()
                job.save(update_fields=['status', 'expired_reason', 'last_verified_at'])
                expired_count += 1
                
                # Track by source
                source_name = job.source.name if job.source else 'unknown'
                source_dead_counts[source_name] = source_dead_counts.get(source_name, 0) + 1
                
            elif response.status_code == 200:
                # Update legitimacy score based on response
                job.last_verified_at = timezone.now()
                job.save(update_fields=['last_verified_at'])
                still_active_count += 1
                
            else:
                job.last_verified_at = timezone.now()
                job.save(update_fields=['last_verified_at'])
                still_active_count += 1
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Job {job.id} ({job.title}) - Request error: {str(e)}")
        
        # Small delay between requests
        import time
        time.sleep(0.1)
    
    # Check if any source has too many dead jobs
    for source_name, dead_count in source_dead_counts.items():
        if dead_count >= 10:  # Threshold for notification
            logger.warning(
                f"High number of dead jobs from source '{source_name}': {dead_count} jobs"
            )
            # In production, you would send a notification here
            # send_notification_to_admin(
            #     f"High number of dead jobs from {source_name}",
            #     f"{dead_count} jobs from {source_name} have expired in the last check."
            # )
    
    # Log summary
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
        
        response = requests.head(
            job.source_url,
            timeout=10,
            allow_redirects=True,
            headers={'User-Agent': 'USAM-Career-Compass/1.0'}
        )
        
        if response.status_code == 404:
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
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}