"""
Qdrant Vector Plugin

Implementation of VectorPlugin for Qdrant vector database.
"""

import time
import structlog
from typing import List, Optional
from django.conf import settings

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)

from .vector_plugin import (
    VectorPlugin,
    VectorDocument,
    VectorSearchQuery,
    VectorSearchResult,
    VectorSearchResponse,
)

logger = structlog.get_logger(__name__)


class QdrantVectorPlugin(VectorPlugin):
    """Qdrant implementation of VectorPlugin."""

    def __init__(self):
        self.host = getattr(settings, "QDRANT_HOST", "localhost")
        self.port = getattr(settings, "QDRANT_PORT", 6333)
        self.api_key = getattr(settings, "QDRANT_API_KEY", None)

        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
            timeout=30,
        )

    def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: str = "cosine",
    ) -> bool:
        """Create a Qdrant collection."""
        try:
            distance_map = {
                "cosine": Distance.COSINE,
                "euclidean": Distance.EUCLID,
                "dot": Distance.DOT,
            }

            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE),
                ),
            )

            logger.info("qdrant_collection_created", collection=name, vector_size=vector_size)
            return True

        except Exception as e:
            logger.error("qdrant_create_collection_failed", collection=name, error=str(e))
            return False

    def delete_collection(self, name: str) -> bool:
        """Delete a Qdrant collection."""
        try:
            self.client.delete_collection(collection_name=name)
            logger.info("qdrant_collection_deleted", collection=name)
            return True
        except Exception as e:
            logger.error("qdrant_delete_collection_failed", collection=name, error=str(e))
            return False

    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.get_collections().collections
            return any(c.name == name for c in collections)
        except Exception as e:
            logger.error("qdrant_collection_exists_failed", collection=name, error=str(e))
            return False

    def upsert(
        self,
        collection: str,
        documents: List[VectorDocument],
    ) -> int:
        """Upsert documents into Qdrant."""
        try:
            points = [
                PointStruct(
                    id=doc.id,
                    vector=doc.vector,
                    payload=doc.payload,
                )
                for doc in documents
            ]

            self.client.upsert(
                collection_name=collection,
                points=points,
            )

            logger.info("qdrant_upsert_success", collection=collection, count=len(documents))
            return len(documents)

        except Exception as e:
            logger.error("qdrant_upsert_failed", collection=collection, error=str(e))
            return 0

    def delete(
        self,
        collection: str,
        ids: List[str],
    ) -> int:
        """Delete documents from Qdrant."""
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=ids,
            )

            logger.info("qdrant_delete_success", collection=collection, count=len(ids))
            return len(ids)

        except Exception as e:
            logger.error("qdrant_delete_failed", collection=collection, error=str(e))
            return 0

    def search(
        self,
        collection: str,
        query: VectorSearchQuery,
    ) -> VectorSearchResponse:
        """Search for similar vectors in Qdrant."""
        start_time = time.time()

        try:
            # Build filter
            query_filter = None
            if query.filter:
                conditions = []
                for key, value in query.filter.items():
                    if isinstance(value, (int, float, str, bool)):
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                    elif isinstance(value, dict):
                        # Range filter: {"gte": 1000, "lte": 5000}
                        if "gte" in value or "lte" in value:
                            conditions.append(
                                FieldCondition(
                                    key=key,
                                    range=Range(
                                        gte=value.get("gte"),
                                        lte=value.get("lte"),
                                    ),
                                )
                            )

                if conditions:
                    query_filter = Filter(must=conditions)

            # Search
            search_result = self.client.search(
                collection_name=collection,
                query_vector=query.vector,
                limit=query.limit,
                score_threshold=query.score_threshold,
                query_filter=query_filter,
            )

            # Convert to response
            results = [
                VectorSearchResult(
                    id=str(hit.id),
                    score=hit.score,
                    payload=hit.payload or {},
                )
                for hit in search_result
            ]

            query_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "qdrant_search_success",
                collection=collection,
                results=len(results),
                time_ms=query_time_ms,
            )

            return VectorSearchResponse(
                results=results,
                total=len(results),
                query_time_ms=query_time_ms,
            )

        except Exception as e:
            logger.error("qdrant_search_failed", collection=collection, error=str(e))
            return VectorSearchResponse(
                results=[],
                total=0,
                query_time_ms=int((time.time() - start_time) * 1000),
            )

    def get(
        self,
        collection: str,
        id: str,
    ) -> Optional[VectorDocument]:
        """Get a document by ID from Qdrant."""
        try:
            points = self.client.retrieve(
                collection_name=collection,
                ids=[id],
            )

            if not points:
                return None

            point = points[0]
            return VectorDocument(
                id=str(point.id),
                vector=point.vector,
                payload=point.payload or {},
            )

        except Exception as e:
            logger.error("qdrant_get_failed", collection=collection, id=id, error=str(e))
            return None

    def count(self, collection: str) -> int:
        """Count documents in Qdrant collection."""
        try:
            info = self.client.get_collection(collection_name=collection)
            return info.points_count
        except Exception as e:
            logger.error("qdrant_count_failed", collection=collection, error=str(e))
            return 0

    def health_check(self) -> dict:
        """Check Qdrant health."""
        try:
            collections = self.client.get_collections()
            return {
                "healthy": True,
                "collections": len(collections.collections),
                "host": self.host,
                "port": self.port,
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "host": self.host,
                "port": self.port,
            }
