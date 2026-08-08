"""
Integration Tests
End-to-end tests for key user workflows across multiple apps.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserJourney:
    """End-to-end user journey tests."""

    def test_complete_user_registration_and_login(self, api_client):
        """Test complete user registration and login flow."""
        # Register
        url = reverse("accounts:register")
        data = {
            "email": "journeyuser@example.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Journey",
            "last_name": "User",
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        # Login
        url = reverse("accounts:login")
        data = {
            "email": "journeyuser@example.com",
            "password": "TestPass123!",
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["data"]

    def test_user_creates_profile_and_searches_jobs(self, api_client, user):
        """Test user creating profile and searching jobs."""
        client = APIClient()
        # Login
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": user.email,
            "password": "TestPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Create career profile
        url = reverse("career:profile-detail")
        data = {
            "target_roles": [{"role": "Senior Developer", "priority": 1}],
            "target_locations": [{"city": "Dubai", "country": "UAE", "priority": 1}],
            "open_to_remote": True,
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        # Search jobs
        url = reverse("jobs:job-list")
        response = client.get(url, {"q": "developer", "location": "Dubai"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_user_applies_to_job_and_saves(self, api_client, user, job):
        """Test user applying to and saving a job."""
        client = APIClient()
        # Login
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": user.email,
            "password": "TestPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Save job
        url = reverse("jobs:job-save", kwargs={"slug": job.slug})
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["is_saved"] is True

        # Apply to job
        url = reverse("jobs:job-apply", kwargs={"slug": job.slug})
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert "source_url" in response.data["data"]


@pytest.mark.django_db
class TestRashidJourney:
    """End-to-end Rashid AI journey tests."""

    def test_user_onboards_and_asks_career_questions(self, api_client, user):
        """Test user onboarding with Rashid and asking career questions."""
        client = APIClient()
        # Login
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": user.email,
            "password": "TestPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Create Rashid profile
        url = reverse("rashid:profile-detail")
        data = {
            "experience_level": "mid",
            "current_role": "Software Engineer",
            "target_role": "Tech Lead",
            "skills": ["Python", "Django"],
            "skill_gaps": ["Leadership"],
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        # Create conversation
        url = reverse("rashid:conversations-list")
        data = {"mode": "career_path"}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        conversation_id = response.data["data"]["id"]

        # Send message
        url = reverse("rashid:conversations-messages", kwargs={"pk": conversation_id})
        data = {
            "role": "user",
            "content": "How can I become a Tech Lead?",
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "content" in response.data["data"]


@pytest.mark.django_db
class TestInterviewJourney:
    """End-to-end interview practice journey tests."""

    def test_user_practices_interview_and_gets_feedback(self, api_client, user):
        """Test user practicing interview and getting feedback."""
        client = APIClient()
        # Login
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": user.email,
            "password": "TestPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Create interview session
        url = reverse("career:interview-sessions-list")
        data = {
            "interview_type": "technical",
            "target_role": "Software Engineer",
            "mode": "text",
            "difficulty": "mid",
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        session_id = response.data["data"]["id"]

        # Complete interview
        url = reverse("career:interview-sessions-detail", kwargs={"pk": session_id})
        data = {
            "status": "completed",
            "overall_score": 0.85,
            "feedback_summary": "Good technical knowledge",
        }
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestJobWorkflow:
    """End-to-end job workflow tests."""

    def test_admin_creates_job_and_user_applies(self, api_client, admin_user, company, source):
        """Test admin creating a job and user applying to it."""
        client = APIClient()
        # Login as admin
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": admin_user.email,
            "password": "AdminPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Create job
        url = reverse("jobs:job-list")
        data = {
            "title": "Senior Developer",
            "slug": "senior-developer",
            "company": company.id,
            "source": source.id,
            "location": "Dubai",
            "location_type": "onsite",
            "industry": "technology",
            "experience_level": "senior",
            "description": "Senior developer needed for growth company.",
            "source_url": "https://example.com/job",
            "status": "active",
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        # Logout and login as regular user
        client = APIClient()
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": "testuser@gmail.com",
            "password": "TestPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Apply to job
        url = reverse("jobs:job-apply", kwargs={"slug": "senior-developer"})
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestSkillGapAnalysis:
    """End-to-end skill gap analysis tests."""

    def test_user_updates_skills_and_gets_analysis(self, api_client, user):
        """Test user updating skills and getting analysis."""
        client = APIClient()
        # Login
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": user.email,
            "password": "TestPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Add skills
        url = reverse("career:skills-list")
        data = {
            "skill_name": "Python",
            "proficiency": "advanced",
            "years_experience": 3,
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        # Get profile completeness
        url = reverse("career:profile-completeness")
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestCareerGoalWorkflow:
    """End-to-end career goal workflow tests."""

    def test_user_sets_goals_and_tracks_progress(self, api_client, user):
        """Test user setting goals and tracking progress."""
        client = APIClient()
        # Login
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": user.email,
            "password": "TestPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Create goal
        url = reverse("career:goals-list")
        data = {
            "title": "Become Senior Developer",
            "description": "Achieve senior level in 2 years",
            "goal_type": "role",
            "target_role": "Senior Developer",
            "priority": "high",
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        goal_id = response.data["data"]["id"]

        # Add milestone
        url = reverse("career:goals-add-milestone", kwargs={"pk": goal_id})
        data = {"title": "Complete Python Course"}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_200_OK

        # Update progress
        url = reverse("career:goals-detail", kwargs={"pk": goal_id})
        data = {"progress": 50}
        response = client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestJobSearchWorkflow:
    """End-to-end job search workflow tests."""

    def test_user_searches_filters_and_saves_jobs(self, api_client, user, job, company, tag):
        """Test user searching, filtering, and saving jobs."""
        client = APIClient()
        # Login
        url = reverse("accounts:login")
        response = client.post(url, {
            "email": user.email,
            "password": "TestPass123!",
        })
        token = response.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Search jobs
        url = reverse("jobs:job-list")
        response = client.get(url, {
            "q": "developer",
            "industry": "technology",
            "location": "Dubai",
        })
        assert response.status_code == status.HTTP_200_OK

        # Save job
        url = reverse("jobs:job-save", kwargs={"slug": job.slug})
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["is_saved"] is True

        # Get saved jobs
        url = reverse("jobs:job-saved-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK