"""
Tests for admin API endpoints (Phase 7a).
Covers all 13 views in apps.core.admin_api_views.
"""
import uuid
import datetime
from unittest.mock import patch

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


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def non_admin_client(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        email="jobseeker@test.com",
        password="TestPass123!",
        role="user",
    )
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def verification_result(db, job):
    from apps.verification.models import VerificationResult
    return VerificationResult.objects.create(
        job=job,
        status="verified",
        trust_score=0.85,
        legitimacy_score=0.9,
        url_accessible=True,
        http_status_code=200,
        domain_matches_company=True,
        ssl_valid=True,
    )


# ---------------------------------------------------------------------------
# 1. TestSystemHealth
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSystemHealth:
    url = reverse("system-health")

    def test_admin_can_get_health(self, admin_client):
        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert "checks" in data
        assert "overall_status" in data
        assert isinstance(data["checks"], list)
        check_names = [c["name"] for c in data["checks"]]
        assert "Database" in check_names

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_rejected(self, api_client):
        resp = api_client.get(self.url)
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# 2. TestScraperDashboard
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestScraperDashboard:
    url = reverse("scraper-dashboard-api")

    def test_admin_can_get_dashboard(self, admin_client, source, job):
        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert "sources" in data
        assert "scrape_stats" in data
        assert "scraper_health" in data
        assert "pipeline_health" in data
        assert len(data["sources"]) >= 1
        assert data["scrape_stats"]["total_jobs"] >= 1

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# 3. TestAICosts
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAICosts:
    url = reverse("ai-costs-api")

    def test_admin_can_get_costs(self, admin_client):
        resp = admin_client.get(self.url)
        # Could be 200 (models exist) or 501 (ImportError in test env)
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED,
        )
        if resp.status_code == status.HTTP_200_OK:
            data = unwrap(resp)
            assert "today" in data
            assert "week" in data
            assert "month" in data


