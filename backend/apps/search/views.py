"""
Search API Views

This module contains the Django REST Framework views for the search functionality.
"""

import logging
from typing import Any, Dict, List, Optional
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.search.services import search_service
from apps.jobs.models import Job
from apps.events.emitter import emit
from apps.events.types import SEARCH_PERFORMED, SEARCH_RESULT_CLICKED

logger = logging.getLogger(__name__)


@extend_schema(tags=["Search"])
class JobSearchView(APIView):
    """
    GET /api/v1/search/jobs/
    
    Typesense-powered job search with faceted filtering.
    
    Features:
    - Typo-tolerant search
    - Faceted filtering (location, salary, type, experience, work_arrangement)
    - Trust score filtering (mandatory)
    - Autocomplete support
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """
        Execute a search query.
        
        Query Parameters:
        - q: Search query string
        - page: Page number (default: 1)
        - page_size: Results per page (default: 20)
        - sort_by: Field to sort by (title, salary_min, salary_max, posted_at)
        - sort_order: Sort order (asc, desc)
        - location: Filter by location
        - industry: Filter by industry
        - experience_level: Filter by experience level
        - work_arrangement: Filter by work arrangement (onsite, remote, hybrid)
        - employment_type: Filter by employment type
        - salary_min: Minimum salary
        - salary_max: Maximum salary
        - company: Filter by company name
        - facets: Comma-separated list of facet fields
        """
        # Parse query parameters
        query = request.query_params.get("q", "")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        sort_by = request.query_params.get("sort_by")
        sort_order = request.query_params.get("sort_order", "desc")
        
        # Build filters
        filters: Dict[str, Any] = {}
        filter_fields = [
            "location",
            "industry",
            "experience_level",
            "work_arrangement",
            "employment_type",
            "salary_min",
            "salary_max",
            "company",
        ]
        for field in filter_fields:
            value = request.query_params.get(field)
            if value:
                # Handle numeric fields
                if field in ("salary_min", "salary_max"):
                    try:
                        filters[field] = float(value)
                    except ValueError:
                        pass
                else:
                    filters[field] = value
        
        # Parse facets
        facets_param = request.query_params.get("facets")
        facets = None
        if facets_param:
            facets = [f.strip() for f in facets_param.split(",") if f.strip()]
        
        # Emit SEARCH_PERFORMED event
        try:
            emit(
                event_type=SEARCH_PERFORMED,
                category="search",
                user=request.user if request.user.is_authenticated else None,
                target_type="search",
                target_id="search_api",
                data={"query": query, "filters": filters, "page": page, "page_size": page_size},
                request=request,
            )
        except Exception:
            pass
        
        # Execute search
        try:
            result = search_service.search(
                query=query,
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
                facets=facets,
            )
            
            return Response({
                "success": True,
                "data": result,
                "message": "",
                "errors": None,
            })
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Search failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Recommendation Engine Views
# ============================================================================

from rest_framework.permissions import IsAuthenticated
from apps.search.recommendation_engine import get_recommendation_engine


@extend_schema(tags=["Recommendations"])
class JobRecommendationsView(APIView):
    """
    GET /api/v1/search/recommendations/
    
    Get job recommendations for the authenticated user using ML-based recommendation engine.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Get job recommendations.
        
        Query Parameters:
        - n_recommendations: Number of recommendations (default: 10)
        - n_items: Number of items to consider (default: 20)
        """
        try:
            n_recommendations = int(request.query_params.get("n_recommendations", 10))
            n_items = int(request.query_params.get("n_items", 20))
            
            engine = get_recommendation_engine(request.user)
            recommendations = engine.get_recommendations(
                n_recommendations=n_recommendations,
                n_items=n_items,
            )
            
            return Response({
                "success": True,
                "data": recommendations,
                "message": "",
                "errors": None,
            })
            
        except Exception as e:
            logger.error(f"Recommendations error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Recommendations failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Recommendations"])
class SimilarJobsView(APIView):
    """
    GET /api/v1/search/similar-jobs/<job_uuid>/
    
    Get jobs similar to a specific job.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_uuid, *args, **kwargs):
        """
        Get similar jobs.
        
        Query Parameters:
        - n_similar: Number of similar jobs (default: 5)
        """
        try:
            n_similar = int(request.query_params.get("n_similar", 5))
            
            engine = get_recommendation_engine(request.user)
            similar_jobs = engine.get_similar_jobs(job_uuid, n_similar=n_similar)
            
            return Response({
                "success": True,
                "data": {
                    "job_id": job_uuid,
                    "similar_jobs": similar_jobs,
                },
                "message": "",
                "errors": None,
            })
            
        except Exception as e:
            logger.error(f"Similar jobs error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Similar jobs failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Recommendations"])
class TrainRecommendationModelView(APIView):
    """
    POST /api/v1/search/train-recommendation-model/
    
    Train the recommendation model for the authenticated user.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """
        Train the recommendation model.
        """
        try:
            engine = get_recommendation_engine(request.user)
            results = engine.train()
            
            return Response({
                "success": True,
                "data": results,
                "message": "",
                "errors": None,
            })
            
        except Exception as e:
            logger.error(f"Train model error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Training failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Search"])
class JobAutocompleteView(APIView):
    """
    GET /api/v1/search/autocomplete/
    
    Get autocomplete suggestions for job titles and company names.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """
        Get autocomplete suggestions.
        
        Query Parameters:
        - q: Partial query string
        - field: Field to autocomplete on (title, company_name)
        - limit: Maximum number of suggestions (default: 10)
        """
        query = request.query_params.get("q", "")
        field = request.query_params.get("field", "title")
        limit = int(request.query_params.get("limit", 10))
        
        if not query:
            return Response({
                "success": True,
                "data": [],
                "message": "",
                "errors": None,
            })
        
        # Emit SEARCH_PERFORMED event for autocomplete
        try:
            emit(
                event_type=SEARCH_PERFORMED,
                category="search",
                user=request.user if request.user.is_authenticated else None,
                target_type="search",
                target_id="autocomplete_api",
                data={"query": query, "field": field, "limit": limit},
                request=request,
            )
        except Exception:
            pass
        
        try:
            suggestions = search_service.autocomplete(
                query=query,
                field=field,
                limit=limit,
            )
            
            return Response({
                "success": True,
                "data": suggestions,
                "message": "",
                "errors": None,
            })
            
        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Autocomplete failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Search"])
class JobFacetsView(APIView):
    """
    GET /api/v1/search/facets/
    
    Get facet values for filtering.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """
        Get facet values.
        
        Query Parameters:
        - facets: Comma-separated list of facet fields
        - location: Filter by location
        - industry: Filter by industry
        """
        facets_param = request.query_params.get("facets")
        facets = None
        if facets_param:
            facets = [f.strip() for f in facets_param.split(",") if f.strip()]
        
        # Build filters
        filters: Dict[str, Any] = {}
        filter_fields = ["location", "industry"]
        for field in filter_fields:
            value = request.query_params.get(field)
            if value:
                filters[field] = value
        
        try:
            facet_data = search_service.get_facets(
                filters=filters,
                facet_fields=facets,
            )
            
            return Response({
                "success": True,
                "data": facet_data,
                "message": "",
                "errors": None,
            })
            
        except Exception as e:
            logger.error(f"Facets error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Facets failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Search"])
class SearchHealthView(APIView):
    """
    GET /api/v1/search/health/
    
    Check health of search backends.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """
        Check health of search backends.
        """
        try:
            health = search_service.health_check()
            
            return Response({
                "success": True,
                "data": health,
                "message": "",
                "errors": None,
            })
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Health check failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)