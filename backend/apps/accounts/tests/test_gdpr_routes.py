"""
Verifies the Privacy Center's self-service GDPR endpoints (data export +
account deletion) are actually reachable. These views already existed in
apps.accounts.views_gdpr but were never wired into a URLconf — this test
guards against that regression now that they're mounted in accounts/urls.py.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models_gdpr import DataExportRequest, AccountDeletionRequest

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def auth_client():
    user = User.objects.create_user(email="gdpr-user@test.com", password="pw12345x")
    c = APIClient()
    c.force_authenticate(user=user)
    return c, user


def test_data_export_request_creates_record(auth_client):
    client, user = auth_client
    resp = client.post("/api/v1/auth/data-export/")
    assert resp.status_code == 202
    assert DataExportRequest.objects.filter(user=user).exists()


def test_data_export_status_lookup(auth_client):
    client, user = auth_client
    create_resp = client.post("/api/v1/auth/data-export/")
    req_id = create_resp.json()["data"]["request_id"]  # str(export_request.id) — the int pk
    resp = client.get(f"/api/v1/auth/data-export/{req_id}/")
    assert resp.status_code == 200


def test_account_deletion_request_schedules_grace_period(auth_client):
    client, user = auth_client
    resp = client.delete("/api/v1/auth/account/deletion-request/")
    assert resp.status_code == 202
    assert AccountDeletionRequest.objects.filter(user=user, status="pending").exists()


def test_account_deletion_status_and_cancel(auth_client):
    client, user = auth_client
    client.delete("/api/v1/auth/account/deletion-request/")

    status_resp = client.get("/api/v1/auth/account/deletion-status/")
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["pending"] is True

    cancel_resp = client.post("/api/v1/auth/account/cancel-deletion/")
    assert cancel_resp.status_code == 200
    assert AccountDeletionRequest.objects.get(user=user).status == "cancelled"


# ── Scheduled execution of due deletions (directive items 8 + 9) ────────────

def test_execute_due_account_deletions_dispatches_due_requests(monkeypatch):
    """The scheduler must find a PAST-due AccountDeletionRequest and
    dispatch the real deletion task — this did not exist before (the
    scheduled_for date was set but nothing ever checked it)."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.accounts.tasks_gdpr import execute_due_account_deletions

    user = User.objects.create_user(email="due-deletion@test.com", password="pw12345x")
    due = AccountDeletionRequest.objects.create(
        user=user, scheduled_for=timezone.now() - timedelta(days=1),
    )
    not_due = AccountDeletionRequest.objects.create(
        user=User.objects.create_user(email="not-due@test.com", password="pw12345x"),
        scheduled_for=timezone.now() + timedelta(days=10),
    )

    dispatched_ids = []

    class _FakeDelay:
        @staticmethod
        def delay(request_id):
            dispatched_ids.append(request_id)

    monkeypatch.setattr("apps.accounts.tasks_gdpr.process_account_deletion", _FakeDelay)

    result = execute_due_account_deletions()
    assert result["dispatched"] == 1
    assert str(due.id) in dispatched_ids
    assert str(not_due.id) not in dispatched_ids


def test_execute_due_account_deletions_skips_users_under_legal_hold(monkeypatch):
    """Directive item 9: a user under an active LegalHold must NEVER be
    swept into deletion, no exceptions."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.accounts.tasks_gdpr import execute_due_account_deletions
    from apps.legal.models import LegalHold

    held_user = User.objects.create_user(email="held-for-deletion@test.com", password="pw12345x")
    LegalHold.objects.create(
        reference="HOLD-DEL-001", scope_description="litigation", reason="active claim",
        user=held_user,
    )
    due = AccountDeletionRequest.objects.create(
        user=held_user, scheduled_for=timezone.now() - timedelta(days=1),
    )

    dispatched_ids = []

    class _FakeDelay:
        @staticmethod
        def delay(request_id):
            dispatched_ids.append(request_id)

    monkeypatch.setattr("apps.accounts.tasks_gdpr.process_account_deletion", _FakeDelay)

    result = execute_due_account_deletions()
    assert result["dispatched"] == 0
    assert result["skipped_held"] == 1
    assert dispatched_ids == []
    due.refresh_from_db()
    assert due.status == "pending"  # untouched, still pending — not silently failed


def test_process_account_deletion_defense_in_depth_blocks_held_user():
    """Even if a request somehow reaches the executor task directly
    (bypassing the scheduler's own hold check), the executor itself must
    independently refuse to delete a held user's data."""
    from apps.accounts.tasks_gdpr import process_account_deletion
    from apps.legal.models import LegalHold

    from django.utils import timezone

    held_user = User.objects.create_user(email="held-executor@test.com", password="pw12345x")
    deletion_request = AccountDeletionRequest.objects.create(
        user=held_user, scheduled_for=timezone.now(),
    )
    LegalHold.objects.create(
        reference="HOLD-DEL-002", scope_description="litigation", reason="active claim",
        user=held_user,
    )

    process_account_deletion(str(deletion_request.id))

    deletion_request.refresh_from_db()
    held_user.refresh_from_db()
    assert deletion_request.status == "pending"  # never flipped to processing/completed
    assert held_user.email == "held-executor@test.com"  # never anonymized
    assert held_user.is_active is True
