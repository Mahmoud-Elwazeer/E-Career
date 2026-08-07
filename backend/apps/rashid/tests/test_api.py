"""
Rashid API Tests
Tests for Rashid AI chat, conversation, and profile management endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestRashidConfigAPI:
    """Tests for Rashid Configuration endpoints."""

    def test_get_rashid_config(self, api_client):
        """Test retrieving Rashid configuration."""
        url = reverse("rashid:config-detail")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "ai_provider" in response.data["data"]
        assert "system_prompt" in response.data["data"]

    def test_update_rashid_config_admin(self, admin_client):
        """Test updating Rashid configuration as admin."""
        url = reverse("rashid:config-detail")
        data = {
            "temperature": 0.8,
            "max_tokens": 3000,
        }
        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestRashidProfileAPI:
    """Tests for Rashid Profile endpoints."""

    def test_get_rashid_profile(self, auth_client, user):
        """Test retrieving user's Rashid profile."""
        url = reverse("rashid:profile-detail")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_rashid_profile(self, auth_client, user):
        """Test creating a Rashid profile."""
        url = reverse("rashid:profile-detail")
        data = {
            "experience_level": "mid",
            "current_role": "Software Engineer",
            "current_situation": "Looking for new opportunities",
            "target_role": "Senior Developer",
            "skills": ["Python", "Django", "React"],
            "skill_gaps": ["Leadership", "System Design"],
            "constraints": {
                "time": "20 hours/week",
                "location": "Dubai",
                "budget": "5000 EGP",
            },
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_rashid_profile(self, auth_client, user):
        """Test updating Rashid profile."""
        url = reverse("rashid:profile-detail")
        data = {
            "target_role": "Tech Lead",
        }
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestRashidConversationAPI:
    """Tests for Rashid Conversation endpoints."""

    def test_list_conversations(self, auth_client, user):
        """Test listing user's conversations."""
        url = reverse("rashid:conversations-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_conversation(self, auth_client, user):
        """Test creating a new conversation."""
        url = reverse("rashid:conversations-list")
        data = {
            "mode": "career_path",
            "title": "Career Path Discussion",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["mode"] == "career_path"

    def test_retrieve_conversation(self, auth_client, user):
        """Test retrieving a specific conversation."""
        # First create a conversation
        url = reverse("rashid:conversations-list")
        response = auth_client.post(url, {
            "mode": "general",
        })
        conversation_id = response.data["data"]["id"]

        # Then retrieve it
        url = reverse("rashid:conversations-detail", kwargs={"pk": conversation_id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_delete_conversation(self, auth_client, user):
        """Test deleting a conversation."""
        # First create a conversation
        url = reverse("rashid:conversations-list")
        response = auth_client.post(url, {
            "mode": "general",
        })
        conversation_id = response.data["data"]["id"]

        # Then delete it
        url = reverse("rashid:conversations-detail", kwargs={"pk": conversation_id})
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestRashidMessageAPI:
    """Tests for Rashid Message endpoints."""

    def test_list_messages(self, auth_client, user):
        """Test listing messages in a conversation."""
        # First create a conversation
        url = reverse("rashid:conversations-list")
        response = auth_client.post(url, {
            "mode": "general",
        })
        conversation_id = response.data["data"]["id"]

        # Then list messages
        url = reverse("rashid:conversations-messages", kwargs={"pk": conversation_id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_message(self, auth_client, user):
        """Test sending a message to Rashid."""
        # First create a conversation
        url = reverse("rashid:conversations-list")
        response = auth_client.post(url, {
            "mode": "general",
        })
        conversation_id = response.data["data"]["id"]

        # Then send a message
        url = reverse("rashid:conversations-messages", kwargs={"pk": conversation_id})
        data = {
            "role": "user",
            "content": "Hello, I need career advice.",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert "content" in response.data["data"]


@pytest.mark.django_db
class TestRashidStarStoriesAPI:
    """Tests for STAR Stories endpoints."""

    def test_list_star_stories(self, auth_client, user):
        """Test listing user's STAR stories."""
        url = reverse("rashid:star-stories-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_create_star_story(self, auth_client, user):
        """Test creating a STAR story."""
        url = reverse("rashid:star-stories-list")
        data = {
            "situation": "Team was behind schedule",
            "task": "Deliver project on time",
            "action": "Implemented agile practices and daily standups",
            "result": "Project delivered 2 days early",
            "reflection": "Communication is key",
            "tags": ["Leadership", "Project Management"],
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_update_star_story(self, auth_client, user):
        """Test updating a STAR story."""
        # First create a story
        url = reverse("rashid:star-stories-list")
        response = auth_client.post(url, {
            "situation": "Test situation",
            "task": "Test task",
            "action": "Test action",
            "result": "Test result",
        })
        story_id = response.data["data"]["id"]

        # Then update it
        url = reverse("rashid:star-stories-detail", kwargs={"pk": story_id})
        data = {"result": "Updated result"}
        response = auth_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestRashidUsageAPI:
    """Tests for Rashid Usage endpoints."""

    def test_get_user_usage(self, auth_client, user):
        """Test retrieving user's daily usage."""
        url = reverse("rashid:usage-detail")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_get_usage_history(self, auth_client, user):
        """Test retrieving usage history."""
        url = reverse("rashid:usage-history")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True


@pytest.mark.django_db
class TestRashidJobAnalysisAPI:
    """Tests for Rashid Job Analysis endpoints."""

    def test_analyze_job(self, auth_client, user, job):
        """Test analyzing a job with Rashid."""
        url = reverse("rashid:analyze-job", kwargs={"job_slug": job.slug})
        data = {
            "question": "Is this job a good fit for me?",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "analysis" in response.data["data"] or "message" in response.data["data"]