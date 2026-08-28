"""
Vector Plugin Abstraction

Abstract base class for vector database plugins.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class VectorDocument:
    """Document to be indexed in vector database."""

    id: str
    vector: List[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorSearchQuery:
    """Vector search query parameters."""

    vector: List[float]
    limit: int = 20
    score_threshold: Optional[float] = None
    filter: Optional[dict[str, Any]] = None


@dataclass
class VectorSearchResult:
    """Single vector search result."""

    id: str
    score: float
    payload: dict[str, Any]


@dataclass
class VectorSearchResponse:
    """Vector search response with results."""

    results: List[VectorSearchResult]
    total: int
    query_time_ms: int


class VectorPlugin(ABC):
    """Abstract base class for vector database plugins."""

    @abstractmethod
    def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: str = "cosine",
    ) -> bool:
        """
        Create a new collection.

        Args:
            name: Collection name
            vector_size: Dimension of vectors
            distance: Distance metric (cosine, euclidean, dot)

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        pass

    @abstractmethod
    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        pass

    @abstractmethod
    def upsert(
        self,
        collection: str,
        documents: List[VectorDocument],
    ) -> int:
        """
        Insert or update documents in collection.

        Returns:
            Number of documents upserted
        """
        pass

    @abstractmethod
    def delete(
        self,
        collection: str,
        ids: List[str],
    ) -> int:
        """
        Delete documents by IDs.

        Returns:
            Number of documents deleted
        """
        pass

    @abstractmethod
    def search(
        self,
        collection: str,
        query: VectorSearchQuery,
    ) -> VectorSearchResponse:
        """
        Search for similar vectors.

        Returns:
            Search response with results
        """
        pass

    @abstractmethod
    def get(
        self,
        collection: str,
        id: str,
    ) -> Optional[VectorDocument]:
        """Get a document by ID."""
        pass

    @abstractmethod
    def count(self, collection: str) -> int:
        """Count documents in collection."""
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """Check if vector database is healthy."""
        pass
