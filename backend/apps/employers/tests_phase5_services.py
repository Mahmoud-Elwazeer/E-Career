"""Tests for Phase 5 employer services: QuickApplyService and ConnectionsService."""
import json
import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model

from apps.employers.quick_apply_service import QuickApplyService
from apps.employers.connections_service import ConnectionsService

User = get_user_model()


# ============================================================================
# QuickApplyService Tests
# ============================================================================

@pytest.mark.django_db
class TestQuickApplyPrepare:
    def test_prepare_returns_mapped_fields(self, user, job):
        from apps.career.models import CareerProfile
        CareerProfile.objects.create(
            user=user,
            skills=["Python", "Django"],
            current_company="Acme Inc",
            current_role="Backend Dev",
            experience_years=5,
            portfolio_url="https://example.com/portfolio",
        )
        svc = QuickApplyService()
        result = svc.prepare_application(user, job)

        assert "mapped_fields" in result
        fields = result["mapped_fields"]
        assert fields["first_name"] == "Test"
        assert fields["last_name"] == "User"
        assert fields["email"] == user.email
        assert fields["current_company"] == "Acme Inc"
        assert fields["current_title"] == "Backend Dev"
        assert fields["experience_years"] == 5
        assert "Python" in fields["skills"]
        assert result["already_applied"] is False

    def test_prepare_without_profile(self, user, job):
        svc = QuickApplyService()
        result = svc.prepare_application(user, job)
        fields = result["mapped_fields"]
        assert fields["email"] == user.email
        assert fields["current_company"] == ""
        assert fields["skills"] == []

    def test_ats_provider_info_greenhouse(self, job):
        job.ats_platform = "greenhouse"
        job.save()
        svc = QuickApplyService()
        info = svc.get_ats_provider_info(job)
        assert info is not None
        assert info["platform"] == "greenhouse"
        assert info["can_auto_submit"] is False

    def test_ats_provider_info_unknown(self, job):
        job.ats_platform = ""
        job.save()
        svc = QuickApplyService()
        info = svc.get_ats_provider_info(job)
        assert info is None


@pytest.mark.django_db
class TestQuickApplyRecord:
    def test_record_creates_application(self, user, job):
        svc = QuickApplyService()
        result = svc.record_application(user, job)
        assert result["created"] is True
        assert result["status"] == "applied"

        from apps.employers.models import JobApplication
        assert JobApplication.objects.filter(user=user, job=job).count() == 1

    def test_record_no_duplicate_on_repeat(self, user, job):
        svc = QuickApplyService()
        result1 = svc.record_application(user, job)
        result2 = svc.record_application(user, job)
        assert result1["created"] is True
        assert result2["created"] is False
        assert result1["application_id"] == result2["application_id"]

        from apps.employers.models import JobApplication
        assert JobApplication.objects.filter(user=user, job=job).count() == 1


# ============================================================================
# ConnectionsService Tests
# ============================================================================

@pytest.mark.django_db
class TestInsiderConnections:
    def test_discoverable_user_returned(self, user, company):
        from apps.career.models import CareerProfile
        other = User.objects.create_user(
            email="insider@test.com",
            password="Pass1234!",
            first_name="Insider",
            last_name="User",
        )
        CareerProfile.objects.create(
            user=other,
            current_company="Test Corp",
            current_role="Engineer",
            is_discoverable=True,
        )
        svc = ConnectionsService()
        result = svc.find_connections(company.id, requesting_user=user)
        names = [c["name"] for c in result["ecareer_connections"]]
        assert "Insider User" in names

    def test_non_discoverable_user_excluded(self, user, company):
        from apps.career.models import CareerProfile
        hidden = User.objects.create_user(
            email="hidden@test.com",
            password="Pass1234!",
            first_name="Hidden",
            last_name="User",
        )
        CareerProfile.objects.create(
            user=hidden,
            current_company="Test Corp",
            current_role="Secret Agent",
            is_discoverable=False,
        )
        svc = ConnectionsService()
        result = svc.find_connections(company.id, requesting_user=user)
        names = [c["name"] for c in result["ecareer_connections"]]
        assert "Hidden User" not in names

    def test_requesting_user_excluded_from_results(self, user, company):
        from apps.career.models import CareerProfile
        CareerProfile.objects.create(
            user=user,
            current_company="Test Corp",
            current_role="Dev",
            is_discoverable=True,
        )
        svc = ConnectionsService()
        result = svc.find_connections(company.id, requesting_user=user)
        user_ids = [c["user_id"] for c in result["ecareer_connections"]]
        assert user.id not in user_ids

    @patch("urllib.request.urlopen")
    def test_github_contributors_returned(self, mock_urlopen, user, company):
        company.github_org = "test-org"
        company.save()

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"login": "dev1", "html_url": "https://github.com/dev1", "avatar_url": "https://avatars.githubusercontent.com/dev1"},
            {"login": "dev2", "html_url": "https://github.com/dev2", "avatar_url": "https://avatars.githubusercontent.com/dev2"},
        ]).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        svc = ConnectionsService()
        result = svc.find_connections(company.id, requesting_user=user)
        assert len(result["github_contributors"]) == 2
        assert result["github_contributors"][0]["username"] == "dev1"

    @patch("urllib.request.urlopen")
    def test_github_api_failure_returns_empty(self, mock_urlopen, user, company):
        company.github_org = "test-org"
        company.save()
        mock_urlopen.side_effect = Exception("API rate limited")

        svc = ConnectionsService()
        result = svc.find_connections(company.id, requesting_user=user)
        assert result["github_contributors"] == []

    def test_no_github_org_returns_empty(self, user, company):
        svc = ConnectionsService()
        result = svc.find_connections(company.id, requesting_user=user)
        assert result["github_contributors"] == []
