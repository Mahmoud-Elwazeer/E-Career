"""
Individual vs Company separation — authorization hardening tests.

Locks in: team management is owner/admin-only; insider_connections is employer-
gated (a job seeker cannot reach it); individual discoverability is owner-only.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.employers.models import EmployerProfile, EmployerTeamMember
from apps.jobs.models import Company

User = get_user_model()
pytestmark = pytest.mark.django_db


def _client(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


@pytest.fixture
def company(db):
    return Company.objects.create(name="Acme", slug="acme", industry="technology", is_active=True)


@pytest.fixture
def owner(db, company):
    u = User.objects.create_user(email="owner@acme.com", password="Pass1234!", role="employer")
    EmployerProfile.objects.create(user=u, company=company, job_title="CEO", is_verified=True)
    return u


@pytest.fixture
def viewer_member(db, company):
    from django.utils import timezone
    u = User.objects.create_user(email="viewer@acme.com", password="Pass1234!", role="employer")
    EmployerProfile.objects.create(user=u, company=company, job_title="Viewer", is_verified=True)
    EmployerTeamMember.objects.create(
        user=u, company=company, role="viewer", is_active=True, accepted_at=timezone.now(),
    )
    return u


@pytest.fixture
def seeker(db):
    return User.objects.create_user(email="seeker@x.com", password="Pass1234!", role="user")


# ── Team RBAC ────────────────────────────────────────────────────────────────
def test_owner_can_invite_team_member(owner):
    User.objects.create_user(email="invitee@acme.com", password="Pass1234!")
    resp = _client(owner).post("/api/v1/employer/team/invite/", {"email": "invitee@acme.com", "role": "recruiter"}, format="json")
    assert resp.status_code in (200, 201)


def test_viewer_member_cannot_invite(viewer_member):
    User.objects.create_user(email="invitee2@acme.com", password="Pass1234!")
    resp = _client(viewer_member).post("/api/v1/employer/team/invite/", {"email": "invitee2@acme.com", "role": "recruiter"}, format="json")
    assert resp.status_code == 403


# ── insider_connections is employer-gated ────────────────────────────────────
def test_seeker_cannot_access_insider_connections(seeker, company):
    resp = _client(seeker).get(f"/api/v1/employer/connections/{company.id}/")
    assert resp.status_code == 403


# ── Discoverability is owner-only + togglable ────────────────────────────────
def test_discoverability_default_false_then_toggle(seeker):
    c = _client(seeker)
    get = c.get("/api/v1/career/discoverability/")
    assert get.status_code == 200
    assert get.json()["data"]["is_discoverable"] is False
    patch = c.patch("/api/v1/career/discoverability/", {"is_discoverable": True}, format="json")
    assert patch.status_code == 200
    assert patch.json()["data"]["is_discoverable"] is True


def test_discoverability_requires_auth():
    resp = APIClient().get("/api/v1/career/discoverability/")
    assert resp.status_code in (401, 403)


# ── Create company (Sections 15-16) ──────────────────────────────────────────
def test_create_company_makes_caller_owner(seeker):
    from apps.employers.models import EmployerProfile, EmployerTeamMember
    resp = _client(seeker).post("/api/v1/employer/companies/create/", {
        "name": "Newco Ltd", "industry": "technology", "size": "11-50", "website": "https://newco.example",
    }, format="json")
    assert resp.status_code == 201
    seeker.refresh_from_db()
    assert seeker.role == "employer"
    prof = EmployerProfile.objects.get(user=seeker)
    assert prof.company.name == "Newco Ltd"
    tm = EmployerTeamMember.objects.get(user=seeker, company=prof.company)
    assert tm.role == "owner"


def test_create_company_rejected_if_already_employer(owner):
    resp = _client(owner).post("/api/v1/employer/companies/create/", {"name": "Another"}, format="json")
    assert resp.status_code == 400
