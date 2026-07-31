"""
Vector Search URL Configuration
"""

from django.urls import path
from .views import (
    SemanticSearchView,
    SimilarJobsView,
    HybridSearchView,
    VectorHealthView,
)

app_name = "vectors"

urlpatterns = [
    path("search/semantic/", SemanticSearchView.as_view(), name="semantic_search"),
    path("search/hybrid/", HybridSearchView.as_view(), name="hybrid_search"),
    path("jobs/<uuid:job_id>/similar/", SimilarJobsView.as_view(), name="similar_jobs"),
    path("health/", VectorHealthView.as_view(), name="health"),
]
