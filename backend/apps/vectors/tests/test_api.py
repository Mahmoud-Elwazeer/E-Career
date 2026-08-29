"""
Tests for Vector Search API Endpoints
"""

import pytest
from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.vectors.plugins.vector_plugin import VectorSearchResponse, VectorSearchResult


@pytest.mark.django_db
class TestSemanticSearchAPI(TestCase):
    """Test semantic search API endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    @patch('apps.vectors.views.get_vector_service')
    def test_semantic_search_success(self, mock_get_service):
        """Test successful semantic search."""
        # Mock vector service
        mock_service = Mock()
        mock_service.semantic_search.return_value = VectorSearchResponse(
            results=[
                VectorSearchResult(
                    id="job-1",
                    score=0.95,
                    payload={
                        "job_id": "job-1",
                        "title": "Python Developer",
                        "company": "TechCorp",
                        "location": "Remote",
                        "salary_min": 80000,
                        "salary_max": 120000,
                    }
                ),
            ],
            total=1,
            query_time_ms=123,
        )
        mock_get_service.return_value = mock_service

        # Make request
        url = reverse('vectors:semantic_search')
        response = self.client.get(url, {"q": "Python developer remote"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["jobs"]) == 1
        assert data["data"]["jobs"][0]["title"] == "Python Developer"
        assert data["data"]["search_type"] == "semantic"

    def test_semantic_search_missing_query(self):
        """Test semantic search without query parameter."""
        url = reverse('vectors:semantic_search')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "q" in data["errors"]

    @patch('apps.vectors.views.get_vector_service')
    def test_semantic_search_with_filters(self, mock_get_service):
        """Test semantic search with filters."""
        mock_service = Mock()
        mock_service.semantic_search.return_value = VectorSearchResponse(
            results=[],
            total=0,
            query_time_ms=45,
        )
        mock_get_service.return_value = mock_service

        # Make request with filters
        url = reverse('vectors:semantic_search')
        response = self.client.get(url, {
            "q": "developer",
            "location": "Cairo",
            "experience_level": "senior",
            "salary_min": 50000,
        })

        assert response.status_code == status.HTTP_200_OK

        # Verify filters were passed correctly
        call_args = mock_service.semantic_search.call_args
        assert call_args[1]["filters"]["location"] == "Cairo"
        assert call_args[1]["filters"]["experience_level"] == "senior"
        assert call_args[1]["filters"]["salary_min"]["gte"] == 50000


@pytest.mark.django_db
class TestSimilarJobsAPI(TestCase):
    """Test similar jobs API endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    @patch('apps.vectors.views.get_vector_service')
    def test_similar_jobs_success(self, mock_get_service):
        """Test finding similar jobs."""
        # Mock vector service
        mock_service = Mock()
        mock_service.similar_items.return_value = VectorSearchResponse(
            results=[
                VectorSearchResult(
                    id="job-2",
                    score=0.92,
                    payload={
                        "job_id": "job-2",
                        "title": "Django Developer",
                        "company": "StartupX",
                        "location": "Cairo",
                    }
                ),
                VectorSearchResult(
                    id="job-3",
                    score=0.85,
                    payload={
                        "job_id": "job-3",
                        "title": "Backend Engineer",
                        "company": "MegaCorp",
                        "location": "Dubai",
                    }
                ),
            ],
            total=2,
            query_time_ms=67,
        )
        mock_get_service.return_value = mock_service

        # Make request
        job_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID
        url = reverse('vectors:similar_jobs', kwargs={'job_id': job_id})
        response = self.client.get(url, {"limit": 5})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["similar_jobs"]) == 2
        assert data["data"]["similar_jobs"][0]["title"] == "Django Developer"


@pytest.mark.django_db
class TestHybridSearchAPI(TestCase):
    """Test hybrid search API endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    @patch('apps.vectors.views.get_vector_service')
    @patch('apps.vectors.views.search_service')
    def test_hybrid_search_success(self, mock_search_service, mock_get_vector_service):
        """Test hybrid search combining keyword and semantic."""
        # Mock keyword search
        mock_search_service.search_jobs.return_value = {
            "hits": [
                {"id": "job-1", "title": "Python Developer", "score": 10.5},
                {"id": "job-2", "title": "Django Developer", "score": 8.2},
            ],
        }

        # Mock semantic search
        mock_vector_service = Mock()
        mock_vector_service.semantic_search.return_value = VectorSearchResponse(
            results=[
                VectorSearchResult(
                    id="job-2",
                    score=0.92,
                    payload={"job_id": "job-2", "title": "Django Developer"}
                ),
                VectorSearchResult(
                    id="job-3",
                    score=0.85,
                    payload={"job_id": "job-3", "title": "Backend Engineer"}
                ),
            ],
            total=2,
            query_time_ms=89,
        )
        mock_get_vector_service.return_value = mock_vector_service

        # Make request
        url = reverse('vectors:hybrid_search')
        response = self.client.get(url, {
            "q": "Python developer",
            "keyword_weight": 0.5,
            "semantic_weight": 0.5,
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["search_type"] == "hybrid"
        assert "jobs" in data["data"]

        # Verify both searches were called
        mock_search_service.search_jobs.assert_called_once()
        mock_vector_service.semantic_search.assert_called_once()


@pytest.mark.django_db
class TestVectorHealthAPI(TestCase):
    """Test vector health check API endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    @patch('apps.vectors.views.get_vector_service')
    def test_health_check_success(self, mock_get_service):
        """Test health check endpoint."""
        # Mock health check
        mock_service = Mock()
        mock_service.health_check.return_value = {
            "vector": {"healthy": True, "collections": 3},
            "embedding": {"healthy": True, "provider": "bedrock_cohere"},
            "collections": {
                "jobs": True,
                "users": True,
                "skills": True,
            },
        }
        mock_get_service.return_value = mock_service

        # Make request
        url = reverse('vectors:health')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["vector"]["healthy"] is True
        assert data["data"]["embedding"]["healthy"] is True
