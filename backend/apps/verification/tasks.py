from __future__ import annotations

import structlog
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def verify_job_task(self, job_id: int):
    """Run full verification on a single job."""
    from apps.jobs.models import Job
    from apps.verification.engine import VerificationEngine

    try:
        job = Job.objects.select_related("company").get(id=job_id)
    except Job.DoesNotExist:
        logger.warning("verify_job_not_found", job_id=job_id)
        return

    engine = VerificationEngine()

    if job.source_type == "employer_posted":
        result = engine.verify_employer_posted_job(job)
    else:
        result = engine.verify_job(job)

    logger.info(
        "verification_task_done",
        job_id=job_id,
        status=result.status,
        trust_score=result.trust_score,
    )


@shared_task
def daily_liveness_check():
    """Periodic: HEAD request to all active job URLs to detect expired listings."""
    from apps.jobs.models import Job
    from apps.verification.models import VerificationResult
    from apps.verification.stages import FreshnessCheckerStage

    checker = FreshnessCheckerStage()
    now = timezone.now()
    cutoff = now - timedelta(hours=24)

    jobs = (
        Job.objects.filter(status="active", is_expired=False)
        .exclude(verification__last_verified_at__gte=cutoff)
        .select_related("verification")[:500]
    )

    checked = 0
    expired = 0

    for job in jobs:
        url = job.direct_apply_url or job.source_url
        result = checker.run(url)

        try:
            vr = job.verification
        except VerificationResult.DoesNotExist:
            continue

        vr.last_verified_at = now
        vr.http_status_code = result.http_status

        if not result.is_accessible or result.is_closed:
            vr.consecutive_failures += 1
            if vr.consecutive_failures >= 3:
                vr.status = "expired"
                job.is_expired = True
                job.save(update_fields=["is_expired"])
                expired += 1
        else:
            vr.consecutive_failures = 0
            vr.url_accessible = True

        vr.save(update_fields=[
            "last_verified_at", "http_status_code",
            "consecutive_failures", "url_accessible", "status",
        ])
        checked += 1

    logger.info("daily_liveness_complete", checked=checked, expired=expired)


@shared_task
def weekly_full_reverification():
    """Periodic: Full re-verification of all active jobs."""
    from apps.jobs.models import Job

    job_ids = list(
        Job.objects.filter(status="active", is_expired=False)
        .values_list("id", flat=True)[:1000]
    )

    for job_id in job_ids:
        verify_job_task.delay(job_id)

    logger.info("weekly_reverification_queued", count=len(job_ids))
