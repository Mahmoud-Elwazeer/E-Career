"""
Tests for admin API endpoints (Phase 7c).
Covers: GDPR export/delete actions, per-company cost breakdown.
"""
from unittest.mock import patch, MagicMock

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


def unwrap(response):
    """Unwrap the standard response envelope {"success": ..., "data": ...}."""
    payload = response.json()
    if isinstance(payload, dict) and "data" in payload and "success" in payload:
        return payload["data"]
    return payload


@pytest.fixture
def non_admin_client(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        email="jobseeker7c@test.com",
        password="TestPass123!",
        role="user",
    )
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def target_user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email="targetuser@test.com",
        password="TestPass123!",
        role="user",
    )


# ---------------------------------------------------------------------------
# GDPR Export Action
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGDPRExportAction:
    url = reverse("gdpr-export-action")

    def test_non_admin_denied(self, non_admin_client, target_user):
        resp = non_admin_client.post(self.url, {"user_id": target_user.id})
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_missing_user_id(self, admin_client):
        resp = admin_client.post(self.url, {})
        data = unwrap(resp)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_found(self, admin_client):
        resp = admin_client.post(self.url, {"user_id": 99999})
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_preview_without_confirm(self, admin_client, target_user):
        resp = admin_client.post(self.url, {"user_id": target_user.id})
        data = unwrap(resp)
        assert resp.status_code == status.HTTP_200_OK
        assert data["requires_confirm"] is True
        assert data["email"] == "targetuser@test.com"

    def test_export_with_confirm(self, admin_client, target_user):
        resp = admin_client.post(
            self.url, {"user_id": target_user.id, "confirm": True}
        )
        data = unwrap(resp)
        assert resp.status_code == status.HTTP_200_OK
        assert data["status"] == "completed"
        assert data["email"] == "targetuser@test.com"
        assert "export_request_id" in data

        from apps.accounts.models_gdpr import DataExportRequest
        req = DataExportRequest.objects.get(user=target_user)
        assert req.status == "completed"

        from apps.core.models import ActivityLog
        log = ActivityLog.objects.filter(action="gdpr_export").first()
        assert log is not None
        assert log.metadata["target_user_id"] == target_user.id


# ---------------------------------------------------------------------------
# GDPR Delete Action
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGDPRDeleteAction:
    url = reverse("gdpr-delete-action")

    def test_non_admin_denied(self, non_admin_client, target_user):
        resp = non_admin_client.post(self.url, {"user_id": target_user.id})
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_missing_user_id(self, admin_client):
        resp = admin_client.post(self.url, {})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_preview_without_confirm(self, admin_client, target_user):
        resp = admin_client.post(self.url, {"user_id": target_user.id})
        data = unwrap(resp)
        assert resp.status_code == status.HTTP_200_OK
        assert data["requires_confirm"] is True
        assert "cannot be undone" in data["message"]

    def test_delete_with_confirm(self, admin_client, target_user):
        resp = admin_client.post(
            self.url, {"user_id": target_user.id, "confirm": True}
        )
        data = unwrap(resp)
        assert resp.status_code == status.HTTP_200_OK
        assert data["status"] == "completed"

        from apps.accounts.models_gdpr import AccountDeletionRequest
        req = AccountDeletionRequest.objects.get(user=target_user)
        assert req.status == "completed"

        from apps.core.models import ActivityLog
        log = ActivityLog.objects.filter(action="gdpr_delete").first()
        assert log is not None

    def test_double_delete_rejected(self, admin_client, target_user):
        self.url
        admin_client.post(
            self.url, {"user_id": target_user.id, "confirm": True}
        )
        resp2 = admin_client.post(
            self.url, {"user_id": target_user.id, "confirm": True}
        )
        assert resp2.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# Per-company AI cost breakdown
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAICostCompanyBreakdown:
    url = reverse("ai-costs-api")

    def test_response_includes_company_costs(self, admin_client):
        resp = admin_client.get(self.url)
        data = unwrap(resp)
        assert resp.status_code == status.HTTP_200_OK
        assert "company_costs" in data
        assert isinstance(data["company_costs"], list)
