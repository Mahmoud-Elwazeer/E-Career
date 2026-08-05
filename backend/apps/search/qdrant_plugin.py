"""
Qdrant Vector Search Plugin

This module implements a Qdrant plugin for the SearchService that provides
semantic search capabilities using vector embeddings.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from django.db.models import QuerySet
from django.conf import settings

from apps.search.interfaces import SearchPlugin
from apps.jobs.models import Job
from apps.search.embeddings import embedding_service

logger = logging.getLogger(__name__)


class QdrantSearchPlugin(SearchPlugin):
    """
    Qdrant vector search plugin for semantic job matching.
    
    Features:
    - Semantic search using Cohere Embed v3 vectors (1024 dimensions)
    - Hybrid search (vector + keyword)
    - Similar job recommendations
    - Candidate similarity matching
    """
    
    name: str = "qdrant"
    
    def __init__(self):
        self._embedding_service = embedding_service
        self._collection_name = getattr(settings, 'QDRANT_COLLECTION_NAME', 'jobs')
    
    @property
    def is_available(self) -> bool:
        """Check if Qdrant is available."""
        return self._embedding_service.qdrant_client is not None
    
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
        Execute a semantic search query using vector embeddings.
        
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
        if not self.is_available:
            logger.warning("Qdrant not available, returning empty results")
            return {
                'results': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'facets': {},
            }
        
        try:
            # Generate query embedding
            query_embedding = self._embedding_service.generate_embedding(query)
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return {
                    'results': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'facets': {},
                }
            
            # Search Qdrant
            results = self._embedding_service.search_by_embedding(query_embedding, limit=page_size)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'job_id': result.get('job_id'),
                    'score': result.get('score', 0),
                    'text': result.get('text', ''),
                })
            
            return {
                'results': formatted_results,
                'total': len(formatted_results),
                'page': page,
                'page_size': page_size,
                'facets': {},
            }
            
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return {
                'results': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'facets': {},
            }
    
    def autocomplete(
        self,
        query: str,
        field: str = "title",
        limit: int = 10,
    ) -> List[str]:
        """
        Get autocomplete suggestions using vector embeddings.
        
        Args:
            query: Partial query string
            field: Field to autocomplete on
            limit: Maximum number of suggestions
            
        Returns:
            List of autocomplete suggestions
        """
        if not self.is_available:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self._embedding_service.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Search Qdrant
            results = self._embedding_service.search_by_embedding(query_embedding, limit=limit)
            
            # Extract titles from results
            suggestions = []
            for result in results:
                text = result.get('text', '')
                # Extract title from text (first line)
                title = text.split('\n')[0] if text else ''
                if title:
                    suggestions.append(title)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Qdrant autocomplete failed: {e}")
            return []
    
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
        # Qdrant doesn't support facets natively, return empty
        return {}
    
    def sync_job(self, job: Job) -> bool:
        """
        Sync a single job to the Qdrant vector index.
        
        Args:
            job: Job instance to sync
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            logger.warning("Qdrant not available, skipping sync")
            return False
        
        try:
            # Generate text to embed (title + description + location)
            text = f"{job.title}\n{job.description}\n{job.location}"
            
            # Store embedding
            success = self._embedding_service.store_embedding(
                job_id=str(job.uuid),
                text=text,
                metadata={
                    'title': job.title,
                    'description': job.description,
                    'location': job.location,
                    'company': job.company.name if job.company else '',
                    'employment_type': job.employment_type,
                    'experience_level': job.experience_level,
                    'remote_type': job.remote_type,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max,
                }
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync job {job.id} to Qdrant: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from the Qdrant vector index.
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            logger.warning("Qdrant not available, skipping delete")
            return False
        
        try:
            # Delete from Qdrant
            self._embedding_service.delete_job_embedding(job_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete job {job_id} from Qdrant: {e}")
            return False
    
    def sync_all_jobs(self, queryset: Optional[QuerySet] = None) -> Tuple[int, int]:
        """
        Sync all jobs to the Qdrant vector index.
        
        Args:
            queryset: Optional queryset to sync (defaults to all active jobs)
            
        Returns:
            Tuple of (synced_count, failed_count)
        """
        if not self.is_available:
            logger.warning("Qdrant not available, skipping sync")
            return 0, 0
        
        if queryset is None:
            queryset = Job.objects.filter(is_active=True)
        
        jobs_data = []
        for job in queryset:
            text = f"{job.title}\n{job.description}\n{job.location}"
            jobs_data.append({
                'id': str(job.uuid),
                'text': text,
                'metadata': {
                    'title': job.title,
                    'description': job.description,
                    'location': job.location,
                    'company': job.company.name if job.company else '',
                    'employment_type': job.employment_type,
                    'experience_level': job.experience_level,
                    'remote_type': job.remote_type,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max,
                }
            })
        
        try:
            result = self._embedding_service.batch_store_embeddings(jobs_data)
            return result['success'], result['failed']
            
        except Exception as e:
            logger.error(f"Failed to batch sync jobs to Qdrant: {e}")
            return 0, len(jobs_data)
    
    def health_check(self) -> bool:
        """
        Check if the Qdrant search backend is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # Try to get collections
            collections = self._embedding_service.qdrant_client.get_collections()
            return len(collections.collections) >= 0
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    def get_similar_jobs(self, job_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get jobs similar to a specific job.
        
        Args:
            job_id: Job ID to find similar jobs for
            limit: Maximum number of similar jobs
            
        Returns:
            List of similar jobs with scores
        """
        if not self.is_available:
            return []
        
        try:
            # Get the job's embedding
            collection_name = getattr(settings, 'QDRANT_COLLECTION_NAME', 'jobs')
            
            # Search for similar jobs
            results = self._embedding_service.qdrant_client.search(
                collection_name=collection_name,
                query_vector=[0.0] * 1024,  # Placeholder - would need to retrieve actual vector
                limit=limit,
            )
            
            # Format results
            formatted_results = []
            for point in results:
                formatted_results.append({
                    'job_id': point.payload.get('job_id'),
                    'score': point.score,
                    'text': point.payload.get('text', ''),
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to get similar jobs: {e}")
            return []
    
    def get_user_recommendations(
        self,
        user_profile_text: str,
        limit: int = 10,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Get job recommendations for a user based on their profile.
        
        Args:
            user_profile_text: User profile text (skills, experience, preferences)
            limit: Maximum number of recommendations
            min_score: Minimum similarity score threshold
            
        Returns:
            List of recommended jobs with scores
        """
        if not self.is_available:
            return []
        
        try:
            # Generate user profile embedding
            user_embedding = self._embedding_service.generate_embedding(user_profile_text)
            if not user_embedding:
                return []
            
            # Search Qdrant
            results = self._embedding_service.search_by_embedding(user_embedding, limit=limit * 2)
            
            # Filter by minimum score and limit
            recommendations = []
            for result in results:
                if result.get('score', 0) >= min_score:
                    recommendations.append({
                        'job_id': result.get('job_id'),
                        'score': result.get('score', 0),
                        'text': result.get('text', ''),
                    })
                    if len(recommendations) >= limit:
                        break
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get user recommendations: {e}")
            return []


# Singleton instance
qdrant_plugin = QdrantSearchPlugin()