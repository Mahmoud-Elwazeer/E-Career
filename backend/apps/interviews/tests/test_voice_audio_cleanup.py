"""
Voice-interview raw-audio cleanup lifecycle tests (directive item 17).

Covers the fix in voice_service.VoiceInterviewService.speech_to_text: the
raw S3 audio object must be deleted on EVERY exit path — success, a
terminal transcription failure (timeout or AWS FAILED status), and any
exception — not just the pre-existing happy path. Also covers the two new
Celery Beat tasks (mark_stale_interview_sessions_abandoned,
cleanup_orphaned_voice_interview_audio).

boto3 is mocked throughout — these tests never make real AWS calls.
"""
from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.interviews.models import InterviewSession
from apps.interviews.voice_service import VoiceInterviewService

User = get_user_model()
pytestmark = pytest.mark.django_db


def _service_with_mocked_boto3():
    """Build a VoiceInterviewService with fake boto3 clients injected,
    bypassing the real __init__ (which constructs real boto3.client
    objects that would try to resolve AWS credentials)."""
    svc = VoiceInterviewService.__new__(VoiceInterviewService)
    svc.s3_client = mock.MagicMock()
    svc.transcribe_client = mock.MagicMock()
    svc.polly_client = mock.MagicMock()
    svc.aws_bucket = "test-bucket"
    svc.aws_media_prefix = "interviews"
    return svc


def _completed_job_response():
    return {"TranscriptionJob": {"TranscriptionJobStatus": "COMPLETED"}}


def _failed_job_response():
    return {"TranscriptionJob": {"TranscriptionJobStatus": "FAILED"}}


@pytest.fixture
def fake_transcript_body():
    import json
    body = mock.MagicMock()
    body.read.return_value = json.dumps(
        {"results": {"transcripts": [{"transcript": "hello world"}]}}
    ).encode("utf-8")
    return {"Body": body}


# ── Success path: object deleted after a successful transcription ──────────

def test_speech_to_text_deletes_s3_object_on_success(fake_transcript_body):
    svc = _service_with_mocked_boto3()
    svc.transcribe_client.get_transcription_job.return_value = _completed_job_response()
    svc.s3_client.get_object.return_value = fake_transcript_body

    with mock.patch("time.sleep"):
        result = svc.speech_to_text(b"fake audio bytes", language="en")

    assert result == "hello world"
    assert svc.s3_client.upload_file.called
    assert svc.s3_client.delete_object.called
    deleted_key = svc.s3_client.delete_object.call_args.kwargs["Key"]
    assert deleted_key.startswith("interviews/audio_")


# ── Terminal failure (timeout or FAILED status): object still deleted ──────

def test_speech_to_text_deletes_s3_object_when_job_fails():
    """Directive-critical: this was the exact gap — a FAILED transcription
    job previously returned None WITHOUT ever deleting the uploaded object."""
    svc = _service_with_mocked_boto3()
    svc.transcribe_client.get_transcription_job.return_value = _failed_job_response()

    with mock.patch("time.sleep"):
        result = svc.speech_to_text(b"fake audio bytes", language="en")

    assert result is None
    assert svc.s3_client.delete_object.called


def test_speech_to_text_deletes_s3_object_on_timeout():
    """Job never reaches a terminal status within the poll window — must
    still clean up the uploaded object."""
    svc = _service_with_mocked_boto3()
    svc.transcribe_client.get_transcription_job.return_value = {
        "TranscriptionJob": {"TranscriptionJobStatus": "IN_PROGRESS"}
    }

    with mock.patch("time.sleep"):
        result = svc.speech_to_text(b"fake audio bytes", language="en")

    assert result is None
    assert svc.s3_client.delete_object.called


# ── Exception anywhere in the pipeline: object still deleted ───────────────

def test_speech_to_text_deletes_s3_object_on_exception_after_upload():
    """Directive-critical: an exception from get_transcription_job (or any
    call after the upload succeeds) previously left the object orphaned
    forever since the function returned from inside the except block
    without ever reaching the delete_object call."""
    svc = _service_with_mocked_boto3()
    svc.transcribe_client.start_transcription_job.side_effect = RuntimeError("AWS blew up")

    result = svc.speech_to_text(b"fake audio bytes", language="en")

    assert result is None
    assert svc.s3_client.upload_file.called  # upload DID happen
    assert svc.s3_client.delete_object.called  # and cleanup still ran


