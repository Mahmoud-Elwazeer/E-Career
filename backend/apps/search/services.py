"""
Search service singleton — delegates to the canonical service module.

This file exists for backwards compatibility. The canonical implementation
is in apps.search.service.SearchService.
"""
from apps.search.service import SearchService, get_search_service  # noqa: F401

search_service = get_search_service()
