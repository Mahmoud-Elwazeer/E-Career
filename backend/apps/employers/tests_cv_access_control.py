"""
CV/document access-control + upload-validation tests (directive item 16).

Covers the fixes for a previously-disclosed, now-confirmed gap: CVs were
served via a bare, predictable, unauthenticated media URL
(JobApplicationSerializer.get_cv_url returned obj.cv_snapshot.url directly).
Also covers the job-application CV upload path, which previously bypassed
apps.core.upload_security entirely (no size/extension/magic-byte check, no
malware scan) even though it accepts the same kind of file as the primary
CV upload endpoint.
"""
from io import BytesIO
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.employers.models import EmployerProfile, JobApplication
from apps.jobs.models import Company, Job, Source

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def company():
    return Company.objects.create(name="Acme Corp", slug="acme-cv-access", industry="technology", is_active=True)


@pytest.fixture
def other_company():
    return Company.objects.create(name="Beta Corp", slug="beta-cv-access", industry="technology", is_active=True)


@pytest.fixture
def employer_user(company):
    user = User.objects.create_user(email="cv-employer@test.com", password="pw12345x", role="employer")
    EmployerProfile.objects.create(user=user, company=company, job_title="Recruiter", is_verified=True)
    return user


@pytest.fixture
def other_employer_user(other_company):
    user = User.objects.create_user(email="cv-other-employer@test.com", password="pw12345x", role="employer")
    EmployerProfile.objects.create(user=user, company=other_company, job_title="Recruiter", is_verified=True)
    return user


@pytest.fixture
def employer_client(employer_user):
    c = APIClient()
    c.force_authenticate(user=employer_user)
    return c


@pytest.fixture
def other_employer_client(other_employer_user):
    c = APIClient()
    c.force_authenticate(user=other_employer_user)
    return c


@pytest.fixture
def candidate_user():
    return User.objects.create_user(email="cv-candidate@test.com", password="pw12345x")


@pytest.fixture
def job(company, employer_user):
    import datetime
    from apps.employers.models import JobPosting

    source = Source.objects.create(name="Direct", slug="direct-cv-access", url="https://example.com")
    j = Job.objects.create(
        title="Backend Engineer", slug="backend-engineer-cv-access", company=company,
        location="Cairo", location_type="onsite", industry="technology",
        experience_level="mid", source_url="https://example.com/1", source=source,
        status="active", posted_at=datetime.date(2026, 1, 1),
    )
    # The CV-download authorization check filters through
    # job__employer_posting__employer — link this Job to a JobPosting owned
    # by the employer fixture so get_queryset actually matches it.
    JobPosting.objects.create(
        employer=employer_user.employer_profile, company=company, mirrored_job=j,
        title=j.title, description="desc", requirements="reqs",
        apply_url="https://example.com/apply", employment_type="full_time",
        experience_level="mid", remote_type="onsite", location="Cairo",
        status="published",
    )
    return j


@pytest.fixture
def application_with_cv(job, candidate_user):
    cv = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 fake pdf content", content_type="application/pdf")
    return JobApplication.objects.create(user=candidate_user, job=job, cv_snapshot=cv)


# ── Access control: only the owning employer can fetch the CV bytes ────────

def test_owning_employer_can_download_cv(employer_client, application_with_cv):
    resp = employer_client.get(f"/api/v1/employer/applications/{application_with_cv.id}/cv/")
    assert resp.status_code == 200
    assert b"".join(resp.streaming_content) == b"%PDF-1.4 fake pdf content"


def test_other_employer_cannot_download_cv(other_employer_client, application_with_cv):
    """Directive-critical: a different employer must never reach another
    employer's applicant's CV bytes — not even by guessing/constructing the
    URL, since the endpoint re-derives authorization from get_queryset on
    every request, not from a client-supplied token."""
    resp = other_employer_client.get(f"/api/v1/employer/applications/{application_with_cv.id}/cv/")
    assert resp.status_code == 404


def test_unauthenticated_cannot_download_cv(application_with_cv):
    resp = APIClient().get(f"/api/v1/employer/applications/{application_with_cv.id}/cv/")
    assert resp.status_code in (401, 403)


def test_cv_url_in_serializer_points_at_authenticated_endpoint_not_bare_media_url(
    employer_client, application_with_cv,
):
    """The serializer must no longer hand out obj.cv_snapshot.url (a bare,
    predictable, unauthenticated media path) — it must point at the
    authorization-checked download endpoint instead."""
    resp = employer_client.get(f"/api/v1/employer/applications/{application_with_cv.id}/")
    assert resp.status_code == 200
    cv_url = resp.json()["data"]["cv_url"]
    assert f"/applications/{application_with_cv.id}/cv/" in cv_url
    assert "/media/" not in cv_url


def test_download_cv_404s_cleanly_when_no_cv_present(employer_client, job, candidate_user):
    application = JobApplication.objects.create(user=candidate_user, job=job)  # no cv_snapshot
    resp = employer_client.get(f"/api/v1/employer/applications/{application.id}/cv/")
    assert resp.status_code == 404


# ── Upload validation: job-application CV upload must go through the ───────
# ── same malware-scan/extension/size pipeline as the primary CV upload ─────

@pytest.fixture
def auth_candidate_client(candidate_user):
    c = APIClient()
    c.force_authenticate(user=candidate_user)
    return c


def test_submit_application_rejects_disallowed_file_extension(auth_candidate_client, job):
    bad_file = SimpleUploadedFile("resume.exe", b"MZ fake exe content", content_type="application/octet-stream")
    resp = auth_candidate_client.post(
        f"/api/v1/jobs/{job.slug}/submit-application/",
        {"cv_file": bad_file}, format="multipart",
    )
    assert resp.status_code == 400
    assert not JobApplication.objects.filter(job=job, user=auth_candidate_client.handler._force_user).exists()


@mock.patch("apps.core.upload_security.scan_stream_for_malware")
def test_submit_application_rejects_malware_detected_file(mock_scan, auth_candidate_client, job):
    from apps.core.upload_security import MalwareScanResult
    mock_scan.return_value = MalwareScanResult(clean=False, threat="Eicar-Test-Signature")

    cv = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 fake pdf", content_type="application/pdf")
    resp = auth_candidate_client.post(
        f"/api/v1/jobs/{job.slug}/submit-application/",
        {"cv_file": cv}, format="multipart",
    )
    assert resp.status_code == 400
    assert "malware" in resp.json()["message"].lower()
    assert not JobApplication.objects.filter(job=job).exists()


@mock.patch("apps.core.upload_security.scan_stream_for_malware")
def test_submit_application_accepts_clean_valid_file(mock_scan, auth_candidate_client, job):
    from apps.core.upload_security import MalwareScanResult
    mock_scan.return_value = MalwareScanResult(clean=True)

    cv = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 clean pdf", content_type="application/pdf")
    resp = auth_candidate_client.post(
        f"/api/v1/jobs/{job.slug}/submit-application/",
        {"cv_file": cv}, format="multipart",
    )
    assert resp.status_code in (200, 201)
    assert JobApplication.objects.filter(job=job).exists()
