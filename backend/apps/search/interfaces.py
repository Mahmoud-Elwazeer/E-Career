"""
Search Service Interface and Plugin Architecture

This module defines the abstract base class for search plugins and the
SearchService that orchestrates multiple search backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from django.db.models import QuerySet
from apps.jobs.models import Job


class SearchPlugin(ABC):
    """Abstract base class for search backend plugins."""
    
    name: str = ""
    
    @abstractmethod
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        facets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a search query.
        
        Args:
            query: The search query string
            filters: Additional filters (e.g., location, salary range)
            page: Page number for pagination
            page_size: Number of results per page
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            facets: List of facet fields to include
            
        Returns:
            Dictionary with search results, total count, and facets
        """
        pass
    
    @abstractmethod
    def autocomplete(
        self,
        query: str,
        field: str = "title",
        limit: int = 10,
    ) -> List[str]:
        """
        Get autocomplete suggestions.
        
        Args:
            query: Partial query string
            field: Field to autocomplete on
            limit: Maximum number of suggestions
            
        Returns:
            List of autocomplete suggestions
        """
        pass
    
    @abstractmethod
    def get_facets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        facet_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get facet values for filtering.
        
        Args:
            filters: Current filters applied
            facet_fields: Fields to get facets for
            
        Returns:
            Dictionary with facet values and counts
        """
        pass
    
    @abstractmethod
    def sync_job(self, job: Job) -> bool:
        """
        Sync a single job to the search index.
        
        Args:
            job: Job instance to sync
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from the search index.
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def sync_all_jobs(self, queryset: Optional[QuerySet] = None) -> Tuple[int, int]:
        """
        Sync all jobs to the search index.
        
        Args:
            queryset: Optional queryset to sync (defaults to all active jobs)
            
        Returns:
            Tuple of (synced_count, failed_count)
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the search backend is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass


class SearchService:
    """
    Main search service that orchestrates multiple search backends.
    
    Uses a primary plugin (e.g., Typesense) with fallback to secondary
    plugin (e.g., Postgres) if the primary fails.
    """
    
    def __init__(self):
        self.plugins: Dict[str, SearchPlugin] = {}
        self.primary_plugin: Optional[SearchPlugin] = None
        self.fallback_plugin: Optional[SearchPlugin] = None
    
    def register_plugin(self, plugin: SearchPlugin) -> None:
        """Register a search plugin."""
        self.plugins[plugin.name] = plugin
        if not self.primary_plugin:
            self.primary_plugin = plugin
        elif not self.fallback_plugin:
            self.fallback_plugin = plugin
    
    def get_plugin(self, name: str) -> Optional[SearchPlugin]:
        """Get a registered plugin by name."""
        return self.plugins.get(name)
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        facets: Optional[List[str]] = None,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a search query using the primary plugin with fallback.
        
        Args:
            query: The search query string
            filters: Additional filters
            page: Page number for pagination
            page_size: Number of results per page
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            facets: List of facet fields to include
            use_fallback: Whether to use fallback plugin if primary fails
            
        Returns:
            Dictionary with search results
        """
        if not self.primary_plugin:
            raise RuntimeError("No primary search plugin registered")
        
        try:
            return self.primary_plugin.search(
                query=query,
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
                facets=facets,
            )
        except Exception as primary_error:
            if use_fallback and self.fallback_plugin:
                # Log the error (would use proper logging in production)
                print(f"Primary search failed: {primary_error}. Falling back to secondary.")
                return self.fallback_plugin.search(
                    query=query,
                    filters=filters,
                    page=page,
                    page_size=page_size,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    facets=facets,
                )
            raise
    
    def autocomplete(
        self,
        query: str,
        field: str = "title",
        limit: int = 10,
        use_fallback: bool = True,
    ) -> List[str]:
        """Get autocomplete suggestions with fallback."""
        if not self.primary_plugin:
            raise RuntimeError("No primary search plugin registered")
        
        try:
            return self.primary_plugin.autocomplete(query=query, field=field, limit=limit)
        except Exception as primary_error:
            if use_fallback and self.fallback_plugin:
                print(f"Primary autocomplete failed: {primary_error}. Falling back.")
                return self.fallback_plugin.autocomplete(query=query, field=field, limit=limit)
            raise
    
    def get_facets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        facet_fields: Optional[List[str]] = None,
        use_fallback: bool = True,
    ) -> Dict[str, Any]:
        """Get facet values with fallback."""
        if not self.primary_plugin:
            raise RuntimeError("No primary search plugin registered")
        
        try:
            return self.primary_plugin.get_facets(
                filters=filters,
                facet_fields=facet_fields,
            )
        except Exception as primary_error:
            if use_fallback and self.fallback_plugin:
                print(f"Primary facets failed: {primary_error}. Falling back.")
                return self.fallback_plugin.get_facets(
                    filters=filters,
                    facet_fields=facet_fields,
                )
            raise
    
    def sync_job(self, job: Job) -> bool:
        """Sync a job to all registered plugins."""
        success = True
        for plugin in self.plugins.values():
            try:
                plugin.sync_job(job)
            except Exception as e:
                print(f"Failed to sync job {job.id} to {plugin.name}: {e}")
                success = False
        return success
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from all registered plugins."""
        success = True
        for plugin in self.plugins.values():
            try:
                plugin.delete_job(job_id)
            except Exception as e:
                print(f"Failed to delete job {job_id} from {plugin.name}: {e}")
                success = False
        return success
    
    def sync_all_jobs(self, queryset: Optional[QuerySet] = None) -> Tuple[int, int]:
        """Sync all jobs to all registered plugins."""
        synced = 0
        failed = 0
        
        for plugin in self.plugins.values():
            try:
                s, f = plugin.sync_all_jobs(queryset)
                synced += s
                failed += f
            except Exception as e:
                print(f"Failed to sync all jobs to {plugin.name}: {e}")
                failed += 1
        
        return synced, failed
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all registered plugins."""
        return {name: plugin.health_check() for name, plugin in self.plugins.items()}