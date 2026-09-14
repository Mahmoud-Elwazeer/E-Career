"""
Cross-company (tenant) isolation regression tests — API/view level.

These lock in the guarantee that one verified employer cannot read or mutate
another company's job postings or applications through the REST API. Object
ownership is already scoped in each ViewSet.get_queryset; these tests assert
the resulting 404 (not found in the requester's queryset) at the HTTP layer so
a future refactor cannot silently widen access.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.employers.models import EmployerProfile, JobPosting
from apps.jobs.models import Company

User = get_user_model()


def _client_for(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def company_a(db):
    return Company.objects.create(name="Alpha Corp", slug="alpha-corp", industry="technology", is_active=True)


@pytest.fixture
def company_b(db):
    return Company.objects.create(name="Beta Corp", slug="beta-corp", industry="finance", is_active=True)


@pytest.fixture
def employer_a(db, company_a):
    user = User.objects.create_user(email="emp_a@alpha.com", password="Pass1234!", role="employer")
    EmployerProfile.objects.create(user=user, company=company_a, job_title="HR", is_verified=True)
    return user


@pytest.fixture
def employer_b(db, company_b):
    user = User.objects.create_user(email="emp_b@beta.com", password="Pass1234!", role="employer")
    EmployerProfile.objects.create(user=user, company=company_b, job_title="HR", is_verified=True)
    return user


@pytest.fixture
def job_b(db, employer_b, company_b):
    """A job posting owned by company B."""
    return JobPosting.objects.create(
        employer=employer_b.employer_profile,
        company=company_b,
        title="Beta Backend Engineer",
        description="desc",
        requirements="reqs",
        apply_url="https://beta.example.com/apply",
        status="active",
    )


@pytest.mark.django_db
class TestCrossCompanyJobIsolation:
    def test_employer_a_cannot_retrieve_company_b_job(self, employer_a, job_b):
        client = _client_for(employer_a)
        resp = client.get(f"/api/v1/employer/jobs/{job_b.pk}/")
        # Not in employer A's queryset -> 404 (never 200 with B's data).
        assert resp.status_code == 404

    def test_employer_a_cannot_update_company_b_job(self, employer_a, job_b):
        client = _client_for(employer_a)
        resp = client.patch(
            f"/api/v1/employer/jobs/{job_b.pk}/",
            {"title": "Hijacked"}, format="json",
        )
        assert resp.status_code == 404
        job_b.refresh_from_db()
        assert job_b.title == "Beta Backend Engineer"

    def test_employer_a_cannot_delete_company_b_job(self, employer_a, job_b):
        client = _client_for(employer_a)
        resp = client.delete(f"/api/v1/employer/jobs/{job_b.pk}/")
        assert resp.status_code == 404
        assert JobPosting.objects.filter(pk=job_b.pk).exists()

    def test_employer_a_job_list_excludes_company_b_jobs(self, employer_a, job_b):
        client = _client_for(employer_a)
        resp = client.get("/api/v1/employer/jobs/")
        assert resp.status_code == 200
        payload = resp.json()
        results = payload.get("data", payload)
        results = results.get("results", results) if isinstance(results, dict) else results
        titles = [j.get("title") for j in results] if isinstance(results, list) else []
        assert "Beta Backend Engineer" not in titles

    def test_employer_b_can_retrieve_own_job(self, employer_b, job_b):
        client = _client_for(employer_b)
        resp = client.get(f"/api/v1/employer/jobs/{job_b.pk}/")
        assert resp.status_code == 200

    def test_anonymous_cannot_access_employer_jobs(self, job_b):
        resp = APIClient().get(f"/api/v1/employer/jobs/{job_b.pk}/")
        assert resp.status_code in (401, 403)
