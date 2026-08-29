"""
Interviews API Tests
Tests for interview session, question, and coding service endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestInterviewSessionAPI:
    """Tests for Interview Session endpoints."""

    def test_list_interview_sessions(self, auth_client, user):
        """Test listing user's interview sessions."""
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_interview_session(self, auth_client, user):
        """Test creating an interview session via ModelViewSet.create."""
        url = reverse("interviews:interview-sessions-list")
        data = {
            "interview_type": "technical",
            "target_role": "Software Engineer",
            "difficulty": "medium",
            "mode": "text",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["interview_type"] == "technical"

    def test_retrieve_interview_session(self, auth_client, user):
        """Test retrieving a specific interview session."""
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        url = reverse("interviews:interview-sessions-detail", kwargs={"pk": session_id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_update_interview_session(self, auth_client, user):
        """Test updating an interview session."""
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        url = reverse("interviews:interview-sessions-detail", kwargs={"pk": session_id})
        data = {
            "status": "completed",
            "overall_score": 0.85,
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_delete_interview_session(self, auth_client, user):
        """Test deleting an interview session."""
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        url = reverse("interviews:interview-sessions-detail", kwargs={"pk": session_id})
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestStartInterviewAPI:
    """Tests for the interview start action."""

    def test_start_interview(self, auth_client, user):
        """Test starting an interview via the start action."""
        url = reverse("interviews:interview-sessions-start")
        data = {
            "interview_type": "technical",
            "target_role": "Software Engineer",
            "difficulty": "medium",
            "mode": "text",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["interview_type"] == "technical"
        assert response.data["data"]["question_count"] == 5
        assert "current_question" in response.data["data"]


@pytest.mark.django_db
class TestInterviewFeedbackAPI:
    """Tests for Interview Feedback endpoints."""

    def test_get_session_feedback(self, auth_client, user):
        """Test retrieving session detail (used as feedback view)."""
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
            "status": "completed",
            "overall_score": 0.85,
            "feedback_summary": "Good technical knowledge",
        })
        session_id = response.data["data"]["id"]

        url = reverse("interviews:interview-sessions-detail", kwargs={"pk": session_id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestInterviewStatsAPI:
    """Tests for interview stats endpoint."""

    def test_get_interview_stats(self, auth_client, user):
        """Test getting interview statistics."""
        url = reverse("interviews:interview-stats")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "total_sessions" in response.data["data"]


@pytest.mark.django_db
class TestInterviewCodingAPI:
    """Tests for Interview Coding endpoints."""

    def test_get_coding_problem(self, auth_client, user):
        """Test getting a coding problem."""
        url = reverse("interviews:coding-problem")
        data = {
            "difficulty": "medium",
            "language": "python",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert "problem" in response.data["data"] or "title" in response.data["data"]

    def test_submit_coding_solution(self, auth_client, user):
        """Test submitting a coding solution."""
        url = reverse("interviews:coding-problem")
        response = auth_client.post(url, {
            "difficulty": "medium",
            "language": "python",
        })
        problem_id = response.data["data"].get("id") or response.data["data"].get("problem_id")

        url = reverse("interviews:coding-solution")
        data = {
            "problem_id": problem_id,
            "code": "def two_sum(nums, target):\n    return [0, 1]",
            "language": "python",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "result" in response.data["data"] or "status" in response.data["data"]

    def test_evaluate_coding_solution(self, auth_client, user):
        """Test evaluating a coding solution."""
        url = reverse("interviews:coding-evaluate")
        data = {
            "code": "def two_sum(nums, target):\n    return [0, 1]",
            "problem": {"title": "Two Sum", "description": "Given an array..."},
            "language": "python",
            "execution_result": {"status": "success"},
        }
        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestInterviewHistoryAPI:
    """Tests for interview history endpoint."""

    def test_get_history(self, auth_client, user):
        """Test getting interview history."""
        url = reverse("interviews:interview-sessions-history")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
