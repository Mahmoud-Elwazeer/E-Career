"""
Celery tasks for job scraping pipeline.
"""
from celery import shared_task
from django.utils import timezone
from django.db import models
from datetime import timedelta
from typing import List, Dict

from apps.jobs.models import Job, Source, Company
from apps.core.models import PipelineHealth, PlatformConfig

from .ats import greenhouse, lever, ashby, bamboohr
from .pipeline.url_resolver import is_direct_company_url, verify_url_live
from .pipeline.legitimacy import calculate_legitimacy_score
from .pipeline.deduplicator import generate_job_hash, generate_job_slug
from .pipeline.normalizer import (
    normalize_employment_type,
    normalize_experience_level,
    normalize_remote_type,
    normalize_location,
    calculate_expiry_date,
)


@shared_task(bind=True, max_retries=3)
def scrape_all_sources(self):
    """
    Master scraping task - runs all active sources.
    Called by Celery Beat every 6 hours.
    """
    start_time = timezone.now()
    total_found = 0
    total_added = 0
    
    try:
        # Get all active sources
        sources = Source.objects.filter(is_active=True)
        
        for source in sources:
            try:
                # Update source status
                source.last_run_at = timezone.now()
                source.last_run_status = 'running'
                source.save(update_fields=['last_run_at', 'last_run_status'])
                
                # Scrape based on ATS platform
                jobs = scrape_source(source)
                
                # Process and store jobs
                added = process_and_store_jobs(jobs, source)
                
                # Update source stats
                source.jobs_found_last_run = len(jobs)
                source.jobs_added_last_run = added
                source.last_run_status = 'success'
                source.error_count = 0
                source.last_error = ''
                source.save()
                
                total_found += len(jobs)
                total_added += added
                
            except Exception as e:
                # Log error and continue with next source
                source.last_run_status = 'failed'
                source.error_count += 1
                source.last_error = str(e)
                source.save()
                continue
        
        # Update pipeline health
        duration = (timezone.now() - start_time).total_seconds()
        PipelineHealth.objects.update_or_create(
            task_name='scrape_all_sources',
            defaults={
                'last_run_at': start_time,
                'last_status': 'success',
                'last_duration': duration,
                'run_count': models.F('run_count') + 1,
            }
        )
        
        return {
            'status': 'success',
            'total_found': total_found,
            'total_added': total_added,
            'duration': duration,
        }
        
    except Exception as exc:
        # Update pipeline health with failure
        PipelineHealth.objects.update_or_create(
            task_name='scrape_all_sources',
            defaults={
                'last_run_at': start_time,
                'last_status': 'failed',
                'last_error': str(exc),
            }
        )
        raise self.retry(exc=exc, countdown=60 * 10)  # Retry in 10 minutes


def scrape_source(source: Source) -> List[Dict]:
    """
    Scrape jobs from a single source based on ATS platform.
    """
    platform = source.ats_platform.lower() if source.ats_platform else ''
    company_slug = source.slug
    
    if platform == 'greenhouse':
        return greenhouse.fetch_greenhouse_jobs(company_slug)
    elif platform == 'lever':
        return lever.fetch_lever_jobs(company_slug)
    elif platform == 'ashby':
        return ashby.fetch_ashby_jobs(company_slug)
    elif platform == 'bamboohr':
        return bamboohr.fetch_bamboohr_jobs(company_slug)
    else:
        return []


