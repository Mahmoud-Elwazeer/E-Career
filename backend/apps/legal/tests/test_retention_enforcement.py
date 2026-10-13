"""
Retention enforcement engine tests (production-hardening pass).

Verifies:
  - Categories with requires_legal_review=True or no retention_period_days
    are reported as not-enforceable, never silently acted on.
  - An unregistered category (no handler) is reported, not guessed at.
  - DRY_RUN (the default) finds candidates but writes nothing.
  - --execute actually enforces for a registered, legally-confirmed category.
  - A user under an active LegalHold is excluded from enforcement.
"""
import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from io import StringIO

from apps.career.models import CareerProfile, InterviewSession
from apps.legal.models import RetentionPolicy, LegalHold
from apps.legal.retention_service import run_retention_enforcement

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_requires_legal_review_category_is_never_enforced():
    RetentionPolicy.objects.create(
        data_category="interview_transcripts", retention_period_days=90,
        requires_legal_review=True,  # explicitly NOT confirmed yet
    )
    report = run_retention_enforcement(dry_run=False)
    result = next(r for r in report.results if r.category == "interview_transcripts")
    assert result.enforceable is False
    assert "requires_legal_review" in result.reason


def test_unconfigured_retention_period_is_never_enforced():
    RetentionPolicy.objects.create(
        data_category="interview_transcripts", retention_period_days=None,
        requires_legal_review=False,
    )
    report = run_retention_enforcement(dry_run=False)
    result = next(r for r in report.results if r.category == "interview_transcripts")
    assert result.enforceable is False
    assert "retention_period_days" in result.reason


def test_unregistered_category_is_reported_not_guessed(): 
    RetentionPolicy.objects.create(
        data_category="some_future_category_with_no_handler", retention_period_days=30,
        requires_legal_review=False,
    )
    report = run_retention_enforcement(dry_run=False)
    result = next(r for r in report.results if r.category == "some_future_category_with_no_handler")
    assert result.enforceable is False
    assert "no enforcement handler" in result.reason


def test_dry_run_finds_candidates_but_writes_nothing():
    RetentionPolicy.objects.create(
        data_category="interview_transcripts", retention_period_days=30,
        requires_legal_review=False,
    )
    user = User.objects.create_user(email="interview-ret@test.com", password="pw12345x")
    old_session = InterviewSession.objects.create(
        user=user, interview_type="technical", transcript="some old transcript text",
    )
    # Backdate created_at past the retention cutoff (auto_now_add bypassed via update()).
    InterviewSession.objects.filter(pk=old_session.pk).update(
        created_at=timezone.now() - timedelta(days=60),
    )

    report = run_retention_enforcement(dry_run=True)
    result = next(r for r in report.results if r.category == "interview_transcripts")
    assert result.enforceable is True
    assert result.candidates_found == 1
    assert result.affected == 0  # dry run — nothing written

    old_session.refresh_from_db()
    assert old_session.transcript == "some old transcript text"  # untouched


def test_execute_actually_clears_aged_interview_transcripts():
    RetentionPolicy.objects.create(
        data_category="interview_transcripts", retention_period_days=30,
        requires_legal_review=False,
    )
    user = User.objects.create_user(email="interview-ret2@test.com", password="pw12345x")
    old_session = InterviewSession.objects.create(
        user=user, interview_type="technical", transcript="sensitive old content",
    )
    InterviewSession.objects.filter(pk=old_session.pk).update(
        created_at=timezone.now() - timedelta(days=60),
    )
    recent_session = InterviewSession.objects.create(
        user=user, interview_type="technical", transcript="recent content",
    )

    report = run_retention_enforcement(dry_run=False)
    result = next(r for r in report.results if r.category == "interview_transcripts")
    assert result.affected == 1

    old_session.refresh_from_db()
    recent_session.refresh_from_db()
    assert old_session.transcript == ""  # cleared
    assert recent_session.transcript == "recent content"  # untouched (not aged out)


def test_legal_hold_excludes_user_from_enforcement():
    RetentionPolicy.objects.create(
        data_category="interview_transcripts", retention_period_days=30,
        requires_legal_review=False,
    )
    held_user = User.objects.create_user(email="held@test.com", password="pw12345x")
    LegalHold.objects.create(
        reference="HOLD-001", scope_description="litigation", reason="legal matter",
        user=held_user,
    )
    old_session = InterviewSession.objects.create(
        user=held_user, interview_type="technical", transcript="protected by legal hold",
    )
    InterviewSession.objects.filter(pk=old_session.pk).update(
        created_at=timezone.now() - timedelta(days=60),
    )

    report = run_retention_enforcement(dry_run=False)
    result = next(r for r in report.results if r.category == "interview_transcripts")
    assert result.candidates_found == 0  # excluded before even being counted
    assert result.affected == 0

    old_session.refresh_from_db()
    assert old_session.transcript == "protected by legal hold"


def test_management_command_defaults_to_dry_run():
    RetentionPolicy.objects.create(
        data_category="interview_transcripts", retention_period_days=30,
        requires_legal_review=False,
    )
    user = User.objects.create_user(email="cmd-dryrun@test.com", password="pw12345x")
    old_session = InterviewSession.objects.create(
        user=user, interview_type="technical", transcript="old content",
    )
    InterviewSession.objects.filter(pk=old_session.pk).update(
        created_at=timezone.now() - timedelta(days=60),
    )

    out = StringIO()
    call_command("enforce_retention", stdout=out)
    assert "DRY RUN" in out.getvalue()

    old_session.refresh_from_db()
    assert old_session.transcript == "old content"  # command alone (no --execute) wrote nothing


def test_management_command_execute_flag_actually_enforces():
    RetentionPolicy.objects.create(
        data_category="interview_transcripts", retention_period_days=30,
        requires_legal_review=False,
    )
    user = User.objects.create_user(email="cmd-execute@test.com", password="pw12345x")
    old_session = InterviewSession.objects.create(
        user=user, interview_type="technical", transcript="old content",
    )
    InterviewSession.objects.filter(pk=old_session.pk).update(
        created_at=timezone.now() - timedelta(days=60),
    )

    out = StringIO()
    call_command("enforce_retention", "--execute", stdout=out)
    assert "EXECUTE" in out.getvalue()

    old_session.refresh_from_db()
    assert old_session.transcript == ""
