"""
EmployerProfileViewSet.list() for a brand-new employer — regression test.

Real bug found during the 2026-09-21 browser-E2E acceptance pass: a
freshly-registered employer-role user (signed up as "company" but hasn't
completed onboarding yet) has no EmployerProfile and no team membership,
so `IsEmployer.has_permission()` returned False and DRF short-circuited
`GET /api/v1/employer/profile/` with a 403 BEFORE `list()`'s own, correct
"no profile yet -> 404" handling ever ran. The frontend (EmployerDashboard.
tsx and others) only knows how to treat a 404 as "redirect to
/app/employer/register" — a 403 instead rendered as a generic, confusing
"Couldn't load your dashboard" error for every single first-time employer
signup, discovered via a real browser running this exact flow end-to-end.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def brand_new_employer():
    """A user who just signed up with account_type='company' -- role is
    already 'employer' (set at registration), but no EmployerProfile or
    team membership exists yet, matching the real signup flow exactly."""
    return User.objects.create_user(
        email="brand-new-employer@example.com",
        password="Pass1234!",
        first_name="New",
        last_name="Employer",
        role="employer",
    )


def test_brand_new_employer_gets_404_not_403_from_profile_list(brand_new_employer):
    client = APIClient()
    client.force_authenticate(user=brand_new_employer)
    resp = client.get("/api/v1/employer/profile/")
    assert resp.status_code == 404, (
        f"Expected a 404 ('no profile yet', the signal the frontend "
        f"correctly redirects to /app/employer/register on) — got "
        f"{resp.status_code} instead, which the frontend treats as an "
        f"opaque, unrecoverable error."
    )


def test_unauthenticated_request_still_rejected(db):
    client = APIClient()
    resp = client.get("/api/v1/employer/profile/")
    assert resp.status_code in (401, 403)


def test_other_employer_actions_still_require_a_real_employer_profile(brand_new_employer):
    """The fix only loosens the 'list' action -- every other action (the
    ones that genuinely require an existing employer profile/role) must
    still be blocked for a profile-less user."""
    client = APIClient()
    client.force_authenticate(user=brand_new_employer)
    resp = client.post("/api/v1/employer/profile/", {"company_name": "Test Co"}, format="json")
    assert resp.status_code in (403, 404)
