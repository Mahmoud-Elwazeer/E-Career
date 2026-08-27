"""
Vector Service

Centralized service for vector operations (embedding generation + vector search).
Handles plugin selection, fallback, and collection management.
"""

import structlog
from typing import List, Optional
from django.conf import settings

from .plugins.vector_plugin import VectorPlugin, VectorSearchQuery, VectorSearchResponse
from .plugins.embedding_plugin import EmbeddingPlugin, EmbeddingRequest, EmbeddingResponse
from .plugins.pgvector_plugin import PgVectorPlugin
from .plugins.cohere_embed_plugin import CohereEmbedPlugin

logger = structlog.get_logger(__name__)

# Collection names
JOBS_COLLECTION = "jobs"
USERS_COLLECTION = "users"
SKILLS_COLLECTION = "skills"

# Vector dimensions
EMBED_DIMENSIONS = 1024  # Cohere Embed v3


class VectorService:
    """Centralized vector service with automatic fallback."""

    def __init__(self):
        self._vector_plugin: Optional[VectorPlugin] = None
        self._embedding_plugin: Optional[EmbeddingPlugin] = None

    @property
    def vector_plugin(self) -> VectorPlugin:
        """Get vector plugin — pgvector is the canonical store."""
        if self._vector_plugin is None:
            self._vector_plugin = PgVectorPlugin()
            logger.info("vector_plugin_selected", plugin="pgvector")
        return self._vector_plugin

    @property
    def embedding_plugin(self) -> EmbeddingPlugin:
        """Get embedding plugin."""
        if self._embedding_plugin is None:
            self._embedding_plugin = CohereEmbedPlugin()
            logger.info("embedding_plugin_selected", plugin="cohere")

        return self._embedding_plugin

    def ensure_collections(self) -> bool:
        """Ensure all required collections exist."""
        collections = [
            (JOBS_COLLECTION, EMBED_DIMENSIONS),
            (USERS_COLLECTION, EMBED_DIMENSIONS),
            (SKILLS_COLLECTION, EMBED_DIMENSIONS),
        ]

        for collection, dimensions in collections:
            if not self.vector_plugin.collection_exists(collection):
                success = self.vector_plugin.create_collection(
                    name=collection,
                    vector_size=dimensions,
                    distance="cosine",
                )
                if not success:
                    logger.error("collection_create_failed", collection=collection)
                    return False

        logger.info("collections_ensured", count=len(collections))
        return True

    def generate_embeddings(
        self,
        texts: List[str],
        input_type: str = "search_document",
    ) -> List[List[float]]:
        """Generate embeddings for texts."""
        request = EmbeddingRequest(
            texts=texts,
            model="cohere-embed-v3",
            input_type=input_type,
        )

        response = self.embedding_plugin.generate(request)
        return response.embeddings

    def semantic_search(
        self,
        collection: str,
        query_text: str,
        limit: int = 20,
        score_threshold: Optional[float] = None,
        filters: Optional[dict] = None,
    ) -> VectorSearchResponse:
        """
        Semantic search using text query.

        Args:
            collection: Collection to search
            query_text: Natural language query
            limit: Max results
            score_threshold: Minimum similarity score
            filters: Payload filters

        Returns:
            Search response with results
        """
        # Generate query embedding
        query_embeddings = self.generate_embeddings(
            texts=[query_text],
            input_type="search_query",
        )

        if not query_embeddings:
            logger.error("query_embedding_failed", query=query_text)
            return VectorSearchResponse(results=[], total=0, query_time_ms=0)

        # Search
        search_query = VectorSearchQuery(
            vector=query_embeddings[0],
            limit=limit,
            score_threshold=score_threshold,
            filter=filters,
        )

        return self.vector_plugin.search(collection, search_query)

    def similar_items(
        self,
        collection: str,
        item_id: str,
        limit: int = 20,
        score_threshold: Optional[float] = None,
        filters: Optional[dict] = None,
    ) -> VectorSearchResponse:
        """
        Find similar items by ID.

        Args:
            collection: Collection to search
            item_id: ID of reference item
            limit: Max results
            score_threshold: Minimum similarity score
            filters: Payload filters

        Returns:
            Search response with results
        """
        # Get item vector
        item = self.vector_plugin.get(collection, item_id)

        if not item:
            logger.error("item_not_found", collection=collection, id=item_id)
            return VectorSearchResponse(results=[], total=0, query_time_ms=0)

        # Search
        search_query = VectorSearchQuery(
            vector=item.vector,
            limit=limit + 1,  # +1 because the item itself will be in results
            score_threshold=score_threshold,
            filter=filters,
        )

        response = self.vector_plugin.search(collection, search_query)

        # Remove the item itself from results
        response.results = [r for r in response.results if r.id != item_id][:limit]
        response.total = len(response.results)

        return response

    def health_check(self) -> dict:
        """Check health of vector and embedding services."""
        vector_health = self.vector_plugin.health_check()
        embedding_health = self.embedding_plugin.health_check()

        return {
            "vector": vector_health,
            "embedding": embedding_health,
            "collections": {
                JOBS_COLLECTION: self.vector_plugin.collection_exists(JOBS_COLLECTION),
                USERS_COLLECTION: self.vector_plugin.collection_exists(USERS_COLLECTION),
                SKILLS_COLLECTION: self.vector_plugin.collection_exists(SKILLS_COLLECTION),
            },
        }


# Singleton instance
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get singleton VectorService instance."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
