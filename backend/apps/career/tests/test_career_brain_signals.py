"""
Tests for CareerBrain signal wiring (Item 1.1).

Verifies that post_save signals on CareerProfile, CareerUserSkill,
and CareerLearning trigger the sync_career_brain Celery task.
"""
from unittest.mock import patch, MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.career.models import CareerProfile, CareerBrain

User = get_user_model()


@pytest.mark.django_db
class TestCareerBrainSignals(TestCase):
    """Test that model saves trigger CareerBrain sync."""

    @patch("apps.career.tasks.sync_career_brain")
    def test_career_profile_save_triggers_sync(self, mock_task):
        mock_task.delay = MagicMock()
        user = User.objects.create_user(
            email="signaltest@example.com",
            password="testpass123",
        )
        CareerProfile.objects.create(user=user, current_role="Developer")
        mock_task.delay.assert_called_with(user.id)

    @patch("apps.career.tasks.sync_career_brain")
    def test_career_user_skill_save_triggers_sync(self, mock_task):
        from apps.career.models import CareerUserSkill
        from apps.skills.models import Skill

        mock_task.delay = MagicMock()
        user = User.objects.create_user(
            email="signaltest2@example.com",
            password="testpass123",
        )
        CareerProfile.objects.create(user=user, current_role="Dev")
        mock_task.delay.reset_mock()

        skill = Skill.objects.create(name="Python")
        CareerUserSkill.objects.create(
            user=user,
            skill=skill,
            proficiency="intermediate",
        )
        mock_task.delay.assert_called_with(user.id)


@pytest.mark.django_db
class TestSyncCareerBrainTask(TestCase):
    """Test the sync_career_brain Celery task directly."""

    @patch("apps.career.tasks.sync_career_brain.delay")
    def setUp(self, mock_delay):
        """Create user/profile with signal mocked to avoid eager execution."""
        self.user = User.objects.create_user(
            email="tasktest@example.com",
            password="testpass123",
        )
        self.profile = CareerProfile.objects.create(
            user=self.user,
            current_role="Engineer",
            experience_years=5,
        )

    def test_sync_creates_career_brain(self):
        from apps.career.tasks import sync_career_brain

        result = sync_career_brain(self.user.id)
        assert result["success"] is True
        assert CareerBrain.objects.filter(user=self.user).exists()

    def test_sync_updates_existing_brain(self):
        from apps.career.tasks import sync_career_brain

        CareerBrain.objects.create(user=self.user)
        result = sync_career_brain(self.user.id)
        assert result["success"] is True
        assert CareerBrain.objects.filter(user=self.user).count() == 1

    def test_sync_skips_missing_profile(self):
        from apps.career.tasks import sync_career_brain

        user2 = User.objects.create_user(
            email="noprofile@example.com",
            password="testpass123",
        )
        result = sync_career_brain(user2.id)
        assert result.get("skipped") is True

    def test_sync_returns_skipped_for_missing_user(self):
        from apps.career.tasks import sync_career_brain

        result = sync_career_brain(99999)
        assert result.get("skipped") is True
