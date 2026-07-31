"""
Scraper Orchestrator

Manages scraper execution with:
- Configurable schedule per source (cron field)
- Rate limiting per ATS platform
- Error tracking + PipelineHealth updates
- Auto-disable failing sources after N failures
"""
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from croniter import croniter

from celery import shared_task
from django.utils import timezone

from apps.jobs.models import Job, Source, Company
from apps.core.models import PipelineHealth, PlatformConfig

from .ats import (
    greenhouse, lever, ashby, bamboohr, workday,
    smartrecruiters, workable, teamtailor
)
from .pipeline.url_resolver import is_direct_company_url, verify_url_live
from .pipeline.legitimacy import calculate_legitimacy_score
from .pipeline.deduplicator import generate_job_hash, generate_job_slug
from .pipeline.normalizer import (
    normalize_employment_type,
    normalize_experience_level,
    normalize_remote_type,
    normalize_location,
)

# Import verification engine
from apps.verification.engine import VerificationEngine
from apps.verification.stages import ATSFingerprintStage

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """
    Orchestrates scraper execution with advanced features.
    
    Features:
    - Configurable schedule per source (cron field)
    - Rate limiting per ATS platform
    - Error tracking + PipelineHealth updates
    - Auto-disable failing sources after N failures
    """
    
    # Default rate limits (requests per minute per platform)
    RATE_LIMITS = {
        'greenhouse': 10,
        'lever': 10,
        'ashby': 5,
        'bamboohr': 5,
        'workday': 2,
        'smartrecruiters': 10,
        'workable': 10,
        'teamtailor': 10,
    }
    
    # Maximum consecutive failures before auto-disable
    MAX_FAILURES = 5
    
    def __init__(self):
        self._rate_limit_tracker: Dict[str, List[datetime]] = {}
        self._failure_tracker: Dict[str, int] = {}
    
    def should_scrape_source(self, source: Source) -> bool:
        """
        Check if a source should be scraped based on its schedule.
        
        Args:
            source: Source instance
            
        Returns:
            True if should scrape, False otherwise
        """
        if not source.is_active:
            return False
        
        # Check if source has a custom schedule
        cron_expression = source.schedule_cron or '0 */6 * * *'
        
        try:
            # Get last run time
            last_run = source.last_run_at
            
            if not last_run:
                # Never run before - run now
                return True
            
            # Calculate next run time
            cron = croniter(cron_expression, last_run)
            next_run = cron.get_next(datetime)
            
            # Check if it's time to run
            return timezone.now() >= next_run
            
        except Exception as e:
            logger.error(f"Failed to check schedule for source {source.id}: {e}")
            return False
    
    def check_rate_limit(self, platform: str) -> bool:
        """
        Check if we can make a request for a platform.
        
        Args:
            platform: ATS platform name
            
        Returns:
            True if request allowed, False if rate limited
        """
        limit = self.RATE_LIMITS.get(platform, 10)
        current_time = timezone.now()
        
        # Initialize tracker if needed
        if platform not in self._rate_limit_tracker:
            self._rate_limit_tracker[platform] = []
        
        # Clean old entries (older than 1 minute)
        cutoff = current_time - timedelta(minutes=1)
        self._rate_limit_tracker[platform] = [
            t for t in self._rate_limit_tracker[platform] if t > cutoff
        ]
        
        # Check if under limit
        return len(self._rate_limit_tracker[platform]) < limit
    
    def record_request(self, platform: str) -> None:
        """Record a request for rate limiting."""
        if platform not in self._rate_limit_tracker:
            self._rate_limit_tracker[platform] = []
        self._rate_limit_tracker[platform].append(timezone.now())
    
    def record_failure(self, source_id: str) -> bool:
        """
        Record a failure for a source.
        
        Args:
            source_id: Source ID
            
        Returns:
            True if source should be disabled
        """
        if source_id not in self._failure_tracker:
            self._failure_tracker[source_id] = 0
        
        self._failure_tracker[source_id] += 1
        
        return self._failure_tracker[source_id] >= self.MAX_FAILURES
    
    def record_success(self, source_id: str) -> None:
        """Record a success for a source."""
        if source_id in self._failure_tracker:
            self._failure_tracker[source_id] = 0
    
    def should_disable_source(self, source: Source) -> bool:
        """
        Check if a source should be disabled due to failures.
        
        Args:
            source: Source instance
            
        Returns:
            True if should be disabled
        """
        return self._failure_tracker.get(source.id, 0) >= self.MAX_FAILURES
    
    def scrape_source(self, source: Source) -> Tuple[List[Dict], int]:
        """
        Scrape jobs from a single source.
        
        Args:
            source: Source instance
            
        Returns:
            Tuple of (jobs, added_count)
        """
        platform = source.ats_platform.lower() if source.ats_platform else ''
        
        # Extract company slug
        company_slug = source.slug
        if company_slug.endswith(f"-{platform}"):
            company_slug = company_slug[:-len(f"-{platform}")]
        
        # Check rate limit
        if not self.check_rate_limit(platform):
            logger.warning(f"Rate limit exceeded for platform {platform}")
            return [], 0
        
        # Fetch jobs based on platform
        jobs = []
        try:
            if platform == 'greenhouse':
                jobs = greenhouse.fetch_greenhouse_jobs(company_slug)
            elif platform == 'lever':
                jobs = lever.fetch_lever_jobs(company_slug)
            elif platform == 'ashby':
                jobs = ashby.fetch_ashby_jobs(company_slug)
            elif platform == 'bamboohr':
                jobs = bamboohr.fetch_bamboohr_jobs(company_slug)
            elif platform == 'workday':
                jobs = workday.fetch_workday_jobs(company_slug)
            elif platform == 'smartrecruiters':
                jobs = smartrecruiters.fetch_smartrecruiters_jobs(company_slug)
            elif platform == 'workable':
                jobs = workable.fetch_workable_jobs(company_slug)
            elif platform == 'teamtailor':
                jobs = teamtailor.fetch_teamtailor_jobs(company_slug)
            else:
                logger.warning(f"Unknown platform: {platform}")
                return [], 0
            
            # Record successful request
            self.record_request(platform)
            
        except Exception as e:
            logger.error(f"Failed to scrape source {source.id}: {e}")
            should_disable = self.record_failure(source.id)
            
            if should_disable:
                source.is_active = False
                source.save(update_fields=['is_active'])
                logger.info(f"Source {source.id} disabled due to failures")
            
            return [], 0
        
        # Process jobs
        added = self._process_jobs(jobs, source)
        
        if added > 0:
            self.record_success(source.id)
        
        return jobs, added
    
    def _process_jobs(self, jobs: List[Dict], source: Source) -> int:
        """
        Process scraped jobs and store valid ones.
        
        Args:
            jobs: List of job dictionaries
            source: Source instance
            
        Returns:
            Count of jobs added
        """
        added_count = 0
        blocked_count = 0
        verified_count = 0
        
        # Initialize verification engine
        verification_engine = VerificationEngine()
        ats_stage = ATSFingerprintStage()
        
        for job_data in jobs:
            try:
                # 1. Validate apply URL
                apply_url = job_data.get('direct_apply_url') or job_data.get('apply_url')
                
                if not apply_url or not is_direct_company_url(apply_url):
                    continue
                
                # 2. Check ATS fingerprint
                ats_result = ats_stage.run(apply_url)
                if ats_result.platform == "BLOCKED_AGGREGATOR":
                    blocked_count += 1
                    continue
                
                # 3. Calculate legitimacy score
                legitimacy_score, legitimacy_flags = calculate_legitimacy_score(job_data)
                
                if legitimacy_score < 0.4:
                    continue
                
                # 4. Get or create company
                company_name = job_data.get('company_slug', source.name)
                company, _ = Company.objects.get_or_create(
                    slug=company_name.lower().replace(' ', '-'),
                    defaults={'name': company_name}
                )
                
                # 5. Generate job hash
                job_hash = generate_job_hash({
                    'company': company.name,
                    'title': job_data.get('title', ''),
                    'location': job_data.get('location', ''),
                })
                
                # 6. Check if job already exists
                existing = Job.objects.filter(
                    ats_job_id=job_data.get('ats_job_id', ''),
                    ats_platform=job_data.get('ats_platform', ''),
                ).first()
                
                if existing:
                    existing.is_expired = False
                    existing.save(update_fields=['is_expired'])
                    continue
                
                # 7. Create new job
                slug = generate_job_slug(
                    company.name,
                    job_data.get('title', ''),
                    job_data.get('ats_job_id', '')
                )
                
                job = Job.objects.create(
                    company=company,
                    source=source,
                    title=job_data.get('title', ''),
                    slug=slug,
                    description=job_data.get('description', ''),
                    location=normalize_location(job_data.get('location', '')),
                    direct_apply_url=apply_url,
                    source_type='scraped',
                    employment_type=normalize_employment_type(job_data.get('employment_type')) or 'full_time',
                    experience_level=normalize_experience_level(job_data.get('experience_level')) or 'mid',
                    remote_type=normalize_remote_type(job_data.get('remote_type')),
                    salary_min=job_data.get('salary_min'),
                    salary_max=job_data.get('salary_max'),
                    salary_currency=job_data.get('salary_currency', 'USD'),
                    posted_at=timezone.now().date(),
                    scraped_at=timezone.now(),
                    expires_at=timezone.now() + timedelta(days=90),
                    legitimacy_score=legitimacy_score,
                    legitimacy_flags=legitimacy_flags,
                    ats_platform=job_data.get('ats_platform', ''),
                    ats_job_id=job_data.get('ats_job_id', ''),
                    raw_data=job_data.get('raw_data', {}),
                )
                
                # 8. Run verification
                try:
                    verification_engine.verify_job(job)
                    verified_count += 1
                except Exception as ve:
                    logger.error(f"Verification failed for job {job.id}: {ve}")
                
                added_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process job: {e}")
                continue
        
        return added_count


