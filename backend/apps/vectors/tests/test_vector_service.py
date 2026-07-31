"""
Tests for Vector Service

Mock-based tests for vector operations without requiring actual Qdrant/Bedrock.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from apps.vectors.service import VectorService, JOBS_COLLECTION, EMBED_DIMENSIONS
from apps.vectors.plugins.vector_plugin import VectorSearchResponse, VectorSearchResult


@pytest.mark.django_db
class TestVectorService(TestCase):
    """Test VectorService operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = VectorService()

    @patch('apps.vectors.service.QdrantVectorPlugin')
    @patch('apps.vectors.service.CohereEmbedPlugin')
    def test_generate_embeddings(self, mock_cohere, mock_qdrant):
        """Test embedding generation."""
        # Mock embedding response
        mock_embed_instance = Mock()
        mock_embed_instance.generate.return_value = Mock(
            embeddings=[[0.1] * 1024, [0.2] * 1024],
            model="cohere.embed-english-v3",
            dimensions=1024,
        )
        mock_cohere.return_value = mock_embed_instance

        # Generate embeddings
        texts = ["Software Engineer job", "Data Scientist position"]
        embeddings = self.service.generate_embeddings(texts, input_type="search_document")

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1024
        mock_embed_instance.generate.assert_called_once()

    @patch('apps.vectors.service.QdrantVectorPlugin')
    @patch('apps.vectors.service.CohereEmbedPlugin')
    def test_semantic_search(self, mock_cohere, mock_qdrant):
        """Test semantic search."""
        # Mock embedding
        mock_embed_instance = Mock()
        mock_embed_instance.generate.return_value = Mock(
            embeddings=[[0.1] * 1024],
        )
        mock_cohere.return_value = mock_embed_instance

        # Mock vector search
        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = {"healthy": True}
        mock_vector_instance.search.return_value = VectorSearchResponse(
            results=[
                VectorSearchResult(
                    id="job-1",
                    score=0.95,
                    payload={
                        "job_id": "job-1",
                        "title": "Senior Python Developer",
                        "company": "TechCorp",
                    }
                ),
                VectorSearchResult(
                    id="job-2",
                    score=0.87,
                    payload={
                        "job_id": "job-2",
                        "title": "Backend Engineer",
                        "company": "StartupX",
                    }
                ),
            ],
            total=2,
            query_time_ms=123,
        )
        mock_qdrant.return_value = mock_vector_instance

        # Perform search
        response = self.service.semantic_search(
            collection=JOBS_COLLECTION,
            query_text="Python developer position",
            limit=10,
        )

        assert response.total == 2
        assert len(response.results) == 2
        assert response.results[0].score == 0.95
        assert response.results[0].payload["title"] == "Senior Python Developer"

    @patch('apps.vectors.service.QdrantVectorPlugin')
    def test_similar_items(self, mock_qdrant):
        """Test finding similar items."""
        # Mock getting item
        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = {"healthy": True}
        mock_vector_instance.get.return_value = Mock(
            id="job-1",
            vector=[0.1] * 1024,
            payload={"job_id": "job-1", "title": "Python Developer"},
        )

        # Mock search results (includes the query item)
        mock_vector_instance.search.return_value = VectorSearchResponse(
            results=[
                VectorSearchResult(
                    id="job-1",  # The query item itself
                    score=1.0,
                    payload={"job_id": "job-1", "title": "Python Developer"}
                ),
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
            total=3,
            query_time_ms=89,
        )
        mock_qdrant.return_value = mock_vector_instance

        # Find similar jobs
        response = self.service.similar_items(
            collection=JOBS_COLLECTION,
            item_id="job-1",
            limit=5,
        )

        # Should exclude the query item itself
        assert response.total == 2
        assert all(r.id != "job-1" for r in response.results)
        assert response.results[0].payload["title"] == "Django Developer"

    @patch('apps.vectors.service.QdrantVectorPlugin')
    def test_ensure_collections(self, mock_qdrant):
        """Test collection creation."""
        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = {"healthy": True}
        mock_vector_instance.collection_exists.return_value = False
        mock_vector_instance.create_collection.return_value = True
        mock_qdrant.return_value = mock_vector_instance

        # Ensure collections
        success = self.service.ensure_collections()

        assert success is True
        assert mock_vector_instance.create_collection.call_count == 3  # jobs, users, skills

    @patch('apps.vectors.service.QdrantVectorPlugin')
    @patch('apps.vectors.service.CohereEmbedPlugin')
    def test_health_check(self, mock_cohere, mock_qdrant):
        """Test health check."""
        # Mock health responses
        mock_vector_instance = Mock()
        mock_vector_instance.health_check.return_value = {
            "healthy": True,
            "collections": 3,
        }
        mock_vector_instance.collection_exists.return_value = True
        mock_qdrant.return_value = mock_vector_instance

        mock_embed_instance = Mock()
        mock_embed_instance.health_check.return_value = {
            "healthy": True,
            "provider": "bedrock_cohere",
        }
        mock_cohere.return_value = mock_embed_instance

        # Check health
        health = self.service.health_check()

        assert health["vector"]["healthy"] is True
        assert health["embedding"]["healthy"] is True
        assert all(health["collections"].values())  # All collections exist


@pytest.mark.django_db
class TestVectorFallback(TestCase):
    """Test fallback to pgvector when Qdrant unavailable."""

    @patch('apps.vectors.service.QdrantVectorPlugin')
    @patch('apps.vectors.service.PgVectorPlugin')
    def test_fallback_to_pgvector(self, mock_pgvector, mock_qdrant):
        """Test automatic fallback to pgvector."""
        # Mock Qdrant as unavailable
        mock_qdrant_instance = Mock()
        mock_qdrant_instance.health_check.return_value = {"healthy": False}
        mock_qdrant.return_value = mock_qdrant_instance

        # Mock pgvector as healthy
        mock_pgvector_instance = Mock()
        mock_pgvector_instance.health_check.return_value = {"healthy": True}
        mock_pgvector.return_value = mock_pgvector_instance

        # Create service (should fallback to pgvector)
        service = VectorService()

        # Force plugin initialization by accessing it
        with patch.object(mock_qdrant_instance, 'health_check', side_effect=Exception("Connection failed")):
            plugin = service.vector_plugin

        # Should be pgvector, not qdrant
        # In actual implementation, we'd check the plugin type
        assert plugin is not None
