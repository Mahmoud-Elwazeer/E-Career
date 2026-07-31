"""
Vector Search API Views

Semantic search, similar jobs, and hybrid search endpoints.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.vectors.service import get_vector_service, JOBS_COLLECTION
from apps.search.services import search_service

logger = logging.getLogger(__name__)


@extend_schema(tags=["Vector Search"])
class SemanticSearchView(APIView):
    """
    GET /api/v1/search/semantic/

    Semantic job search using natural language queries.
    Powered by Cohere Embed v3 + Qdrant vector database.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="q", description="Natural language search query", required=True, type=str),
            OpenApiParameter(name="limit", description="Max results (default: 20)", type=int),
            OpenApiParameter(name="threshold", description="Minimum similarity score (0-1)", type=float),
            OpenApiParameter(name="location", description="Filter by location", type=str),
            OpenApiParameter(name="experience_level", description="Filter by experience level", type=str),
            OpenApiParameter(name="employment_type", description="Filter by employment type", type=str),
            OpenApiParameter(name="salary_min", description="Minimum salary", type=int),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        Semantic search for jobs using natural language.

        Query Parameters:
        - q: Natural language query (required)
        - limit: Max results (default: 20)
        - threshold: Minimum similarity score (default: None)
        - location, experience_level, employment_type, salary_min: Filters
        """
        query = request.query_params.get("q", "")
        limit = int(request.query_params.get("limit", 20))
        threshold = request.query_params.get("threshold")
        if threshold:
            threshold = float(threshold)

        if not query:
            return Response({
                "success": False,
                "data": None,
                "message": "Query parameter 'q' is required",
                "errors": {"q": "This field is required"},
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build filters
        filters = {}
        filter_fields = ["location", "experience_level", "employment_type"]
        for field in filter_fields:
            value = request.query_params.get(field)
            if value:
                filters[field] = value

        # Salary filter
        salary_min = request.query_params.get("salary_min")
        if salary_min:
            filters["salary_min"] = {"gte": int(salary_min)}

        # Trust score filter (mandatory)
        filters["trust_score"] = {"gte": 0.4}

        try:
            vector_service = get_vector_service()

            # Semantic search
            results = vector_service.semantic_search(
                collection=JOBS_COLLECTION,
                query_text=query,
                limit=limit,
                score_threshold=threshold,
                filters=filters,
            )

            # Convert to response format
            jobs = []
            for result in results.results:
                jobs.append({
                    "id": result.payload.get("job_id"),
                    "title": result.payload.get("title"),
                    "company": result.payload.get("company"),
                    "location": result.payload.get("location"),
                    "employment_type": result.payload.get("employment_type"),
                    "experience_level": result.payload.get("experience_level"),
                    "salary_min": result.payload.get("salary_min"),
                    "salary_max": result.payload.get("salary_max"),
                    "similarity_score": result.score,
                })

            return Response({
                "success": True,
                "data": {
                    "jobs": jobs,
                    "total": results.total,
                    "query_time_ms": results.query_time_ms,
                    "search_type": "semantic",
                },
                "message": "",
                "errors": None,
            })

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Semantic search failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Vector Search"])
class SimilarJobsView(APIView):
    """
    GET /api/v1/jobs/{job_id}/similar/

    Find jobs similar to a specific job using vector similarity.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="limit", description="Max results (default: 10)", type=int),
            OpenApiParameter(name="threshold", description="Minimum similarity score (0-1)", type=float),
        ],
    )
    def get(self, request, job_id, *args, **kwargs):
        """
        Find similar jobs by vector similarity.

        Path Parameters:
        - job_id: ID of reference job

        Query Parameters:
        - limit: Max results (default: 10)
        - threshold: Minimum similarity score
        """
        limit = int(request.query_params.get("limit", 10))
        threshold = request.query_params.get("threshold")
        if threshold:
            threshold = float(threshold)

        try:
            vector_service = get_vector_service()

            # Find similar jobs
            filters = {"trust_score": {"gte": 0.4}}

            results = vector_service.similar_items(
                collection=JOBS_COLLECTION,
                item_id=str(job_id),
                limit=limit,
                score_threshold=threshold,
                filters=filters,
            )

            # Convert to response format
            jobs = []
            for result in results.results:
                jobs.append({
                    "id": result.payload.get("job_id"),
                    "title": result.payload.get("title"),
                    "company": result.payload.get("company"),
                    "location": result.payload.get("location"),
                    "employment_type": result.payload.get("employment_type"),
                    "similarity_score": result.score,
                })

            return Response({
                "success": True,
                "data": {
                    "similar_jobs": jobs,
                    "total": results.total,
                    "query_time_ms": results.query_time_ms,
                },
                "message": "",
                "errors": None,
            })

        except Exception as e:
            logger.error(f"Similar jobs error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Similar jobs search failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Vector Search"])
