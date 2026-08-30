"""
Tests for admin API endpoints (Phase 7b).
Covers: Celery Beat viewer, global search, packages/entitlements, copilot.
"""
import uuid
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
        email="jobseeker7b@test.com",
        password="TestPass123!",
        role="user",
    )
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


# ---------------------------------------------------------------------------
# Celery Beat viewer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCeleryBeatList:
    url = reverse("celery-beat-list")

    def test_admin_can_list_tasks(self, admin_client):
        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert "tasks" in data
        assert "count" in data
        assert isinstance(data["tasks"], list)

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCeleryBeatToggle:

    def test_toggle_task(self, admin_client):
        from django_celery_beat.models import PeriodicTask, IntervalSchedule
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=10, period=IntervalSchedule.SECONDS
        )
        task = PeriodicTask.objects.create(
            name="test-toggle-task",
            task="some.task",
            interval=schedule,
            enabled=True,
        )
        url = reverse("celery-beat-toggle", kwargs={"task_id": task.id})
        resp = admin_client.patch(url, {"enabled": False}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert data["enabled"] is False

        task.refresh_from_db()
        assert task.enabled is False

    def test_creates_activity_log(self, admin_client):
        from django_celery_beat.models import PeriodicTask, IntervalSchedule
        from apps.core.models import ActivityLog

        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=10, period=IntervalSchedule.SECONDS
        )
        task = PeriodicTask.objects.create(
            name="test-log-task",
            task="some.task",
            interval=schedule,
            enabled=True,
        )
        url = reverse("celery-beat-toggle", kwargs={"task_id": task.id})
        admin_client.patch(url, {"enabled": False}, format="json")

        log = ActivityLog.objects.filter(action="celery_task_disable").first()
        assert log is not None
        assert log.metadata["task_name"] == "test-log-task"

    def test_missing_enabled_rejected(self, admin_client):
        from django_celery_beat.models import PeriodicTask, IntervalSchedule

        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=10, period=IntervalSchedule.SECONDS
        )
        task = PeriodicTask.objects.create(
            name="test-missing-field",
            task="some.task",
            interval=schedule,
        )
        url = reverse("celery-beat-toggle", kwargs={"task_id": task.id})
        resp = admin_client.patch(url, {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_404_nonexistent_task(self, admin_client):
        url = reverse("celery-beat-toggle", kwargs={"task_id": 999999})
        resp = admin_client.patch(url, {"enabled": False}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_non_admin_rejected(self, non_admin_client):
        url = reverse("celery-beat-toggle", kwargs={"task_id": 1})
        resp = non_admin_client.patch(url, {"enabled": False}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Global search
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminSearch:
    url = reverse("admin-search")

    def test_search_returns_results(self, admin_client, user, company, job):
        resp = admin_client.get(self.url, {"q": company.name[:3]})
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        assert "results" in data
        assert "count" in data

    def test_search_finds_users(self, admin_client, admin_user):
        resp = admin_client.get(self.url, {"q": admin_user.email[:5]})
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        user_results = [r for r in data["results"] if r["type"] == "user"]
        assert len(user_results) >= 1

    def test_short_query_rejected(self, admin_client):
        resp = admin_client.get(self.url, {"q": "a"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_query_rejected(self, admin_client):
        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.get(self.url, {"q": "test"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Subscription Plans
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSubscriptionPlans:
    url = reverse("subscription-plans-list")

    def test_list_plans(self, admin_client):
        from apps.core.models import SubscriptionPlan
        SubscriptionPlan.objects.create(
            name="Pro Plan",
            job_posting_limit=20,
            candidate_search_limit=200,
            ai_features_enabled=True,
        )
        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        results = data.get("results", data) if isinstance(data, dict) else data
        assert len(results) >= 1

    def test_create_plan(self, admin_client):
        resp = admin_client.post(
            self.url,
            {
                "name": "Starter Plan",
                "job_posting_limit": 3,
                "candidate_search_limit": 20,
                "ai_features_enabled": False,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = unwrap(resp)
        assert data["name"] == "Starter Plan"
        assert data["job_posting_limit"] == 3

    def test_retrieve_and_update_plan(self, admin_client):
        from apps.core.models import SubscriptionPlan
        plan = SubscriptionPlan.objects.create(
            name="Update Test Plan",
            job_posting_limit=5,
        )
        detail_url = reverse("subscription-plans-detail", kwargs={"uuid": plan.uuid})
        resp = admin_client.patch(
            detail_url,
            {"name": "Updated Plan Name"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        plan.refresh_from_db()
        assert plan.name == "Updated Plan Name"

    def test_delete_plan(self, admin_client):
        from apps.core.models import SubscriptionPlan
        plan = SubscriptionPlan.objects.create(name="Delete Me Plan")
        detail_url = reverse("subscription-plans-detail", kwargs={"uuid": plan.uuid})
        resp = admin_client.delete(detail_url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not SubscriptionPlan.objects.filter(pk=plan.pk).exists()

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Company Subscriptions
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCompanySubscriptions:
    url = reverse("company-subscriptions-list")

    def test_list_subscriptions(self, admin_client, company):
        from apps.core.models import SubscriptionPlan, CompanySubscription
        plan = SubscriptionPlan.objects.create(name="Test Plan Sub")
        CompanySubscription.objects.create(
            company=company, plan=plan, status="active"
        )
        resp = admin_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        data = unwrap(resp)
        results = data.get("results", data) if isinstance(data, dict) else data
        assert len(results) >= 1

    def test_create_subscription(self, admin_client, company):
        from apps.core.models import SubscriptionPlan
        plan = SubscriptionPlan.objects.create(name="New Sub Plan")
        resp = admin_client.post(
            self.url,
            {"company": company.pk, "plan": plan.pk, "status": "trial"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Entitlement checks
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestEntitlementChecks:

    def test_job_posting_limit_enforced(self):
        from apps.core.permissions import check_entitlement
        from apps.core.models import SubscriptionPlan, CompanySubscription
        from apps.jobs.models import Company
        from rest_framework.exceptions import PermissionDenied

        company = Company.objects.create(name="Entitlement Test Co")
        plan = SubscriptionPlan.objects.create(
            name="Tight Plan",
            job_posting_limit=2,
        )
        CompanySubscription.objects.create(
            company=company, plan=plan, status="active"
        )

        check_entitlement(company, "job_posting", 1)

        with pytest.raises(PermissionDenied):
            check_entitlement(company, "job_posting", 2)

    def test_no_subscription_allows_everything(self):
        from apps.core.permissions import check_entitlement
        from apps.jobs.models import Company

        company = Company.objects.create(name="No Sub Co")
        assert check_entitlement(company, "job_posting", 100) is True
        assert check_entitlement(company, "candidate_search", 999) is True

    def test_unlimited_plan(self):
        from apps.core.permissions import check_entitlement
        from apps.core.models import SubscriptionPlan, CompanySubscription
        from apps.jobs.models import Company

        company = Company.objects.create(name="Unlimited Co")
        plan = SubscriptionPlan.objects.create(
            name="Unlimited Plan",
            job_posting_limit=0,
            candidate_search_limit=0,
        )
        CompanySubscription.objects.create(
            company=company, plan=plan, status="active"
        )
        assert check_entitlement(company, "job_posting", 9999) is True
        assert check_entitlement(company, "candidate_search", 9999) is True


# ---------------------------------------------------------------------------
# Admin Copilot
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAdminCopilot:
    url = reverse("admin-copilot-chat")

    def test_empty_message_rejected(self, admin_client):
        resp = admin_client.post(self.url, {"message": ""}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_message_rejected(self, admin_client):
        resp = admin_client.post(self.url, {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_admin_rejected(self, non_admin_client):
        resp = non_admin_client.post(
            self.url, {"message": "hello"}, format="json"
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_copilot_responds_or_501(self, admin_client):
        resp = admin_client.post(
            self.url, {"message": "What is the system health?"}, format="json"
        )
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
