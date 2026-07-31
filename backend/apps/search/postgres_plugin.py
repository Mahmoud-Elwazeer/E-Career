"""
PostgreSQL Search Plugin (Fallback)

Implements the SearchPlugin interface using PostgreSQL's full-text search.
Used as a fallback when Typesense is unavailable.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from django.db.models import QuerySet, Q
from django.db.models.functions import Lower
from django.db.models.expressions import RawSQL
from apps.jobs.models import Job
from apps.search.interfaces import SearchPlugin

logger = logging.getLogger(__name__)


class PostgresSearchPlugin(SearchPlugin):
    """
    PostgreSQL search plugin implementing the SearchPlugin interface.
    
    Uses PostgreSQL's full-text search (tsvector/tsquery) for search functionality.
    Falls back to this when Typesense is unavailable.
    """
    
    name: str = "postgres"
    
    def __init__(self):
        self.trust_score_threshold = 0.4  # Default threshold
    
    def _get_trust_score_filter(self) -> Q:
        """Get the trust score filter Q object."""
        return Q(trust_score__gte=self.trust_score_threshold)
    
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
        Execute a search query using PostgreSQL full-text search.
        
        Args:
            query: The search query string
            filters: Additional filters (e.g., location, salary range)
            page: Page number for pagination
            page_size: Number of results per page
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            facets: List of facet fields to include (not fully supported in this fallback)
            
        Returns:
            Dictionary with search results, total count, and facets
        """
        try:
            # Start with active jobs and trust score filter
            qs = Job.objects.filter(status="active").filter(self._get_trust_score_filter())
            
            # Add text search
            if query:
                # Use PostgreSQL full-text search
                from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
                from django.db.models import F
                
                # Create search vector for title and description
                vector = SearchVector("title", weight="A") + SearchVector("description", weight="B")
                
                search_query = SearchQuery(query)
                
                qs = qs.annotate(
                    search=vector,
                    rank=SearchRank(F("search"), search_query),
                ).filter(search=search_query).order_by("-rank")
            else:
                # No query, just apply filters
                qs = qs.order_by("-posted_at")
            
            # Apply additional filters
            if filters:
                if filters.get("location"):
                    qs = qs.filter(location__icontains=filters["location"])
                if filters.get("industry"):
                    qs = qs.filter(industry=filters["industry"])
                if filters.get("experience_level"):
                    qs = qs.filter(experience_level=filters["experience_level"])
                if filters.get("work_arrangement"):
                    qs = qs.filter(work_arrangement=filters["work_arrangement"])
                if filters.get("employment_type"):
                    qs = qs.filter(employment_type=filters["employment_type"])
                if filters.get("salary_min"):
                    qs = qs.filter(salary_min__gte=filters["salary_min"])
                if filters.get("salary_max"):
                    qs = qs.filter(salary_max__lte=filters["salary_max"])
                if filters.get("company"):
                    qs = qs.filter(company__name__icontains=filters["company"])
            
            # Apply sorting
            if sort_by:
                if sort_by == "salary_min":
                    qs = qs.order_by(f"{'-' if sort_order == 'desc' else ''}salary_min")
                elif sort_by == "salary_max":
                    qs = qs.order_by(f"{'-' if sort_order == 'desc' else ''}salary_max")
                elif sort_by == "posted_at":
                    qs = qs.order_by(f"{'-' if sort_order == 'desc' else ''}posted_at")
                else:
                    qs = qs.order_by(f"{'-' if sort_order == 'desc' else ''}title")
            else:
                # Default: sort by posted_at descending
                qs = qs.order_by("-posted_at")
            
            # Calculate pagination
            total = qs.count()
            start = (page - 1) * page_size
            end = start + page_size
            
            # Get results
            results = qs[start:end]
            
            # Process results
            processed_results = []
            for job in results:
                # Get skills from tags
                skills = list(job.tags.values_list("name", flat=True))
                
                processed_results.append({
                    "id": str(job.id),
                    "title": job.title or "",
                    "company_name": job.company.name if job.company else "",
                    "location": job.location or "",
                    "country": "",
                    "work_arrangement": job.work_arrangement or "",
                    "industry": job.industry or "",
                    "experience_level": job.experience_level or "",
                    "employment_type": job.employment_type or "",
                    "salary_min": job.salary_min or 0,
                    "salary_max": job.salary_max or 0,
                    "salary_currency": job.salary_currency or "USD",
                    "skills": skills,
                    "ats_platform": job.ats_platform or "",
                    "trust_score": job.trust_score if hasattr(job, "trust_score") and job.trust_score else 0.0,
                    "posted_at": job.posted_at.timestamp() if job.posted_at else 0,
                    "description": job.description or "",
                })
            
            # Calculate facets (simplified - not as efficient as Typesense)
            processed_facets = {}
            if facets:
                for facet_field in facets:
                    try:
                        if facet_field == "location":
                            facet_data = qs.values("location").annotate(count=RawSQL("COUNT(*) OVER (PARTITION BY location)", [])).distinct("location")[:10]
                            processed_facets[facet_field] = {
                                "counts": [{"value": item["location"], "count": 1} for item in facet_data],
                                "total_values": qs.values("location").distinct().count(),
                            }
                        elif facet_field == "industry":
                            facet_data = qs.values("industry").annotate(count=RawSQL("COUNT(*) OVER (PARTITION BY industry)", [])).distinct("industry")[:10]
                            processed_facets[facet_field] = {
                                "counts": [{"value": item["industry"], "count": 1} for item in facet_data],
                                "total_values": qs.values("industry").distinct().count(),
                            }
                        elif facet_field == "company_name":
                            facet_data = qs.select_related("company").values("company__name").annotate(count=RawSQL("COUNT(*) OVER (PARTITION BY company_id)", [])).distinct("company__name")[:10]
                            processed_facets[facet_field] = {
                                "counts": [{"value": item["company__name"], "count": 1} for item in facet_data],
                                "total_values": qs.select_related("company").values("company__name").distinct().count(),
                            }
                    except Exception as e:
                        logger.error(f"Failed to compute facet {facet_field}: {e}")
            
            return {
                "results": processed_results,
                "total": total,
                "facets": processed_facets,
                "page": page,
                "page_size": page_size,
                "query": query,
            }
            
        except Exception as e:
            logger.error(f"Postgres search error: {e}")
            return {
                "results": [],
                "total": 0,
                "facets": {},
                "page": page,
                "page_size": page_size,
                "error": str(e),
            }
    
    def autocomplete(
        self,
        query: str,
        field: str = "title",
        limit: int = 10,
    ) -> List[str]:
        """
        Get autocomplete suggestions from PostgreSQL.
        
        Args:
            query: Partial query string
            field: Field to autocomplete on
            limit: Maximum number of suggestions
            
        Returns:
            List of autocomplete suggestions
        """
        try:
            qs = Job.objects.filter(status="active").filter(self._get_trust_score_filter())
            
            if field == "title":
                qs = qs.filter(title__icontains=query).values_list("title", flat=True).distinct()[:limit]
            elif field == "company_name":
                qs = qs.select_related("company").filter(company__name__icontains=query).values_list("company__name", flat=True).distinct()[:limit]
            else:
                qs = []
            
            return list(qs)
            
        except Exception as e:
            logger.error(f"Postgres autocomplete error: {e}")
            return []
    
    def get_facets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        facet_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get facet values for filtering (simplified implementation).
        
        Args:
            filters: Current filters applied
            facet_fields: Fields to get facets for
            
        Returns:
            Dictionary with facet values and counts
        """
        try:
            qs = Job.objects.filter(status="active").filter(self._get_trust_score_filter())
            
            if filters:
                if filters.get("location"):
                    qs = qs.filter(location__icontains=filters["location"])
                if filters.get("industry"):
                    qs = qs.filter(industry=filters["industry"])
            
            if not facet_fields:
                facet_fields = ["location", "industry", "experience_level", "work_arrangement", "employment_type", "company_name"]
            
            processed_facets = {}
            for facet_field in facet_fields:
                try:
                    if facet_field == "location":
                        data = qs.values("location").annotate(count=RawSQL("COUNT(*) OVER (PARTITION BY location)", [])).distinct("location")[:20]
                        processed_facets[facet_field] = {
                            "counts": [{"value": item["location"], "count": 1} for item in data],
                            "total_values": qs.values("location").distinct().count(),
                        }
                    elif facet_field == "industry":
                        data = qs.values("industry").annotate(count=RawSQL("COUNT(*) OVER (PARTITION BY industry)", [])).distinct("industry")[:20]
                        processed_facets[facet_field] = {
                            "counts": [{"value": item["industry"], "count": 1} for item in data],
                            "total_values": qs.values("industry").distinct().count(),
                        }
                    elif facet_field == "company_name":
                        data = qs.select_related("company").values("company__name").annotate(count=RawSQL("COUNT(*) OVER (PARTITION BY company_id)", [])).distinct("company__name")[:20]
                        processed_facets[facet_field] = {
                            "counts": [{"value": item["company__name"], "count": 1} for item in data],
                            "total_values": qs.select_related("company").values("company__name").distinct().count(),
                        }
                except Exception as e:
                    logger.error(f"Failed to compute facet {facet_field}: {e}")
            
            return processed_facets
            
        except Exception as e:
            logger.error(f"Postgres facets error: {e}")
            return {}
    
    def sync_job(self, job: Job) -> bool:
        """
        Sync a single job to PostgreSQL (no-op for this fallback).
        
        Args:
            job: Job instance to sync
            
        Returns:
            True if successful, False otherwise
        """
        # PostgreSQL is the source of truth, so no sync needed
        return True
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from PostgreSQL (no-op for this fallback).
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        # PostgreSQL is the source of truth, so no sync needed
        return True
    
    def sync_all_jobs(self, queryset: Optional[QuerySet] = None) -> Tuple[int, int]:
        """
        Sync all jobs to PostgreSQL (no-op for this fallback).
        
        Args:
            queryset: Optional queryset to sync (defaults to all active jobs)
            
        Returns:
            Tuple of (synced_count, failed_count)
        """
        # PostgreSQL is the source of truth, so no sync needed
        if queryset is None:
            queryset = Job.objects.filter(status="active")
        return queryset.count(), 0
    
    def health_check(self) -> bool:
        """
        Check if PostgreSQL is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple query
            Job.objects.exists()
            return True
        except Exception as e:
            logger.error(f"Postgres health check failed: {e}")
            return False