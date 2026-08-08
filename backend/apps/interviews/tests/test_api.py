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
        """Test creating an interview session."""
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
        # First create a session
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        # Then retrieve it
        url = reverse("interviews:interview-sessions-detail", kwargs={"pk": session_id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_update_interview_session(self, auth_client, user):
        """Test updating an interview session."""
        # First create a session
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        # Then update it
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
        # First create a session
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        # Then delete it
        url = reverse("interviews:interview-sessions-detail", kwargs={"pk": session_id})
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestInterviewQuestionAPI:
    """Tests for Interview Question endpoints."""

    def test_list_questions(self, auth_client, user):
        """Test listing questions in a session."""
        # First create a session
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        # Then list questions
        url = reverse("interviews:interview-questions-list", kwargs={"session_id": session_id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_question(self, auth_client, user):
        """Test creating a question in a session."""
        # First create a session
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        # Then create a question
        url = reverse("interviews:interview-questions-list", kwargs={"session_id": session_id})
        data = {
            "question_index": 1,
            "question_text": "What is a Python decorator?",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_question(self, auth_client, user):
        """Test updating a question."""
        # First create a session and question
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
        })
        session_id = response.data["data"]["id"]

        url = reverse("interviews:interview-questions-list", kwargs={"session_id": session_id})
        response = auth_client.post(url, {
            "question_index": 1,
            "question_text": "What is a Python decorator?",
        })
        question_id = response.data["data"]["id"]

        # Then update the question
        url = reverse("interviews:interview-questions-detail", kwargs={"session_id": session_id, "pk": question_id})
        data = {
            "answer_text": "A decorator is a function that takes another function and extends its behavior.",
            "score": 0.9,
            "feedback": "Good explanation!",
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestInterviewFeedbackAPI:
    """Tests for Interview Feedback endpoints."""

    def test_get_session_feedback(self, auth_client, user):
        """Test retrieving feedback for a session."""
        # First create a completed session
        url = reverse("interviews:interview-sessions-list")
        response = auth_client.post(url, {
            "interview_type": "technical",
            "target_role": "Software Engineer",
            "status": "completed",
            "overall_score": 0.85,
            "feedback_summary": "Good technical knowledge",
        })
        session_id = response.data["data"]["id"]

        # Then get feedback
        url = reverse("interviews:interview-feedback", kwargs={"pk": session_id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "feedback_summary" in response.data["data"]


@pytest.mark.django_db
class TestInterviewPracticeAPI:
    """Tests for Interview Practice endpoints."""

    def test_get_practice_questions(self, auth_client, user):
        """Test getting practice questions."""
        url = reverse("interviews:practice-questions")
        data = {
            "interview_type": "technical",
            "target_role": "Software Engineer",
            "difficulty": "medium",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "questions" in response.data["data"]

    def test_get_coding_question(self, auth_client, user):
        """Test getting a coding question."""
        url = reverse("interviews:coding-question")
        data = {
            "difficulty": "medium",
            "topic": "algorithms",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "question" in response.data["data"] or "problem" in response.data["data"]


@pytest.mark.django_db
class TestInterviewVoiceAPI:
    """Tests for Interview Voice endpoints."""

    def test_start_voice_interview(self, auth_client, user):
        """Test starting a voice interview."""
        url = reverse("interviews:voice-interview-start")
        data = {
            "interview_type": "behavioral",
            "target_role": "Product Manager",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_submit_voice_answer(self, auth_client, user):
        """Test submitting a voice answer."""
        # First start a voice interview
        url = reverse("interviews:voice-interview-start")
        response = auth_client.post(url, {
            "interview_type": "behavioral",
            "target_role": "Product Manager",
        })
        session_id = response.data["data"]["id"]

        # Then submit voice answer
        url = reverse("interviews:voice-interview-answer", kwargs={"pk": session_id})
        data = {
            "question_index": 1,
            "transcript": "I would prioritize features based on user impact.",
            "duration_seconds": 45,
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


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

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "problem" in response.data["data"] or "title" in response.data["data"]

    def test_submit_coding_solution(self, auth_client, user):
        """Test submitting a coding solution."""
        # First get a problem
        url = reverse("interviews:coding-problem")
        response = auth_client.post(url, {
            "difficulty": "medium",
            "language": "python",
        })
        problem_id = response.data["data"].get("id") or response.data["data"].get("problem_id")

        # Then submit solution
        url = reverse("interviews:coding-solution")
        data = {
            "problem_id": problem_id,
            "code": "def two_sum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []",
            "language": "python",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "result" in response.data["data"] or "status" in response.data["data"]