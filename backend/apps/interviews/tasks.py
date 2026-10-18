"""
Celery tasks for interview session lifecycle cleanup (directive item 17).

Two complementary sweeps:
  1. `mark_stale_interview_sessions_abandoned` — an InterviewSession stuck
     in `in_progress` for a long time (browser closed mid-recording,
     network dropped, user walked away) is never explicitly completed or
     abandoned today — the `'abandoned'` status choice exists on the model
     but nothing ever sets it. This sweep does.
  2. `cleanup_orphaned_voice_interview_audio` — defense-in-depth for raw
     audio objects in S3 that were never cleaned up. `voice_service.
     speech_to_text` now deletes its own object in a `finally` block on
     every exit path (success, terminal transcription failure, exception),
     so this sweep should normally find nothing — it exists to catch any
     object that slipped through anyway (e.g. a crash between upload and
     the finally block running, or a pre-existing orphan from before this
     fix shipped). No DB field persists the S3 key for a given object, so
     this sweep works by listing the `interviews/audio_*.mp3` prefix and
     deleting anything older than a safety window — a legitimate in-flight
     object is deleted by `speech_to_text` within ~30 seconds, so an object
     surviving past the window is, by construction, orphaned.
"""
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# An in-flight speech_to_text call never takes longer than ~30s (its own
# poll timeout) plus upload/download overhead — anything surviving well
# past that under the audio prefix is orphaned, not legitimately in-flight.
ORPHAN_AUDIO_SAFETY_WINDOW_SECONDS = 15 * 60  # 15 minutes

# A session with no activity for this long is considered abandoned rather
# than genuinely still in progress.
STALE_SESSION_THRESHOLD_HOURS = 24


@shared_task
def mark_stale_interview_sessions_abandoned():
    """Find InterviewSession rows stuck in_progress past the stale
    threshold and mark them abandoned. Never touches a session that has
    already completed."""
    from .models import InterviewSession

    cutoff = timezone.now() - timezone.timedelta(hours=STALE_SESSION_THRESHOLD_HOURS)
    stale = InterviewSession.objects.filter(status='in_progress', started_at__lt=cutoff)
    count = stale.update(status='abandoned')
    logger.info(f"mark_stale_interview_sessions_abandoned: marked {count} session(s) abandoned")
    return {"marked_abandoned": count}


@shared_task
def cleanup_orphaned_voice_interview_audio():
    """Defense-in-depth sweep for raw audio S3 objects that outlived the
    safety window — see module docstring. Returns a summary dict; never
    raises on an individual object's delete failure (logs and continues)."""
    import boto3

    bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    prefix = getattr(settings, 'AWS_MEDIA_PREFIX', 'interviews')
    if not bucket:
        logger.warning("cleanup_orphaned_voice_interview_audio: no AWS_STORAGE_BUCKET_NAME configured, skipping")
        return {"scanned": 0, "deleted": 0, "skipped_no_bucket": True}

    s3 = boto3.client('s3', region_name=getattr(settings, 'AWS_REGION', 'us-east-1'))
    audio_prefix = f"{prefix}/audio_"
    cutoff = timezone.now() - timezone.timedelta(seconds=ORPHAN_AUDIO_SAFETY_WINDOW_SECONDS)

    scanned = 0
    deleted = 0
    failed = 0

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=audio_prefix):
        for obj in page.get('Contents', []):
            scanned += 1
            last_modified = obj['LastModified']
            if last_modified.tzinfo is None:
                last_modified = last_modified.replace(tzinfo=timezone.utc)
            if last_modified >= cutoff:
                continue  # still within the legitimate in-flight window
            try:
                s3.delete_object(Bucket=bucket, Key=obj['Key'])
                deleted += 1
                logger.warning(f"cleanup_orphaned_voice_interview_audio: deleted orphaned object {obj['Key']}")
            except Exception as e:
                failed += 1
                logger.error(f"cleanup_orphaned_voice_interview_audio: failed to delete {obj['Key']}: {e}")

    logger.info(
        f"cleanup_orphaned_voice_interview_audio: scanned={scanned} deleted={deleted} failed={failed}"
    )
    return {"scanned": scanned, "deleted": deleted, "failed": failed}
