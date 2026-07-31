"""
Tests for the event emitter system.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.events.emitter import emit, emit_sync, _get_client_ip
from apps.events.types import (
    USER_REGISTERED, USER_LOGGED_IN, JOB_VIEWED, JOB_SAVED,
    SEARCH_PERFORMED, CV_UPLOADED, AI_MODEL_CALLED
)

User = get_user_model()


class TestEventEmitter(TestCase):
    """Test event emission functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
    
    @patch('apps.events.tasks.write_event.delay')
    def test_emit_creates_event(self, mock_delay):
        """Test that emit() creates an event via Celery task."""
        emit(
            event_type=USER_REGISTERED,
            category="user",
            user=self.user,
            target_type="user",
            target_id=str(self.user.id),
            data={"email": self.user.email},
        )
        
        # Verify the Celery task was called
        mock_delay.assert_called_once()
        call_args = mock_delay.call_args[1]
        assert call_args['event_type'] == USER_REGISTERED
        assert call_args['category'] == "user"
        assert call_args['user_id'] == self.user.id
    
    @patch('apps.events.models.EventLog.objects.create')
    def test_emit_sync_creates_event(self, mock_create):
        """Test that emit_sync() creates an event directly."""
        emit_sync(
            event_type=USER_LOGGED_IN,
            category="user",
            user=self.user,
            target_type="user",
            target_id=str(self.user.id),
        )
        
        # Verify the event was created
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['event_type'] == USER_LOGGED_IN
        assert call_kwargs['category'] == "user"
        assert call_kwargs['user_id'] == self.user.id
    
    def test_get_client_ip(self):
        """Test IP address extraction from request."""
        # Test with X-Forwarded-For header
        request = MagicMock()
        request.META = {'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1'}
        assert _get_client_ip(request) == '192.168.1.1'
        
        # Test with REMOTE_ADDR
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        assert _get_client_ip(request) == '127.0.0.1'
        
        # Test with no IP
        request.META = {}
        assert _get_client_ip(request) is None


class TestEventTypes(TestCase):
    """Test event type constants."""
    
    def test_user_event_types(self):
        """Test user event type constants."""
        assert USER_REGISTERED == "user_registered"
        assert USER_LOGGED_IN == "user_logged_in"
    
    def test_job_event_types(self):
        """Test job event type constants."""
        assert JOB_VIEWED == "job_viewed"
        assert JOB_SAVED == "job_saved"
    
    def test_search_event_types(self):
        """Test search event type constants."""
        assert SEARCH_PERFORMED == "search_performed"
    
    def test_cv_event_types(self):
        """Test CV event type constants."""
        assert CV_UPLOADED == "cv_uploaded"
    
    def test_ai_event_types(self):
        """Test AI event type constants."""
        assert AI_MODEL_CALLED == "ai_model_called"