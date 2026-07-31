from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchQuery:
    """Represents a search request with filters and pagination."""

    q: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    facets: list[str] = field(default_factory=list)
    sort_by: str = ""
    page: int = 1
    per_page: int = 20
    query_by: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """A single search hit."""

    id: str
    score: float
    data: dict[str, Any]
    highlights: dict[str, str] = field(default_factory=dict)


@dataclass
class FacetCount:
    """A single facet value count."""

    value: str
    count: int


@dataclass
class SearchResponse:
    """Response from a search operation."""

    hits: list[SearchResult]
    total: int
    page: int
    per_page: int
    facets: dict[str, list[FacetCount]] = field(default_factory=dict)
    query_time_ms: int = 0


class SearchPlugin(abc.ABC):
    """Abstract base class for search engine plugins."""

    @abc.abstractmethod
    def initialize(self) -> None:
        """Set up connection and create collections/indexes if needed."""

    @abc.abstractmethod
    def search(self, collection: str, query: SearchQuery) -> SearchResponse:
        """Execute a search query against a collection."""

    @abc.abstractmethod
    def index_document(self, collection: str, document: dict[str, Any]) -> None:
        """Index or update a single document."""

    @abc.abstractmethod
    def index_documents_batch(
        self, collection: str, documents: list[dict[str, Any]]
    ) -> int:
        """Index multiple documents. Returns count of successfully indexed."""

    @abc.abstractmethod
    def delete_document(self, collection: str, document_id: str) -> None:
        """Remove a document from the index."""

    @abc.abstractmethod
    def create_collection(self, collection: str, schema: dict[str, Any]) -> None:
        """Create a collection with the given schema."""

    @abc.abstractmethod
    def drop_collection(self, collection: str) -> None:
        """Drop a collection and all its data."""

    @abc.abstractmethod
    def health_check(self) -> bool:
        """Return True if the search engine is healthy."""

    @abc.abstractmethod
    def autocomplete(
        self, collection: str, prefix: str, field: str, limit: int = 5
    ) -> list[str]:
        """Return autocomplete suggestions for a prefix."""