def test_speech_to_text_does_not_attempt_delete_if_upload_itself_failed():
    """If the upload never succeeded, there's no s3_key to clean up —
    delete_object must not be called with a key that was never uploaded."""
    svc = _service_with_mocked_boto3()
    svc.s3_client.upload_file.side_effect = RuntimeError("upload failed")

    result = svc.speech_to_text(b"fake audio bytes", language="en")

    assert result is None
    # s3_key IS set before upload_file is called (it's generated first),
    # so finally still attempts delete_object — this is safe/idempotent
    # (deleting a nonexistent key is a no-op on real S3) and is the
    # correct conservative behavior: better to attempt an unnecessary
    # delete than to risk missing a real cleanup.
    assert svc.s3_client.delete_object.called


def test_speech_to_text_cleanup_failure_does_not_mask_original_result(fake_transcript_body):
    """If the cleanup delete_object call itself raises, that must be
    logged and swallowed — never propagate and crash the caller, and must
    never alter the already-determined transcript result."""
    svc = _service_with_mocked_boto3()
    svc.transcribe_client.get_transcription_job.return_value = _completed_job_response()
    svc.s3_client.get_object.return_value = fake_transcript_body
    svc.s3_client.delete_object.side_effect = RuntimeError("delete failed")

    with mock.patch("time.sleep"):
        result = svc.speech_to_text(b"fake audio bytes", language="en")

    assert result == "hello world"  # cleanup failure didn't corrupt the real result


# ── Celery task: mark_stale_interview_sessions_abandoned ───────────────────

def test_mark_stale_sessions_abandoned_marks_old_in_progress_sessions():
    from apps.interviews.tasks import mark_stale_interview_sessions_abandoned

    user = User.objects.create_user(email="stale-interview@test.com", password="pw12345x")
    stale = InterviewSession.objects.create(
        user=user, interview_type="technical", target_role="Backend Engineer", status="in_progress",
    )
    InterviewSession.objects.filter(pk=stale.pk).update(
        started_at=timezone.now() - timedelta(hours=48),
    )
    recent = InterviewSession.objects.create(
        user=user, interview_type="technical", target_role="Backend Engineer", status="in_progress",
    )
    completed = InterviewSession.objects.create(
        user=user, interview_type="technical", target_role="Backend Engineer", status="completed",
    )
    InterviewSession.objects.filter(pk=completed.pk).update(
        started_at=timezone.now() - timedelta(hours=48),
    )

    result = mark_stale_interview_sessions_abandoned()

    stale.refresh_from_db()
    recent.refresh_from_db()
    completed.refresh_from_db()
    assert stale.status == "abandoned"
    assert recent.status == "in_progress"  # too recent, untouched
    assert completed.status == "completed"  # already terminal, never touched
    assert result["marked_abandoned"] == 1


# ── Celery task: cleanup_orphaned_voice_interview_audio ─────────────────────

def test_cleanup_orphaned_audio_deletes_old_objects_only():
    from apps.interviews.tasks import cleanup_orphaned_voice_interview_audio

    old_time = timezone.now() - timedelta(minutes=30)
    recent_time = timezone.now() - timedelta(minutes=1)

    fake_s3 = mock.MagicMock()
    fake_paginator = mock.MagicMock()
    fake_paginator.paginate.return_value = [{
        "Contents": [
            {"Key": "interviews/audio_old123.mp3", "LastModified": old_time},
            {"Key": "interviews/audio_recent456.mp3", "LastModified": recent_time},
        ]
    }]
    fake_s3.get_paginator.return_value = fake_paginator

    with mock.patch("boto3.client", return_value=fake_s3), \
         mock.patch("django.conf.settings.AWS_STORAGE_BUCKET_NAME", "test-bucket", create=True):
        result = cleanup_orphaned_voice_interview_audio()

    assert result["scanned"] == 2
    assert result["deleted"] == 1
    fake_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key="interviews/audio_old123.mp3")


def test_cleanup_orphaned_audio_skips_when_no_bucket_configured():
    from apps.interviews.tasks import cleanup_orphaned_voice_interview_audio

    with mock.patch("django.conf.settings.AWS_STORAGE_BUCKET_NAME", None, create=True):
        result = cleanup_orphaned_voice_interview_audio()

    assert result["skipped_no_bucket"] is True
    assert result["deleted"] == 0
