"""
Embedding Plugin Abstraction

Abstract base class for embedding generation plugins (Cohere, OpenAI, Bedrock, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class EmbeddingRequest:
    """Request to generate embeddings."""

    texts: List[str]
    model: str = "cohere-embed-v3"
    input_type: str = "search_document"  # search_document, search_query, classification, clustering


@dataclass
class EmbeddingResponse:
    """Response containing generated embeddings."""

    embeddings: List[List[float]]
    model: str
    dimensions: int
    tokens_used: int = 0
    cost_usd: float = 0.0


class EmbeddingPlugin(ABC):
    """Abstract base class for embedding generation plugins."""

    @abstractmethod
    def generate(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings for given texts.

        Args:
            request: Embedding request with texts and parameters

        Returns:
            Embedding response with vectors
        """
        pass

    @abstractmethod
    def get_dimensions(self, model: str) -> int:
        """Get the dimension size for a model."""
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """Check if embedding service is healthy."""
        pass
