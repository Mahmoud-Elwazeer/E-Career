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
    smartrecruiters, workable, teamtailor, eightfold, icims
)
from .pipeline.url_resolver import is_direct_company_url, verify_url_live
from .pipeline.legitimacy import calculate_legitimacy_score, assess_job
from .pipeline.deduplicator import (
    generate_job_hash, generate_job_slug, dedup_verdict, normalize_title_for_dedup,
)
from .pipeline.normalizer import (
    normalize_employment_type,
    normalize_experience_level,
    normalize_remote_type,
    normalize_location,
    normalize_seniority,
    build_provenance,
)
from .pipeline.contract import NormalizedJob

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
        'eightfold': 5,
        'icims': 3,
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
    
    def scrape_source_fetch_only(self, source: Source) -> List[Dict]:
        """Fetch jobs for a source WITHOUT persisting (connector-matrix dry-run).

        Dispatches to the same connector set as scrape_source but skips the
        _process_jobs funnel, so we can probe a connector's raw fetch output
        without writing to the DB.
        """
        platform = source.ats_platform.lower() if source.ats_platform else ''
        company_slug = source.slug
        if company_slug.endswith(f"-{platform}"):
            company_slug = company_slug[: -len(f"-{platform}")]
        dispatch = {
            'greenhouse': greenhouse.fetch_greenhouse_jobs,
            'lever': lever.fetch_lever_jobs,
            'ashby': ashby.fetch_ashby_jobs,
            'bamboohr': bamboohr.fetch_bamboohr_jobs,
            'workday': workday.fetch_workday_jobs,
            'smartrecruiters': smartrecruiters.fetch_smartrecruiters_jobs,
            'workable': workable.fetch_workable_jobs,
            'teamtailor': teamtailor.fetch_teamtailor_jobs,
            'eightfold': eightfold.fetch_eightfold_jobs,
            'icims': icims.fetch_icims_jobs,
        }
        fn = dispatch.get(platform)
        if not fn:
            return []
        try:
            return fn(company_slug) or []
        except Exception as e:
            logger.warning("fetch_only_failed platform=%s error=%s", platform, str(e))
            return []

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
            elif platform == 'eightfold':
                jobs = eightfold.fetch_eightfold_jobs(company_slug)
            elif platform == 'icims':
                jobs = icims.fetch_icims_jobs(company_slug)
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

        # Structured run metrics so a "fetched N / created 0" run is observable
        # instead of silently swallowed (§2/§9/§21).
        from .pipeline.run_metrics import (
            RunMetrics, MISSING_APPLY_URL, NOT_DIRECT_URL, BLOCKED_AGGREGATOR,
            NORMALIZATION_ERROR, LOW_LEGITIMACY, DUPLICATE, PERSISTENCE_ERROR,
            VERIFICATION_ERROR,
        )
        metrics = RunMetrics(
            source=getattr(source, 'slug', ''),
            provider=(getattr(source, 'ats_platform', '') or ''),
            fetched=len(jobs),
        )

        for job_data in jobs:
            try:
                # 1. Validate apply URL
                apply_url = job_data.get('direct_apply_url') or job_data.get('apply_url')

                if not apply_url:
                    metrics.reject(MISSING_APPLY_URL, job_data.get('title'))
                    continue
                # Had a candidate apply url to evaluate.
                metrics.direct_apply_candidate += 1
                if not is_direct_company_url(apply_url):
                    metrics.reject(NOT_DIRECT_URL, apply_url)
                    continue
                # Passed the direct/moat gate.
                metrics.direct_apply_verified += 1

                # 2. Check ATS fingerprint
                ats_result = ats_stage.run(apply_url)
                if ats_result.platform == "BLOCKED_AGGREGATOR":
                    blocked_count += 1
                    metrics.reject(BLOCKED_AGGREGATOR, apply_url)
                    continue

                # 3. Assess legitimacy — SOURCE TRUST and CONTENT QUALITY are
                #    reported separately (§6). The moat still gates on content
                #    quality (0.4); source trust never buys publication.
                assessment = assess_job(job_data, content_threshold=0.4)
                legitimacy_score = assessment['content_quality']
                legitimacy_flags = assessment['content_flags']

                if not assessment['publishable']:
                    metrics.reject(LOW_LEGITIMACY, {
                        'title': job_data.get('title'),
                        'content_quality': legitimacy_score,
                        'source_trust': assessment['source_trust'],
                        'block_reasons': assessment['block_reasons'],
                        'flags': legitimacy_flags,
                    })
                    continue
                
                # 3b. Map the connector dict into the ONE authoritative
                #     contract (§5) so downstream code never guesses connector
                #     keys. This resolves the REAL employer name instead of the
                #     lowercased board slug (the long-standing company-name bug).
                njob = NormalizedJob.from_connector_dict(job_data, source=source)
                contract_problems = njob.validate()
                if contract_problems:
                    metrics.reject(NORMALIZATION_ERROR, {
                        'title': job_data.get('title'), 'problems': contract_problems,
                    })
                    continue
                metrics.normalized += 1

                # 4. Get or create company — keyed on a stable slug, but stored
                #    with the resolved human employer name (njob.company_name).
                company_slug_key = (
                    (njob.company_slug or njob.company_name or source.name)
                    .lower().replace(' ', '-')
                )
                # Strip a trailing ATS suffix from the KEY so airbnb-greenhouse
                # and a future airbnb-lever collapse to one "airbnb" company.
                for _sfx in ('-greenhouse', '-lever', '-ashby', '-workday',
                             '-smartrecruiters', '-icims', '-workable',
                             '-teamtailor', '-bamboohr', '-oracle', '-sap'):
                    if company_slug_key.endswith(_sfx):
                        company_slug_key = company_slug_key[: -len(_sfx)]
                        break
                company, _created_co = Company.objects.get_or_create(
                    slug=company_slug_key,
                    defaults={'name': njob.company_name or source.name},
                )
                # Backfill a real name if the company was previously created
                # with a slug-like placeholder name.
                if (not _created_co and njob.company_name
                        and company.name.lower().replace(' ', '-') == company.slug):
                    company.name = njob.company_name
                    company.save(update_fields=['name'])
                
                # 5. Generate job hash
                job_hash = generate_job_hash({
                    'company': company.name,
                    'title': job_data.get('title', ''),
                    'location': job_data.get('location', ''),
                })
                
                # 6. Layered deduplication (Section 9).
                #    L1: exact (ats_platform, ats_job_id) — strongest identity.
                #    L2: cross-source normalized (company + normalized title + location)
                #        catches the same role posted via a different source/id.
                verdict = dedup_verdict({
                    'ats_platform': job_data.get('ats_platform', ''),
                    'ats_job_id': job_data.get('ats_job_id', ''),
                    'direct_apply_url': apply_url,
                    'company': company.name,
                    'title': job_data.get('title', ''),
                    'location': job_data.get('location', ''),
                })

                existing = None
                if job_data.get('ats_job_id') and job_data.get('ats_platform'):
                    existing = Job.objects.filter(
                        ats_job_id=job_data.get('ats_job_id', ''),
                        ats_platform=job_data.get('ats_platform', ''),
                    ).first()

                if existing is None:
                    # L2 cross-source check against active jobs at this company.
                    norm_title = normalize_title_for_dedup(job_data.get('title', ''))
                    loc = (job_data.get('location', '') or '').lower().strip()
                    for cand in Job.objects.filter(company=company).only(
                        'id', 'title', 'location', 'is_expired', 'quality_state'
                    )[:200]:
                        if (
                            normalize_title_for_dedup(cand.title) == norm_title
                            and (cand.location or '').lower().strip() == loc
                        ):
                            existing = cand
                            break

                if existing:
                    existing.is_expired = False
                    existing.quality_state = 'probably_active'
                    existing.save(update_fields=['is_expired', 'quality_state'])
                    metrics.updated += 1
                    metrics.duplicates += 1
                    metrics.reject(DUPLICATE, job_data.get('title'))
                    continue
                
                # 7. Create new job
                slug = generate_job_slug(
                    company.name,
                    job_data.get('title', ''),
                    job_data.get('ats_job_id', '')
                )

                seniority, seniority_conf = normalize_seniority(
                    job_data.get('title', ''), job_data.get('experience_level', '')
                )
                normalized_loc = normalize_location(job_data.get('location', ''))
                provenance = build_provenance(
                    {**job_data, 'direct_apply_url': apply_url,
                     'location': normalized_loc,
                     'experience_level': seniority or job_data.get('experience_level')},
                    source=job_data.get('ats_platform') or source.slug,
                    method='ats_api',
                    confidence=1.0,
                )
                if seniority:
                    provenance['experience_level'] = {
                        'value': seniority, 'source': 'title_inference',
                        'method': 'heuristic', 'confidence': round(seniority_conf, 3),
                    }
                # Record the source-trust dimension separately from content
                # quality so the split is auditable on the persisted job (§6).
                provenance['_source_trust'] = {
                    'value': assessment['source_trust'],
                    'evidence': assessment['source_evidence'],
                    'is_structured_ats': assessment['is_structured_ats'],
                }

                # experience_level must be one of Job.EXPERIENCE_LEVEL_CHOICES
                # (entry/mid/senior/lead). normalize_seniority may return
                # director/executive/student — clamp those to the nearest valid.
                _EXP_CLAMP = {
                    'director': 'lead', 'executive': 'lead', 'c_level': 'lead',
                    'student': 'entry', 'junior': 'entry',
                }
                exp_level = seniority or normalize_experience_level(job_data.get('experience_level')) or 'mid'
                exp_level = _EXP_CLAMP.get(exp_level, exp_level)
                if exp_level not in {'entry', 'mid', 'senior', 'lead'}:
                    exp_level = 'mid'

                # location_type + industry are REQUIRED on Job. The orchestrator
                # previously omitted them (causing create to fail). Derive sane,
                # valid defaults from available signals.
                work_arr = normalize_remote_type(job_data.get('remote_type')) or 'onsite'
                loc_type = work_arr if work_arr in {'remote', 'hybrid', 'onsite'} else 'onsite'
                industry = (getattr(company, 'industry', '') or 'technology')

                try:
                    job = Job.objects.create(
                        company=company,
                        source=source,
                        title=job_data.get('title', ''),
                        slug=slug,
                        description=job_data.get('description', ''),
                        location=normalized_loc or 'Not specified',
                        location_type=loc_type,
                        industry=industry,
                        direct_apply_url=apply_url,
                        # source_url is a REQUIRED URLField; it was previously
                        # never set (stored empty). Use the contract's resolved
                        # canonical/source url, falling back to the apply url.
                        source_url=(njob.canonical_job_url or njob.source_url or apply_url),
                        source_type='scraped',
                        employment_type=normalize_employment_type(job_data.get('employment_type')) or 'full_time',
                        experience_level=exp_level,
                        work_arrangement=work_arr,
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
                        field_provenance=provenance,
                    )
                except Exception as ce:
                    # Capture the REAL persistence error instead of hiding it.
                    metrics.reject(PERSISTENCE_ERROR, f"{type(ce).__name__}: {ce}")
                    logger.error("job_persistence_failed", error=str(ce),
                                 error_type=type(ce).__name__, title=job_data.get('title'))
                    continue

                added_count += 1
                metrics.created += 1

                # 8. Run verification. A created+verified job is PUBLISHABLE
                #    (visible to users); a created-but-unverified job still
                #    persists but is not counted publishable.
                job_verified = False
                try:
                    verification_engine.verify_job(job)
                    verified_count += 1
                    metrics.verified += 1
                    job_verified = True
                except Exception as ve:
                    metrics.reject(VERIFICATION_ERROR, str(ve))
                    logger.error(f"Verification failed for job {job.id}: {ve}")

                if job_verified:
                    metrics.publishable += 1

                # 9. Search index sync — measure that persisted jobs actually
                #    reach the search backend (§20). Counted separately so a
                #    Typesense outage shows as indexed<created, not silent loss.
                try:
                    from apps.search.service import SearchService
                    SearchService().sync_job(job)
                    metrics.indexed += 1
                except Exception as se:
                    logger.warning("search_sync_failed job=%s error=%s", job.id, se)

            except Exception as e:
                metrics.errors += 1
                metrics.reject('UNKNOWN', f"{type(e).__name__}: {e}")
                logger.error(f"Failed to process job: {e}")
                continue

        # Emit aggregated run metrics + zero-yield anomaly alert (§21).
        # NOTE: this module uses stdlib logging, which does NOT accept arbitrary
        # kwargs — pass the summary as a single formatted arg. Set the attribute
        # FIRST so metrics are always retrievable even if logging misbehaves.
        summary = metrics.to_dict()
        summary['degraded'] = metrics.is_degraded
        self._last_run_metrics = summary
        try:
            if metrics.is_zero_yield_anomaly:
                logger.warning("scrape_zero_yield_anomaly: %s", summary)
            elif metrics.is_degraded:
                logger.warning("scrape_run_degraded: %s", summary)
            else:
                logger.info("scrape_run_metrics: %s", summary)
        except Exception:
            pass

        return added_count

    def scrape_all_sources(self) -> Dict:
        """
        Scrape all active sources synchronously.

        Returns:
            Dict with total_found and total_added counts.
        """
        total_found = 0
        total_added = 0

        sources = Source.objects.filter(is_active=True)

        for source in sources:
            if not self.should_scrape_source(source):
                continue

            try:
                source.last_run_at = timezone.now()
                source.save(update_fields=['last_run_at'])

                jobs, added = self.scrape_source(source)
                total_found += len(jobs)
                total_added += added
            except Exception as e:
                logger.error(f"Failed to scrape source {source.id}: {e}")
                continue

        return {
            'total_found': total_found,
            'total_added': total_added,
        }


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

                # §9: fold this run's health into the source lifecycle so a
                # rotting source (fetching but never persisting) auto-flags as
                # DEGRADED and accrues zero-yield runs that trigger rediscovery.
                run = getattr(orchestrator, '_last_run_metrics', None) or {}
                if run.get('degraded'):
                    source.consecutive_zero_yield_runs = (
                        (source.consecutive_zero_yield_runs or 0) + 1
                    )
                    # Don't clobber a terminal state (migrated/invalid/disabled).
                    if source.lifecycle_state in ('active', 'degraded'):
                        source.lifecycle_state = 'degraded'
                else:
                    source.consecutive_zero_yield_runs = 0
                    if source.lifecycle_state == 'degraded':
                        source.lifecycle_state = 'active'
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