def process_and_store_jobs(jobs: List[Dict], source: Source) -> int:
    """
    Process scraped jobs and store valid ones to database.
    Returns count of jobs added.
    """
    added_count = 0
    
    for job_data in jobs:
        try:
            # 1. Validate apply URL
            apply_url = job_data.get('direct_apply_url') or job_data.get('apply_url')
            
            if not apply_url or not is_direct_company_url(apply_url):
                # Skip jobs without direct apply URLs
                continue
            
            # 2. Calculate legitimacy score
            legitimacy_score, legitimacy_flags = calculate_legitimacy_score(job_data)
            
            # Skip obviously scam jobs
            if legitimacy_score < 0.4:
                continue
            
            # 3. Get or create company
            company_name = job_data.get('company_slug', source.name)
            company, _ = Company.objects.get_or_create(
                slug=company_name.lower().replace(' ', '-'),
                defaults={'name': company_name}
            )
            
            # 4. Generate job hash for deduplication
            job_hash = generate_job_hash({
                'company': company.name,
                'title': job_data.get('title', ''),
                'location': job_data.get('location', ''),
            })
            
            # 5. Check if job already exists
            existing = Job.objects.filter(
                ats_job_id=job_data.get('ats_job_id', ''),
                ats_platform=job_data.get('ats_platform', ''),
            ).first()
            
            if existing:
                # Update existing job
                existing.is_expired = False
                existing.save(update_fields=['is_expired'])
                continue
            
            # 6. Create new job
            slug = generate_job_slug(
                company.name,
                job_data.get('title', ''),
                job_data.get('ats_job_id', '')
            )
            
            Job.objects.create(
                company=company,
                source=source,
                title=job_data.get('title', ''),
                slug=slug,
                description=job_data.get('description', ''),
                location=normalize_location(job_data.get('location', '')),
                direct_apply_url=apply_url,
                source_type='scraped',
                employment_type=normalize_employment_type(job_data.get('employment_type')),
                experience_level=normalize_experience_level(job_data.get('experience_level')),
                remote_type=normalize_remote_type(job_data.get('remote_type')),
                salary_min=job_data.get('salary_min'),
                salary_max=job_data.get('salary_max'),
                salary_currency=job_data.get('salary_currency', 'USD'),
                scraped_at=timezone.now(),
                expires_at=calculate_expiry_date(None),
                legitimacy_score=legitimacy_score,
                legitimacy_flags=legitimacy_flags,
                ats_platform=job_data.get('ats_platform', ''),
                ats_job_id=job_data.get('ats_job_id', ''),
                raw_data=job_data.get('raw_data', {}),
            )
            
            added_count += 1
            
        except Exception as e:
            # Log error and continue
            print(f"Failed to process job: {e}")
            continue
    
    return added_count


@shared_task
def verify_apply_urls():
    """
    Daily task - checks every active job's apply URL.
    Marks jobs as expired if URL is dead.
    """
    start_time = timezone.now()
    checked = 0
    expired = 0
    
    try:
        # Get all active jobs
        jobs = Job.objects.filter(is_expired=False)
        
        for job in jobs.iterator():
            is_live, status_code = verify_url_live(job.direct_apply_url)
            
            job.apply_url_verified = is_live
            job.apply_url_status_code = status_code
            job.apply_url_checked_at = timezone.now()
            
            if not is_live:
                job.is_expired = True
                expired += 1
            
            job.save(update_fields=[
                'apply_url_verified',
                'apply_url_status_code',
                'apply_url_checked_at',
                'is_expired'
            ])
            
            checked += 1
        
        # Update pipeline health
        duration = (timezone.now() - start_time).total_seconds()
        PipelineHealth.objects.update_or_create(
            task_name='verify_apply_urls',
            defaults={
                'last_run_at': start_time,
                'last_status': 'success',
                'last_duration': duration,
                'run_count': models.F('run_count') + 1,
            }
        )
        
        return {
            'checked': checked,
            'expired': expired,
        }
        
    except Exception as e:
        PipelineHealth.objects.update_or_create(
            task_name='verify_apply_urls',
            defaults={
                'last_run_at': start_time,
                'last_status': 'failed',
                'last_error': str(e),
            }
        )
        raise


@shared_task
def expire_old_jobs():
    """
    Daily task - marks jobs older than max_job_age_days as expired.
    """
    try:
        config = PlatformConfig.objects.get(pk=1)
        cutoff_date = timezone.now() - timedelta(days=config.max_job_age_days)
    except PlatformConfig.DoesNotExist:
        cutoff_date = timezone.now() - timedelta(days=90)
    
    expired_count = Job.objects.filter(
        created_at__lt=cutoff_date,
        is_expired=False
    ).update(is_expired=True)
    
    return {'expired': expired_count}


@shared_task
def scrape_single_source(source_id: str):
    """
    Scrape a single source by ID.
    Useful for manual testing or on-demand scraping.
    """
    try:
        source = Source.objects.get(id=source_id)
    except Source.DoesNotExist:
        return {'error': f'Source {source_id} not found'}
    
    jobs = scrape_source(source)
    added = process_and_store_jobs(jobs, source)
    
    return {
        'source': source.name,
        'found': len(jobs),
        'added': added,
    }