class HybridSearchView(APIView):
    """
    GET /api/v1/search/hybrid/

    Hybrid search combining keyword (Typesense) and semantic (Qdrant) search.
    Uses Reciprocal Rank Fusion (RRF) to merge results.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="q", description="Search query", required=True, type=str),
            OpenApiParameter(name="limit", description="Max results (default: 20)", type=int),
            OpenApiParameter(name="keyword_weight", description="Weight for keyword results (0-1, default: 0.5)", type=float),
            OpenApiParameter(name="semantic_weight", description="Weight for semantic results (0-1, default: 0.5)", type=float),
            OpenApiParameter(name="location", description="Filter by location", type=str),
            OpenApiParameter(name="experience_level", description="Filter by experience level", type=str),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        Hybrid search combining keyword and semantic search.

        Uses Reciprocal Rank Fusion (RRF) algorithm to merge results.

        Query Parameters:
        - q: Search query (required)
        - limit: Max results (default: 20)
        - keyword_weight: Weight for keyword search (default: 0.5)
        - semantic_weight: Weight for semantic search (default: 0.5)
        - Standard filters: location, experience_level, etc.
        """
        query = request.query_params.get("q", "")
        limit = int(request.query_params.get("limit", 20))
        keyword_weight = float(request.query_params.get("keyword_weight", 0.5))
        semantic_weight = float(request.query_params.get("semantic_weight", 0.5))

        if not query:
            return Response({
                "success": False,
                "data": None,
                "message": "Query parameter 'q' is required",
                "errors": {"q": "This field is required"},
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build filters
        filters = {}
        for field in ["location", "experience_level", "employment_type"]:
            value = request.query_params.get(field)
            if value:
                filters[field] = value

        try:
            # 1. Keyword search (Typesense)
            keyword_results = search_service.search(
                query=query,
                filters=filters,
                page=1,
                page_size=limit,
            )

            # 2. Semantic search (Qdrant)
            vector_service = get_vector_service()
            vector_filters = {k: v for k, v in filters.items()}
            vector_filters["trust_score"] = {"gte": 0.4}

            semantic_results = vector_service.semantic_search(
                collection=JOBS_COLLECTION,
                query_text=query,
                limit=limit,
                filters=vector_filters,
            )

            # 3. Reciprocal Rank Fusion (RRF)
            rrf_scores = {}
            k = 60  # RRF constant

            # Score keyword results
            for rank, hit in enumerate(keyword_results.get("hits", []), start=1):
                job_id = hit.get("id")
                rrf_scores[job_id] = rrf_scores.get(job_id, 0) + keyword_weight / (k + rank)

            # Score semantic results
            for rank, result in enumerate(semantic_results.results, start=1):
                job_id = result.payload.get("job_id")
                rrf_scores[job_id] = rrf_scores.get(job_id, 0) + semantic_weight / (k + rank)

            # Sort by RRF score
            ranked_job_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:limit]

            # Fetch full job details (simplified - in production, batch query jobs)
            merged_jobs = []
            for job_id in ranked_job_ids:
                # Find job in either result set
                job_data = None

                for hit in keyword_results.get("hits", []):
                    if hit.get("id") == job_id:
                        job_data = hit
                        break

                if not job_data:
                    for result in semantic_results.results:
                        if result.payload.get("job_id") == job_id:
                            job_data = result.payload
                            break

                if job_data:
                    merged_jobs.append({
                        **job_data,
                        "rrf_score": rrf_scores[job_id],
                    })

            return Response({
                "success": True,
                "data": {
                    "jobs": merged_jobs,
                    "total": len(merged_jobs),
                    "search_type": "hybrid",
                    "keyword_count": len(keyword_results.get("hits", [])),
                    "semantic_count": len(semantic_results.results),
                },
                "message": "",
                "errors": None,
            })

        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Hybrid search failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Vector Search"])
class VectorHealthView(APIView):
    """
    GET /api/v1/vectors/health/

    Check health of vector search components.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Check health of vector and embedding services."""
        try:
            vector_service = get_vector_service()
            health = vector_service.health_check()

            return Response({
                "success": True,
                "data": health,
                "message": "",
                "errors": None,
            })

        except Exception as e:
            logger.error(f"Vector health check error: {e}")
            return Response({
                "success": False,
                "data": None,
                "message": "Health check failed",
                "errors": {"detail": str(e)},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
