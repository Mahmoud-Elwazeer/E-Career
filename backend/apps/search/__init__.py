# Search app for Typesense-powered job search
from .services import search_service, embedding_service
from .embeddings import EmbeddingService

__all__ = [
    'search_service',
    'embedding_service',
    'EmbeddingService',
]

default_app_config = "apps.search.apps.SearchConfig"