# Global orchestrator instance
orchestrator = ScraperOrchestrator()


@shared_task(bind=True, max_retries=3)
def scrape_all_sources_orchestrated(self):
    """
    Master scraping task with orchestrator features.
    """
    start_time = timezone.now()
    total_found = 0
    total_added = 0
    
    try:
        # Get all active sources
        sources = Source.objects.filter(is_active=True)
        
        for source in sources:
            try:
                # Check if should scrape based on schedule
                if not orchestrator.should_scrape_source(source):
                    continue
                
                # Update source status
                source.last_run_at = timezone.now()
                source.last_run_status = 'running'
                source.save(update_fields=['last_run_at', 'last_run_status'])
                
                # Scrape with orchestrator
                jobs, added = orchestrator.scrape_source(source)
                
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
                # Log error and continue
                source.last_run_status = 'failed'
                source.error_count += 1
                source.last_error = str(e)
                source.save()
                continue
        
        # Update pipeline health
        duration = (timezone.now() - start_time).total_seconds()
        pipeline_health, created = PipelineHealth.objects.get_or_create(
            task_name='scrape_all_sources_orchestrated',
            defaults={
                'last_run_at': start_time,
                'last_status': 'success',
                'last_duration': duration,
                'run_count': 1,
            }
        )
        if not created:
            pipeline_health.last_run_at = start_time
            pipeline_health.last_status = 'success'
            pipeline_health.last_duration = duration
            pipeline_health.run_count += 1
            pipeline_health.save()
        
        return {
            'status': 'success',
            'total_found': total_found,
            'total_added': total_added,
            'duration': duration,
        }
        
    except Exception as exc:
        PipelineHealth.objects.update_or_create(
            task_name='scrape_all_sources_orchestrated',
            defaults={
                'last_run_at': start_time,
                'last_status': 'failed',
                'last_error': str(exc),
            }
        )
        raise self.retry(exc=exc, countdown=60 * 10)


def scrape_single_source_orchestrated(source_id: str) -> Dict:
    """
    Scrape a single source using orchestrator.
    
    Args:
        source_id: Source ID
        
    Returns:
        Dict with scrape results
    """
    try:
        source = Source.objects.get(id=source_id)
    except Source.DoesNotExist:
        return {'error': f'Source {source_id} not found'}
    
    jobs, added = orchestrator.scrape_source(source)
    
    return {
        'source': source.name,
        'found': len(jobs),
        'added': added,
    }