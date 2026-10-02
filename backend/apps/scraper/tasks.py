"""
Celery tasks for job scraping pipeline.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from typing import List, Dict

from apps.jobs.models import Job, Source, Company
from apps.jobs.company_resolution import company_resolver
from apps.core.models import PipelineHealth, PlatformConfig

from .ats import (
    greenhouse, lever, ashby, bamboohr, smartrecruiters, workable, teamtailor,
    workday, icims, oracle, sap, eightfold, recruitee, personio, jobvite,
)
from .orchestrator import orchestrator, scrape_all_sources_orchestrated
from .strategy_router import StrategyRouter
from .pipeline.url_resolver import is_direct_company_url, verify_url_live
from .pipeline.legitimacy import calculate_legitimacy_score
from .pipeline.deduplicator import generate_job_hash, generate_job_slug
from .pipeline.normalizer import (
    normalize_employment_type,
    normalize_experience_level,
    normalize_remote_type,
    normalize_location,
    build_provenance,
)

# Import verification engine
from apps.verification.engine import VerificationEngine
from apps.verification.stages import ATSFingerprintStage


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
        pipeline_health, created = PipelineHealth.objects.get_or_create(
            task_name='scrape_all_sources',
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


def _dispatch_structured_ats(platform: str, company_slug: str) -> List[Dict]:
    """TIER 0 (STRUCTURED) connector dispatch.

    This is the ORIGINAL scrape_source if/elif body, unchanged, now extracted
    into its own function so StrategyRouter can call it as `structured_runner`
    without any duplicated logic. Keep this in sync with
    ScraperOrchestrator.scrape_source in orchestrator.py (same dispatch set).
    """
    if platform == 'greenhouse':
        return greenhouse.fetch_greenhouse_jobs(company_slug)
    elif platform == 'lever':
        return lever.fetch_lever_jobs(company_slug)
    elif platform == 'ashby':
        return ashby.fetch_ashby_jobs(company_slug)
    elif platform == 'bamboohr':
        return bamboohr.fetch_bamboohr_jobs(company_slug)
    elif platform == 'smartrecruiters':
        return smartrecruiters.fetch_smartrecruiters_jobs(company_slug)
    elif platform == 'workable':
        return workable.fetch_workable_jobs(company_slug)
    elif platform == 'teamtailor':
        return teamtailor.fetch_teamtailor_jobs(company_slug)
    elif platform == 'workday':
        return workday.fetch_workday_jobs(company_slug)
    elif platform == 'icims':
        return icims.fetch_icims_jobs(company_slug)
    elif platform == 'eightfold':
        return eightfold.fetch_eightfold_jobs(company_slug)
    elif platform == 'recruitee':
        return recruitee.fetch_recruitee_jobs(company_slug)
    elif platform == 'personio':
        return personio.fetch_personio_jobs(company_slug)
    elif platform == 'oracle':
        return oracle.fetch_oracle_jobs(company_slug)
    elif platform == 'sap':
        return sap.fetch_sap_jobs(company_slug)
    elif platform == 'jobvite':
        return jobvite.fetch_jobvite_jobs(company_slug)
    else:
        # A configured Source routed here with an unknown platform string.
        # StrategyRouter only calls this for Tier.STRUCTURED decisions, i.e.
        # platform IS in STRATEGY_ROUTER's STRUCTURED_ATS set, so reaching
        # this branch means STRUCTURED_ATS and this dispatch have drifted out
        # of sync - log loudly so that drift is visible instead of silent.
        import structlog
        structlog.get_logger().warning(
            "scrape_source_structured_dispatch_gap", platform=platform
        )
        return []


def _adaptive_fallback_runner(source: Source) -> List[Dict]:
    """TIER 3 (ADAPTIVE) fallback for sources with no known structured ATS
    connector.

    Per the Notion lesson (§8-10): never guess a page-specific scraper for an
    "unknown" source before checking whether it is actually a KNOWN ATS we
    just haven't recorded (employer migrated, or the seed data is stale). So
    this always runs source discovery FIRST and only drops to the real
    out-of-process Scrapling adaptive extractor if discovery finds nothing.
    """
    import os
    import structlog
    from django.conf import settings

    log = structlog.get_logger()
    company_slug = source.slug
    platform = (source.ats_platform or '').lower()
    if platform and company_slug.endswith(f"-{platform}"):
        company_slug = company_slug[: -len(f"-{platform}")]

    # Step 1: source discovery — probe known ATS endpoint templates before
    # ever paying for the heavier adaptive/out-of-process tier.
    try:
        import requests
        from .strategy_router import STRUCTURED_ATS
        from .pipeline.source_discovery import discover_ats

        def _fetcher(url):
            r = requests.get(url, timeout=15, headers={"User-Agent": "usam-jobs-discovery/1.0"})
            try:
                payload = r.json()
            except ValueError:
                payload = None
            return r.status_code, payload

        discovery = discover_ats(company_slug, fetcher=_fetcher)
        if discovery.healthy and discovery.provider in STRUCTURED_ATS:
            log.info(
                "adaptive_fallback_discovered_known_ats",
                source=source.slug, provider=discovery.provider,
                job_count=discovery.job_count,
            )
            jobs = _dispatch_structured_ats(discovery.provider, discovery.tenant or company_slug)
            if jobs:
                return jobs
    except Exception as e:
        log.warning("adaptive_fallback_discovery_failed", source=source.slug, error=str(e))

    # Step 2: real Tier-3 adaptive extraction via the isolated Scrapling
    # out-of-process runner. Inert (returns []) unless SCRAPLING_RUNNER_PYTHON
    # is configured — Scrapling is never installed into this venv.
    url = getattr(source, 'url', '') or ''
    if not url:
        return []

    # Two equally-valid ways to configure the isolated runner (§5 of the
    # Dockerfile docstring): a full command list (e.g. the reproducible
    # Docker image) takes priority over a bare python-executable path.
    runner_cmd_list = list(getattr(settings, 'SCRAPLING_RUNNER_CMD', []) or [])
    runner_python = getattr(settings, 'SCRAPLING_RUNNER_PYTHON', '') or os.environ.get('SCRAPLING_RUNNER_PYTHON', '')

    if runner_cmd_list:
        runner_cmd = runner_cmd_list
    elif runner_python:
        runner_script = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "extraction_runners", "scrapling_runner.py",
        ))
        runner_cmd = [runner_python, runner_script]
    else:
        log.info("adaptive_fallback_no_runner_configured", source=source.slug)
        return []

    try:
        from .pipeline.extraction_adapter import OutOfProcessBackend, ExtractionTier

        backend = OutOfProcessBackend(
            name="scrapling", tier=ExtractionTier.ADAPTIVE_PARSER,
            runner_cmd=runner_cmd,
        )
        if not backend.available():
            return []
        result = backend.extract(url)
        if not result.ok:
            log.info("adaptive_fallback_no_jobs", source=source.slug, error=result.error)
        return result.jobs or []
    except Exception as e:
        log.warning("adaptive_fallback_runner_failed", source=source.slug, error=str(e))
        return []


def scrape_source(source: Source) -> List[Dict]:
    """
    Scrape jobs from a single source.

    Routes through StrategyRouter (apps.scraper.strategy_router) so the tiered
    acquisition strategy is the REAL dispatch path, not a parallel/inert one.
    structured_runner wraps the exact pre-existing if/elif dispatch (zero
    behavior change for any source with a known ats_platform); adaptive_runner
    is the new Tier-3 fallback (source discovery -> Scrapling out-of-process),
    only reached for sources whose platform is NOT in STRUCTURED_ATS.
    """
    router = StrategyRouter(
        structured_runner=_dispatch_structured_ats,
        adaptive_runner=_adaptive_fallback_runner,
    )
    jobs, _decision = router.run(source)
    return jobs


def process_and_store_jobs(jobs: List[Dict], source: Source) -> int:
    """
    Process scraped jobs and store valid ones to database.
    Returns count of jobs added.
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
                # Skip jobs without direct apply URLs
                continue
            
            # 2. Check ATS fingerprint - block blocked aggregators
            ats_result = ats_stage.run(apply_url)
            if ats_result.platform == "BLOCKED_AGGREGATOR":
                blocked_count += 1
                continue
            
            # 3. Calculate legitimacy score
            legitimacy_score, legitimacy_flags = calculate_legitimacy_score(job_data)
            
            # Skip obviously scam jobs
            if legitimacy_score < 0.4:
                continue
            
            # 4. Resolve to ONE canonical company (§11 Company Resolution
            #    Service) instead of the old inline get_or_create, which
            #    stored the raw lowercase board slug as the company's NAME
            #    (e.g. a company literally named "stripe"). The resolver also
            #    persists a (platform, tenant_slug) -> Company identity so a
            #    future ATS migration for this same employer (see
            #    source_discovery.py's Notion/Plaid/Ramp lesson) reuses this
            #    Company instead of creating a duplicate.
            platform = job_data.get('ats_platform', '') or (source.ats_platform or '')
            tenant_slug = job_data.get('company_slug', '') or source.slug
            resolution = company_resolver.resolve(
                platform=platform,
                tenant_slug=tenant_slug,
                company_domain=job_data.get('company_domain', ''),
                fallback_name=source.name,
                source=source,
            )
            company = resolution.company
            
            # 5. Generate job hash for deduplication
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
                existing.quality_state = 'probably_active'
                existing.save(update_fields=['is_expired', 'quality_state'])
                continue
            
            # 7. Create new job
            slug = generate_job_slug(
                company.name,
                job_data.get('title', ''),
                job_data.get('ats_job_id', '')
            )
            
            from datetime import date

            # location_type + industry are REQUIRED on Job; clamp experience_level
            # to valid choices (entry/mid/senior/lead). Previously omitted →
            # every create raised and was swallowed (fetched N / added 0).
            _exp = normalize_experience_level(job_data.get('experience_level')) or 'mid'
            _exp = {'director': 'lead', 'executive': 'lead', 'c_level': 'lead',
                    'student': 'entry', 'junior': 'entry'}.get(_exp, _exp)
            if _exp not in {'entry', 'mid', 'senior', 'lead'}:
                _exp = 'mid'
            _work_arr = normalize_remote_type(job_data.get('remote_type')) or 'onsite'
            _loc_type = _work_arr if _work_arr in {'remote', 'hybrid', 'onsite'} else 'onsite'
            _industry = getattr(company, 'industry', '') or 'technology'

            try:
                job = Job.objects.create(
                    company=company,
                    source=source,
                    title=job_data.get('title', ''),
                    slug=slug,
                    description=job_data.get('description', ''),
                    location=normalize_location(job_data.get('location', '')) or 'Not specified',
                    location_type=_loc_type,
                    industry=_industry,
                    direct_apply_url=apply_url,
                    source_type='scraped',
                    employment_type=normalize_employment_type(job_data.get('employment_type')) or 'full_time',
                    experience_level=_exp,
                    work_arrangement=_work_arr,
                    salary_min=job_data.get('salary_min'),
                    salary_max=job_data.get('salary_max'),
                    salary_currency=job_data.get('salary_currency', 'USD'),
                    posted_at=date.today(),
                    scraped_at=timezone.now(),
                    expires_at=timezone.now() + timedelta(days=90),
                    legitimacy_score=legitimacy_score,
                    legitimacy_flags=legitimacy_flags,
                    ats_platform=job_data.get('ats_platform', ''),
                    ats_job_id=job_data.get('ats_job_id', ''),
                    raw_data=job_data.get('raw_data', {}),
                    field_provenance=build_provenance(
                        job_data,
                        source=job_data.get('ats_platform') or source.slug,
                        method='ats_api',
                        confidence=1.0,
                    ),
                )
            except Exception as ce:
                import structlog
                structlog.get_logger().error(
                    "job_persistence_failed", error=str(ce),
                    error_type=type(ce).__name__, title=job_data.get('title'),
                    source=source.slug,
                )
                continue

            # 8. Run full verification on new job
            try:
                verification_result = verification_engine.verify_job(job)
                verified_count += 1
            except Exception as ve:
                # Log verification error but don't block the job
                print(f"Verification failed for job {job.id}: {ve}")
            
            added_count += 1
            
        except Exception as e:
            # Log error and continue
            print(f"Failed to process job: {e}")
            continue
    
    return added_count


