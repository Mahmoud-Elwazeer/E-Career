"""
Career API Tests
Tests for career profile, skills, goals, and interview session endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django.conf import settings


@pytest.mark.django_db
class TestCareerProfileAPI:
    """Tests for Career Profile endpoints."""

    def test_get_career_profile(self, auth_client, user):
        """Test retrieving user's career profile."""
        url = reverse("career:profile-detail")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_career_profile(self, auth_client, user):
        """Test creating a career profile."""
        url = reverse("career:profile-detail")
        data = {
            "target_roles": [{"role": "Senior Developer", "priority": 1}],
            "target_locations": [{"city": "Dubai", "country": "UAE", "priority": 1}],
            "target_salary_min": 100000,
            "target_salary_currency": "USD",
            "open_to_remote": True,
            "experience_years": 5,
            "current_role": "Software Engineer",
            "current_company": "Tech Corp",
            "alert_frequency": "daily",
            "min_match_score": 0.7,
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_career_profile(self, auth_client, user):
        """Test updating career profile."""
        url = reverse("career:profile-detail")
        data = {
            "target_roles": [{"role": "Tech Lead", "priority": 1}],
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_update_completeness(self, auth_client, user):
        """Test updating profile completeness."""
        url = reverse("career:profile-completeness")
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestUserSkillAPI:
    """Tests for User Skill endpoints."""

    def test_list_user_skills(self, auth_client, user):
        """Test listing user's skills."""
        url = reverse("career:skills-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_user_skill(self, auth_client, user):
        """Test creating a user skill."""
        url = reverse("career:skills-list")
        data = {
            "skill_name": "Python",
            "proficiency": "advanced",
            "years_experience": 3,
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_user_skill(self, auth_client, user):
        """Test updating a user skill."""
        url = reverse("career:skills-list")
        data = {
            "skill_name": "Python",
            "proficiency": "expert",
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_delete_user_skill(self, auth_client, user):
        """Test deleting a user skill."""
        url = reverse("career:skills-list")
        data = {"skill_name": "Python"}
        response = auth_client.delete(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestLearningAPI:
    """Tests for Learning History endpoints."""

    def test_list_learning(self, auth_client, user):
        """Test listing user's learning history."""
        url = reverse("career:learning-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_learning(self, auth_client, user):
        """Test creating a learning entry."""
        url = reverse("career:learning-list")
        data = {
            "title": "Python Advanced",
            "platform": "Coursera",
            "skills_gained": [{"skill_name": "Python", "level_delta": 0.2}],
            "completed_at": "2024-01-15",
            "certificate_url": "https://example.com/cert",
            "course_id": "CS101",
            "duration_hours": 40,
            "difficulty_level": "advanced",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_learning(self, auth_client, user):
        """Test updating a learning entry."""
        url = reverse("career:learning-list")
        data = {
            "title": "Python Advanced Updated",
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestTalentScoreAPI:
    """Tests for Talent Score endpoints."""

    def test_get_talent_score(self, auth_client, user):
        """Test retrieving user's talent score."""
        url = reverse("career:talent-score-detail")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_get_dimension_breakdown(self, auth_client, user):
        """Test getting talent score breakdown."""
        url = reverse("career:talent-score-breakdown")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestInterviewSessionAPI:
    """Tests for Interview Session endpoints."""

    def test_list_interview_sessions(self, auth_client, user):
        """Test listing user's interview sessions."""
        url = reverse("career:interview-sessions-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_interview_session(self, auth_client, user):
        """Test creating an interview session."""
        url = reverse("career:interview-sessions-list")
        data = {
            "interview_type": "technical",
            "target_role": "Software Engineer",
            "target_company": "Tech Corp",
            "mode": "text",
            "difficulty": "mid",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_retrieve_interview_session(self, auth_client, user):
        """Test retrieving a specific interview session."""
        # First create a session
        url = reverse("career:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        # Then retrieve it
        url = reverse("career:interview-sessions-detail", kwargs={"pk": session_id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_update_interview_session(self, auth_client, user):
        """Test updating an interview session."""
        # First create a session
        url = reverse("career:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        # Then update it
        url = reverse("career:interview-sessions-detail", kwargs={"pk": session_id})
        data = {
            "status": "completed",
            "overall_score": 0.85,
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestCareerGoalAPI:
    """Tests for Career Goal endpoints."""

    def test_list_career_goals(self, auth_client, user):
        """Test listing user's career goals."""
        url = reverse("career:goals-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_career_goal(self, auth_client, user):
        """Test creating a career goal."""
        url = reverse("career:goals-list")
        data = {
            "title": "Become Senior Developer",
            "description": "Achieve senior level in 2 years",
            "goal_type": "role",
            "target_role": "Senior Developer",
            "priority": "high",
            "status": "active",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_career_goal(self, auth_client, user):
        """Test updating a career goal."""
        # First create a goal
        url = reverse("career:goals-list")
        response = auth_client.post(url, {
            "title": "Test Goal",
            "goal_type": "role",
        })
        goal_id = response.data["data"]["id"]

        # Then update it
        url = reverse("career:goals-detail", kwargs={"pk": goal_id})
        data = {"progress": 50}
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_add_milestone(self, auth_client, user):
        """Test adding a milestone to a goal."""
        # First create a goal
        url = reverse("career:goals-list")
        response = auth_client.post(url, {
            "title": "Test Goal",
            "goal_type": "role",
        })
        goal_id = response.data["data"]["id"]

        # Then add milestone
        url = reverse("career:goals-add-milestone", kwargs={"pk": goal_id})
        data = {"title": "Complete Python Course"}
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_complete_milestone(self, auth_client, user):
        """Test completing a milestone."""
        # First create a goal with milestone
        url = reverse("career:goals-list")
        response = auth_client.post(url, {
            "title": "Test Goal",
            "goal_type": "role",
            "milestones": [{"id": "m1", "title": "Test Milestone", "completed": False}],
        })
        goal_id = response.data["data"]["id"]

        # Then complete milestone
        url = reverse("career:goals-complete-milestone", kwargs={"pk": goal_id})
        data = {"milestone_id": "m1"}
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestCareerBrainAPI:
    """Tests for Career Brain endpoints."""

    def test_get_career_brain(self, auth_client, user):
        """Test retrieving user's career brain."""
        url = reverse("career:career-brain-detail")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_update_career_brain(self, auth_client, user):
        """Test updating career brain context."""
        url = reverse("career:career-brain-detail")
        data = {
            "identity": {
                "professional_title": "Senior Developer",
                "career_stage": "mid",
                "self_perception": "Experienced engineer",
            },
            "skills": {
                "Python": {"level": "expert", "verified": True, "years": 5},
                "Django": {"level": "advanced", "verified": True, "years": 4},
            },
            "goals": [
                {"goal": "Become Tech Lead", "priority": "high", "timeline": "2 years", "status": "active"},
            ],
            "preferences": {
                "work_style": "Remote",
                "target_locations": ["Dubai", "Remote"],
                "salary_min": 100000,
            },
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True