"""
Search Service Initialization

This module initializes the SearchService with all registered plugins.
"""

from apps.search.interfaces import SearchService
from apps.search.typesense_plugin import TypesenseSearchPlugin
from apps.search.postgres_plugin import PostgresSearchPlugin
from apps.search.embeddings import embedding_service, EmbeddingService


def get_search_service() -> SearchService:
    """
    Get the initialized SearchService with all plugins registered.
    
    Returns:
        SearchService instance with Typesense (primary) and Postgres (fallback)
    """
    service = SearchService()
    
    # Register Typesense as primary plugin
    typesense_plugin = TypesenseSearchPlugin()
    service.register_plugin(typesense_plugin)
    
    # Register Postgres as fallback plugin
    postgres_plugin = PostgresSearchPlugin()
    service.register_plugin(postgres_plugin)
    
    return service


# Global search service instance
search_service = get_search_service()

# Global embedding service instance
embedding_service = embedding_service