@shared_task
def verify_apply_urls():
    """
    Daily task - checks every active job's apply URL using verification engine.
    Marks jobs as expired if URL is dead.
    """
    from apps.verification.engine import VerificationEngine
    
    start_time = timezone.now()
    checked = 0
    expired = 0
    
    try:
        # Get all active jobs
        jobs = Job.objects.filter(is_expired=False)
        
        verification_engine = VerificationEngine()
        
        for job in jobs.iterator():
            try:
                # Run verification to check URL liveness
                result = verification_engine.verify_job(job)
                
                if result.status == "expired" or not result.url_accessible:
                    job.is_expired = True
                    job.quality_state = 'expired'
                    expired += 1

                checked += 1
            except Exception as ve:
                print(f"Verification failed for job {job.id}: {ve}")
                continue

            job.save(update_fields=['is_expired', 'quality_state'])
        
        # Update pipeline health
        duration = (timezone.now() - start_time).total_seconds()
        pipeline_health, created = PipelineHealth.objects.get_or_create(
            task_name='verify_apply_urls',
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
def verify_employer_posted_job(job_id: int):
    """
    Verify employer-posted jobs. Auto-verifies if employer is verified.
    """
    from apps.verification.engine import VerificationEngine
    
    try:
        job = Job.objects.get(id=job_id)
        verification_engine = VerificationEngine()
        result = verification_engine.verify_employer_posted_job(job)
        return {
            'status': result.status,
            'trust_score': result.trust_score,
        }
    except Job.DoesNotExist:
        return {'error': 'Job not found'}


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
    ).update(is_expired=True, quality_state='expired')
    
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