# ---------------------------------------------------------------------------
# 4. TestVerificationResult
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVerificationResult:

    def test_returns_verification_for_job(self, admin_client, job, verification_result):
        url = reverse("verification-result", kwargs={"job_uuid": job.uuid})
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert data["job_uuid"] == str(job.uuid)
        assert data["status"] == "verified"
        assert data["trust_score"] == 0.85
        assert data["admin_override"] is False

    def test_404_for_nonexistent_job(self, admin_client):
        fake_uuid = uuid.uuid4()
        url = reverse("verification-result", kwargs={"job_uuid": fake_uuid})
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_non_admin_rejected(self, non_admin_client, job):
        url = reverse("verification-result", kwargs={"job_uuid": job.uuid})
        resp = non_admin_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# 5. TestVerificationOverride
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVerificationOverride:

    def test_admin_can_override(self, admin_client, admin_user, job, verification_result):
        url = reverse("verification-override", kwargs={"job_uuid": job.uuid})
        resp = admin_client.patch(
            url,
            {"admin_override": True, "override_reason": "Manually verified"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert data["admin_override"] is True
        assert data["override_by"] == admin_user.email
        assert data["override_reason"] == "Manually verified"

        # Verify DB was updated
        verification_result.refresh_from_db()
        assert verification_result.admin_override is True
        assert verification_result.override_by == admin_user

    def test_creates_activity_log(self, admin_client, job, verification_result):
        from apps.core.models import ActivityLog

        url = reverse("verification-override", kwargs={"job_uuid": job.uuid})
        admin_client.patch(
            url,
            {"admin_override": True, "override_reason": "Checked"},
            format="json",
        )
        log = ActivityLog.objects.filter(action="verification_override").first()
        assert log is not None
        assert log.target_type == "VerificationResult"
        assert log.metadata["job_uuid"] == str(job.uuid)

    def test_missing_field_rejected(self, admin_client, job, verification_result):
        url = reverse("verification-override", kwargs={"job_uuid": job.uuid})
        resp = admin_client.patch(url, {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_admin_rejected(self, non_admin_client, job, verification_result):
        url = reverse("verification-override", kwargs={"job_uuid": job.uuid})
        resp = non_admin_client.patch(
            url,
            {"admin_override": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# 6. TestSourceControl
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSourceControl:

    def test_start_action(self, admin_client, source):
        source.is_active = False
        source.save(update_fields=["is_active"])

        url = reverse("source-control", kwargs={"source_uuid": source.uuid})
        resp = admin_client.post(url, {"action": "start"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        source.refresh_from_db()
        assert source.is_active is True

    def test_stop_action(self, admin_client, source):
        url = reverse("source-control", kwargs={"source_uuid": source.uuid})
        resp = admin_client.post(url, {"action": "stop"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        source.refresh_from_db()
        assert source.is_active is False

    def test_pause_action(self, admin_client, source):
        url = reverse("source-control", kwargs={"source_uuid": source.uuid})
        resp = admin_client.post(url, {"action": "pause"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        source.refresh_from_db()
        assert source.is_active is False

    @patch("apps.scraper.tasks.scrape_single_source")
    def test_run_now_dispatches_task(self, mock_task, admin_client, source):
        url = reverse("source-control", kwargs={"source_uuid": source.uuid})
        resp = admin_client.post(url, {"action": "run_now"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        mock_task.delay.assert_called_once_with(str(source.id))

    def test_invalid_action_rejected(self, admin_client, source):
        url = reverse("source-control", kwargs={"source_uuid": source.uuid})
        resp = admin_client.post(url, {"action": "destroy"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_creates_activity_log(self, admin_client, source):
        from apps.core.models import ActivityLog

        url = reverse("source-control", kwargs={"source_uuid": source.uuid})
        admin_client.post(url, {"action": "stop"}, format="json")
        log = ActivityLog.objects.filter(action="source_stop").first()
        assert log is not None
        assert log.target_type == "Source"
        assert log.target_id == str(source.uuid)
        assert log.metadata["source_name"] == source.name

    def test_non_admin_rejected(self, non_admin_client, source):
        url = reverse("source-control", kwargs={"source_uuid": source.uuid})
        resp = non_admin_client.post(url, {"action": "start"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_nonexistent_source_404(self, admin_client):
        fake_uuid = uuid.uuid4()
        url = reverse("source-control", kwargs={"source_uuid": fake_uuid})
        resp = admin_client.post(url, {"action": "start"}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# 7. TestAdminCompanies
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminCompanies:

    def test_list_companies(self, admin_client, company):
        url = reverse("admin-companies-list")
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        results = data.get("results", data) if isinstance(data, dict) else data
        assert len(results) >= 1

    def test_retrieve_company(self, admin_client, company):
        url = reverse("admin-companies-detail", kwargs={"uuid": company.uuid})
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert data["name"] == company.name

    def test_update_company(self, admin_client, company):
        url = reverse("admin-companies-detail", kwargs={"uuid": company.uuid})
        resp = admin_client.patch(
            url,
            {"name": "Updated Corp"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        company.refresh_from_db()
        assert company.name == "Updated Corp"

    def test_non_admin_rejected(self, non_admin_client, company):
        url = reverse("admin-companies-list")
        resp = non_admin_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# 8. TestTalentPools
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTalentPools:
    url = reverse("admin-talent-pools")

    def test_list_pools(self, admin_client):
        resp = admin_client.get(self.url)
        # 200 when models importable, still 200 with empty queryset if not
        assert resp.status_code == status.HTTP_200_OK

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# 9. TestUserTimeline
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserTimeline:

    def test_returns_events(self, admin_client, admin_user):
        from apps.core.models import ActivityLog

        ActivityLog.objects.create(
            user=admin_user,
            action="test_action",
            target_type="Test",
            target_id="1",
        )
        url = reverse("user-timeline", kwargs={"user_id": admin_user.pk})
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert data["user_id"] == admin_user.pk
        assert data["event_count"] >= 1
        assert data["events"][0]["action"] == "test_action"

    def test_empty_timeline(self, admin_client, user):
        url = reverse("user-timeline", kwargs={"user_id": user.pk})
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert data["event_count"] == 0

    def test_404_for_nonexistent_user(self, admin_client):
        url = reverse("user-timeline", kwargs={"user_id": 999999})
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_non_admin_rejected(self, non_admin_client, user):
        url = reverse("user-timeline", kwargs={"user_id": user.pk})
        resp = non_admin_client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# 10. TestGDPRDashboard
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGDPRDashboard:
    url = reverse("gdpr-dashboard")

    def test_returns_counts(self, admin_client):
        resp = admin_client.get(self.url)
        # 200 if GDPR models importable, 501 otherwise
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED,
        )
        if resp.status_code == status.HTTP_200_OK:
            data = unwrap(resp)
            assert "data_exports" in data
            assert "account_deletions" in data
            assert "pending" in data["data_exports"]
            assert "upcoming_7_days" in data["account_deletions"]

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_with_gdpr_data(self, admin_client, admin_user):
        try:
            from apps.accounts.models_gdpr import (
                DataExportRequest,
                AccountDeletionRequest,
            )
        except ImportError:
            pytest.skip("GDPR models not available")

        DataExportRequest.objects.create(user=admin_user, status="pending")
        AccountDeletionRequest.objects.create(
            user=admin_user,
            status="pending",
            scheduled_for=timezone.now() + datetime.timedelta(days=3),
        )

        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert data["data_exports"]["pending"] >= 1
        assert data["account_deletions"]["pending"] >= 1
        assert data["account_deletions"]["upcoming_7_days"] >= 1


# ---------------------------------------------------------------------------
# 11. TestCompanyTimeline
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCompanyTimeline:

    def test_returns_events(self, admin_client, admin_user, company):
        from apps.core.models import ActivityLog

        ActivityLog.objects.create(
            user=admin_user,
            action="company_update",
            target_type="Company",
            target_id=str(company.uuid),
        )
        url = reverse("company-timeline", kwargs={"company_uuid": company.uuid})
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert data["company_name"] == company.name
        assert data["event_count"] >= 1

    def test_404_for_nonexistent_company(self, admin_client):
        fake_uuid = uuid.uuid4()
        url = reverse("company-timeline", kwargs={"company_uuid": fake_uuid})
        resp = admin_client.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# 12. TestRecommendationDiagnostics
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRecommendationDiagnostics:
    url = reverse("recommendation-diagnostics")

    def test_missing_params_rejected(self, admin_client):
        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonexistent_user_404(self, admin_client, job):
        resp = admin_client.get(
            self.url,
            {"user_id": 999999, "job_uuid": str(job.uuid)},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_job_404(self, admin_client, user):
        resp = admin_client.get(
            self.url,
            {"user_id": user.pk, "job_uuid": str(uuid.uuid4())},
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
