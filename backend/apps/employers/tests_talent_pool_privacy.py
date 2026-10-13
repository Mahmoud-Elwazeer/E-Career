"""
Talent Pool privacy end-to-end tests (production-hardening pass).

Verifies the ACTUAL employer-facing data path, not just the toggle response:
  - Candidate OFF (is_discoverable=False) -> employer cannot discover or add.
  - Candidate ON -> employer can add, candidate appears in pool detail/ranking.
  - Candidate withdraws AFTER being added to a saved pool -> they must stop
    appearing to the employer going forward (the real gap this pass fixes:
    `was_discoverable_at_creation` is an audit snapshot, not a current-
    visibility gate — `TalentPool.active_candidates()` now re-checks live
    `CareerProfile.is_discoverable` on every read).
  - The audit record (`TalentPoolCandidate` row) is NOT deleted on withdrawal
    — only the employer-facing "currently visible" view excludes it.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.career.models import CareerProfile
from apps.employers.models import EmployerProfile, TalentPool, TalentPoolCandidate
from apps.jobs.models import Company

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def company():
    return Company.objects.create(name="Acme Corp", slug="acme-corp", industry="technology", is_active=True)


@pytest.fixture
def employer_user(company):
    user = User.objects.create_user(email="employer@test.com", password="pw12345x", role="employer")
    EmployerProfile.objects.create(user=user, company=company, job_title="Recruiter", is_verified=True)
    return user


@pytest.fixture
def employer_client(employer_user):
    c = APIClient()
    c.force_authenticate(user=employer_user)
    return c


@pytest.fixture
def candidate_user():
    return User.objects.create_user(email="candidate@test.com", password="pw12345x")


@pytest.fixture
def pool(employer_user):
    return TalentPool.objects.create(employer=employer_user.employer_profile, name="Backend Engineers")


def test_candidate_off_by_default_cannot_be_added_to_pool(employer_client, pool, candidate_user):
    """CareerProfile.is_discoverable defaults to False — a candidate who
    never opted in must be rejected by add_candidate."""
    CareerProfile.objects.create(user=candidate_user, is_discoverable=False)
    resp = employer_client.post(
        f"/api/v1/employer/talent-pools/{pool.id}/add_candidate/",
        {"user_id": candidate_user.id}, format="json",
    )
    assert resp.status_code == 403
    assert not TalentPoolCandidate.objects.filter(pool=pool, user=candidate_user).exists()


def test_candidate_on_can_be_added_and_appears_in_pool_detail(employer_client, pool, candidate_user):
    CareerProfile.objects.create(user=candidate_user, is_discoverable=True)
    resp = employer_client.post(
        f"/api/v1/employer/talent-pools/{pool.id}/add_candidate/",
        {"user_id": candidate_user.id}, format="json",
    )
    assert resp.status_code == 201

    detail = employer_client.get(f"/api/v1/employer/talent-pools/{pool.id}/")
    assert detail.status_code == 200
    candidate_ids = [c["user"] for c in detail.json()["data"]["candidates"]]
    assert candidate_user.id in candidate_ids
    assert detail.json()["data"]["candidate_count"] == 1


def test_candidate_withdrawal_stops_future_employer_discovery_in_saved_pool(
    employer_client, pool, candidate_user,
):
    """The real end-to-end privacy proof: add while opted-in, then withdraw,
    then confirm the employer's ALREADY-SAVED pool no longer surfaces them —
    not just that a fresh add_candidate call would be rejected."""
    profile = CareerProfile.objects.create(user=candidate_user, is_discoverable=True)
    add_resp = employer_client.post(
        f"/api/v1/employer/talent-pools/{pool.id}/add_candidate/",
        {"user_id": candidate_user.id}, format="json",
    )
    assert add_resp.status_code == 201

    # Sanity: visible while still opted in.
    detail_before = employer_client.get(f"/api/v1/employer/talent-pools/{pool.id}/")
    assert candidate_user.id in [c["user"] for c in detail_before.json()["data"]["candidates"]]

    # Candidate withdraws consent.
    profile.is_discoverable = False
    profile.save(update_fields=["is_discoverable"])

    # The employer's existing saved pool must no longer show this candidate.
    detail_after = employer_client.get(f"/api/v1/employer/talent-pools/{pool.id}/")
    assert detail_after.status_code == 200
    candidate_ids_after = [c["user"] for c in detail_after.json()["data"]["candidates"]]
    assert candidate_user.id not in candidate_ids_after
    assert detail_after.json()["data"]["candidate_count"] == 0

    # The underlying audit record is retained, not deleted — withdrawal
    # changes visibility, not history.
    assert TalentPoolCandidate.objects.filter(pool=pool, user=candidate_user).exists()
    row = TalentPoolCandidate.objects.get(pool=pool, user=candidate_user)
    assert row.was_discoverable_at_creation is True  # historical snapshot untouched


def test_active_candidates_helper_excludes_withdrawn_candidate(pool, candidate_user):
    """Unit-level proof of the model helper itself, independent of the API."""
    profile = CareerProfile.objects.create(user=candidate_user, is_discoverable=True)
    TalentPoolCandidate.objects.create(pool=pool, user=candidate_user, was_discoverable_at_creation=True)
    assert pool.active_candidates().filter(user=candidate_user).exists()

    profile.is_discoverable = False
    profile.save(update_fields=["is_discoverable"])
    assert not pool.active_candidates().filter(user=candidate_user).exists()
    # Raw membership (audit) is untouched.
    assert pool.candidates.filter(user=candidate_user).exists()


def test_rank_pool_excludes_withdrawn_candidates(employer_client, pool, candidate_user):
    """A withdrawn candidate must not be served up for ranking either."""
    profile = CareerProfile.objects.create(user=candidate_user, is_discoverable=True)
    TalentPoolCandidate.objects.create(pool=pool, user=candidate_user, was_discoverable_at_creation=True)

    profile.is_discoverable = False
    profile.save(update_fields=["is_discoverable"])

    resp = employer_client.post(
        f"/api/v1/employer/talent-pools/{pool.id}/rank/", {"job_id": 1}, format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["candidates_ranked"] == 0
