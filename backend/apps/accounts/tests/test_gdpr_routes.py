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
