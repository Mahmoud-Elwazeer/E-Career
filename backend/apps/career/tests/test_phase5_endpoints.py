"""Tests for Phase 5 career endpoints (match-breakdown, tailor)."""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestMatchBreakdownEndpoint:
    def test_match_breakdown_returns_data(self, auth_client, user, job):
        from apps.career.models import CareerProfile
        CareerProfile.objects.get_or_create(
            user=user,
            defaults={"skills": ["Python", "Django"]},
        )
        url = reverse("career:match-breakdown", kwargs={"job_id": job.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get("data", response.data)
        assert "overall_score" in data
        assert "breakdown" in data

    def test_match_breakdown_unauthenticated(self, api_client, job):
        url = reverse("career:match-breakdown", kwargs={"job_id": job.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_match_breakdown_nonexistent_job(self, auth_client, user):
        from apps.career.models import CareerProfile
        CareerProfile.objects.get_or_create(user=user)
        url = reverse("career:match-breakdown", kwargs={"job_id": 99999})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTailorEndpoint:
    def test_tailor_returns_scores(self, auth_client, user, job):
        from apps.career.models import CareerProfile
        CareerProfile.objects.get_or_create(
            user=user,
            defaults={
                "skills": ["Python", "Django"],
                "cv_parsed_data": {"text": "Experienced Python developer with Django skills."},
            },
        )
        url = reverse("career:job-tailor", kwargs={"job_id": job.id})
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get("data", response.data)
        assert "original_score" in data
        assert "tailored_score" in data
        assert "suggestions" in data

    def test_tailor_unauthenticated(self, api_client, job):
        url = reverse("career:job-tailor", kwargs={"job_id": job.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
