"""
Typesense Search Plugin

Implements the SearchPlugin interface for Typesense search engine.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from django.conf import settings
from django.db.models import QuerySet
from apps.jobs.models import Job
from apps.search.interfaces import SearchPlugin

logger = logging.getLogger(__name__)


class TypesenseSearchPlugin(SearchPlugin):
    """
    Typesense search plugin implementing the SearchPlugin interface.
    
    Features:
    - Typo-tolerant search
    - Faceted filtering
    - Autocomplete
    - Trust score filtering
    """
    
    name: str = "typesense"
    
    def __init__(self):
        self.client = None
        self.collection_name = "jobs"
        self.trust_score_threshold = getattr(
            settings, "SEARCH_TRUST_SCORE_THRESHOLD", 0.4
        )
        self._init_client()
    
    def _init_client(self) -> None:
        """Initialize Typesense client."""
        try:
            import typesense
            
            host = getattr(settings, "TYPESENSE_HOST", "typesense")
            port = getattr(settings, "TYPESENSE_PORT", 8108)
            protocol = getattr(settings, "TYPESENSE_PROTOCOL", "http")
            api_key = getattr(settings, "TYPESENSE_API_KEY", "ecareer_typesense_dev_key")
            
            self.client = typesense.Client({
                "nodes": [{
                    "host": host,
                    "port": port,
                    "protocol": protocol,
                }],
                "api_key": api_key,
                "connection_timeout_seconds": 5,
            })
            logger.info("Typesense client initialized successfully")
        except ImportError:
            logger.error("typesense package not installed. Run: pip install typesense")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Typesense client: {e}")
            self.client = None
    
    def _ensure_collection(self) -> bool:
        """Ensure the jobs collection exists with the correct schema."""
        if not self.client:
            return False
        
        try:
            # Check if collection exists
            collections = self.client.collections.retrieve()
            collection_names = [c["name"] for c in collections]
            
            if self.collection_name not in collection_names:
                # Create the collection with the schema from DATA_ARCHITECTURE.md
                schema = {
                    "name": self.collection_name,
                    "fields": [
                        {"name": "id", "type": "string"},
                        {"name": "title", "type": "string", "index": True},
                        {"name": "company_name", "type": "string", "facet": True},
                        {"name": "location", "type": "string", "facet": True},
                        {"name": "country", "type": "string", "facet": True},
                        {"name": "work_arrangement", "type": "string", "facet": True},
                        {"name": "industry", "type": "string", "facet": True},
                        {"name": "experience_level", "type": "string", "facet": True},
                        {"name": "employment_type", "type": "string", "facet": True},
                        {"name": "salary_min", "type": "int32", "facet": True},
                        {"name": "salary_max", "type": "int32", "facet": True},
                        {"name": "salary_currency", "type": "string", "facet": True},
                        {"name": "skills", "type": "string[]", "facet": True},
                        {"name": "ats_platform", "type": "string", "facet": True},
                        {"name": "trust_score", "type": "float"},
                        {"name": "posted_at", "type": "int64"},
                        {"name": "description", "type": "string"},
                    ],
                    "default_sorting_field": "posted_at",
                    "token_separators": ["-", "/"],
                }
                self.client.collections.create(schema)
                logger.info(f"Created Typesense collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            return False
    
    def _job_to_document(self, job: Job) -> Dict[str, Any]:
        """Convert a Job model instance to a Typesense document."""
        # Extract skills from tags
        skills = list(job.tags.values_list("name", flat=True)) if job.tags.exists() else []
        
        # Extract country from location (simple heuristic)
        location_parts = job.location.split(",") if job.location else []
        country = location_parts[-1].strip() if len(location_parts) > 1 else ""
        
        return {
            "id": str(job.id),
            "title": job.title or "",
            "company_name": job.company.name if job.company else "",
            "location": job.location or "",
            "country": country,
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
            "posted_at": int(job.posted_at.timestamp()) if job.posted_at else 0,
            "description": job.description or "",
        }
    
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
        Execute a search query using Typesense.
        
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
        if not self.client or not self._ensure_collection():
            return {
                "results": [],
                "total": 0,
                "facets": {},
                "page": page,
                "page_size": page_size,
            }
        
        try:
            # Build search parameters
            search_params: Dict[str, Any] = {
                "q": query or "*",
                "query_by": "title,description,company_name",
                "page": page,
                "per_page": page_size,
                "highlight_fields": "title,description",
                "highlight_affinity": "10",
                "typo_tokens_threshold": 100,
                "prefix": "false",
                "drop_tokens_threshold": 10,
                "cross_fields": "title,description",
            }
            
            # Add trust score filter (mandatory)
            search_params["filter_by"] = f"trust_score:>={self.trust_score_threshold}"
            
            # Add additional filters
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    if key == "location" and value:
                        filter_parts.append(f"location:=[{value}]")
                    elif key == "industry" and value:
                        filter_parts.append(f"industry:=[{value}]")
                    elif key == "experience_level" and value:
                        filter_parts.append(f"experience_level:=[{value}]")
                    elif key == "work_arrangement" and value:
                        filter_parts.append(f"work_arrangement:=[{value}]")
                    elif key == "employment_type" and value:
                        filter_parts.append(f"employment_type:=[{value}]")
                    elif key == "salary_min" and value:
                        filter_parts.append(f"salary_min:>={value}")
                    elif key == "salary_max" and value:
                        filter_parts.append(f"salary_max:<={value}")
                    elif key == "company" and value:
                        filter_parts.append(f"company_name=={value}")
                if filter_parts:
                    search_params["filter_by"] += " && " + " && ".join(filter_parts)
            
            # Add sorting
            if sort_by:
                sort_field = sort_by
                if sort_field == "salary_min":
                    sort_field = "salary_min"
                elif sort_field == "salary_max":
                    sort_field = "salary_max"
                elif sort_field == "posted_at":
                    sort_field = "posted_at"
                else:
                    sort_field = "title"
                search_params["sort_by"] = f"{sort_field}:{sort_order}"
            
            # Add facets
            if facets:
                search_params["facets"] = ",".join(facets)
                search_params["facet_limit"] = 10
            
            # Execute search
            result = self.client.collections[self.collection_name].documents.search(search_params)
            
            # Process results
            processed_results = []
            for hit in result.get("hits", []):
                document = hit.get("document", {})
                processed_results.append({
                    "id": document.get("id"),
                    "title": document.get("title"),
                    "company_name": document.get("company_name"),
                    "location": document.get("location"),
                    "country": document.get("country"),
                    "work_arrangement": document.get("work_arrangement"),
                    "industry": document.get("industry"),
                    "experience_level": document.get("experience_level"),
                    "employment_type": document.get("employment_type"),
                    "salary_min": document.get("salary_min"),
                    "salary_max": document.get("salary_max"),
                    "salary_currency": document.get("salary_currency"),
                    "skills": document.get("skills", []),
                    "ats_platform": document.get("ats_platform"),
                    "trust_score": document.get("trust_score", 0.0),
                    "posted_at": document.get("posted_at"),
                    "description": document.get("description"),
                })
            
            # Process facets
            processed_facets = {}
            for facet_field, facet_data in result.get("facets", {}).items():
                processed_facets[facet_field] = {
                    "counts": [
                        {"value": bucket["value"], "count": bucket["count"]}
                        for bucket in facet_data.get("counts", [])
                    ],
                    "total_values": facet_data.get("total_values", 0),
                }
            
            return {
                "results": processed_results,
                "total": result.get("found", 0),
                "facets": processed_facets,
                "page": page,
                "page_size": page_size,
                "query": query,
            }
            
        except Exception as e:
            logger.error(f"Typesense search error: {e}")
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
        Get autocomplete suggestions from Typesense.
        
        Args:
            query: Partial query string
            field: Field to autocomplete on
            limit: Maximum number of suggestions
            
        Returns:
            List of autocomplete suggestions
        """
        if not self.client or not self._ensure_collection():
            return []
        
        try:
            result = self.client.collections[self.collection_name].documents.search({
                "q": query,
                "query_by": field,
                "prefix": "true",
                "per_page": limit,
                "max_candidates": 10,
                "highlight_full_fields": field,
            })
            
            suggestions = []
            for hit in result.get("hits", []):
                document = hit.get("document", {})
                if field == "title":
                    suggestions.append(document.get("title", ""))
                elif field == "company_name":
                    suggestions.append(document.get("company_name", ""))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Typesense autocomplete error: {e}")
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
        if not self.client or not self._ensure_collection():
            return {}
        
        if not facet_fields:
            facet_fields = [
                "location",
                "industry",
                "experience_level",
                "work_arrangement",
                "employment_type",
                "company_name",
            ]
        
        try:
            search_params = {
                "q": "*",
                "filter_by": f"trust_score:>={self.trust_score_threshold}",
                "facets": ",".join(facet_fields),
                "facet_limit": 20,
            }
            
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    if key == "location" and value:
                        filter_parts.append(f"location:=[{value}]")
                    elif key == "industry" and value:
                        filter_parts.append(f"industry:=[{value}]")
                if filter_parts:
                    search_params["filter_by"] += " && " + " && ".join(filter_parts)
            
            result = self.client.collections[self.collection_name].documents.search(search_params)
            
            processed_facets = {}
            for facet_field, facet_data in result.get("facets", {}).items():
                processed_facets[facet_field] = {
                    "counts": [
                        {"value": bucket["value"], "count": bucket["count"]}
                        for bucket in facet_data.get("counts", [])
                    ],
                    "total_values": facet_data.get("total_values", 0),
                }
            
            return processed_facets
            
        except Exception as e:
            logger.error(f"Typesense facets error: {e}")
            return {}
    
    def sync_job(self, job: Job) -> bool:
        """
        Sync a single job to the Typesense index.
        
        Args:
            job: Job instance to sync
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self._ensure_collection():
            return False
        
        try:
            document = self._job_to_document(job)
            self.client.collections[self.collection_name].documents.upsert(document)
            return True
        except Exception as e:
            logger.error(f"Failed to sync job {job.id} to Typesense: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from the Typesense index.
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.collections[self.collection_name].documents[job_id].delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id} from Typesense: {e}")
            return False
    
    def sync_all_jobs(self, queryset: Optional[QuerySet] = None) -> Tuple[int, int]:
        """
        Sync all jobs to the Typesense index.
        
        Args:
            queryset: Optional queryset to sync (defaults to all active jobs)
            
        Returns:
            Tuple of (synced_count, failed_count)
        """
        if not self.client or not self._ensure_collection():
            return 0, 0
        
        if queryset is None:
            queryset = Job.objects.filter(status="active")
        
        synced = 0
        failed = 0
        
        try:
            # Prepare documents in batch
            documents = []
            for job in queryset.iterator():
                try:
                    documents.append(self._job_to_document(job))
                    if len(documents) >= 100:  # Batch size
                        self.client.collections[self.collection_name].documents.upsert(documents)
                        synced += len(documents)
                        documents = []
                except Exception as e:
                    logger.error(f"Failed to prepare job {job.id}: {e}")
                    failed += 1
            
            # Sync remaining documents
            if documents:
                self.client.collections[self.collection_name].documents.upsert(documents)
                synced += len(documents)
                
        except Exception as e:
            logger.error(f"Failed to sync all jobs: {e}")
        
        return synced, failed
    
    def health_check(self) -> bool:
        """
        Check if the Typesense backend is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Try to get server info
            self.client.collections.retrieve()
            return True
        except Exception as e:
            logger.error(f"Typesense health check failed: {e}")
            return False