@shared_task
def scrape_single_url(url: str):
    """
    Scrape jobs from a single URL using the adaptive scraper.
    Triggered by changedetection.io when a career page changes.
    """
    try:
        from apps.intelligence.adaptive_scraper import get_adaptive_scraper

        scraper = get_adaptive_scraper()
        jobs = scraper.scrape_career_page(url)

        if not jobs:
            return {'url': url, 'found': 0, 'added': 0}

        source = Source.objects.filter(url__icontains=url[:100]).first()
        if not source:
            return {'url': url, 'found': len(jobs), 'added': 0, 'note': 'No matching source'}

        added = process_and_store_jobs(jobs, source)
        return {'url': url, 'found': len(jobs), 'added': added}

    except Exception as e:
        return {'url': url, 'error': str(e)}


@shared_task
def process_career_page_changes():
    """
    Process all detected career page changes from changedetection.io.
    Scheduled to run every hour.
    """
    from .change_detection import get_career_page_monitor

    monitor = get_career_page_monitor()
    if not monitor.is_available:
        return {'status': 'skipped', 'reason': 'changedetection.io not available'}

    result = monitor.process_changes()
    return result


@shared_task
def register_career_pages_for_monitoring():
    """Register all active sources for career page monitoring."""
    from .change_detection import get_career_page_monitor

    monitor = get_career_page_monitor()
    if not monitor.is_available:
        return {'status': 'skipped', 'reason': 'changedetection.io not available'}

    registered = monitor.register_source_pages()
    return {'registered': registered}