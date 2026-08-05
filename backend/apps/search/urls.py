"""
Search URL Configuration

This module defines the URL patterns for the search functionality.
"""

from django.urls import path
from apps.search.views import (
    JobSearchView,
    JobAutocompleteView,
    JobFacetsView,
    SearchHealthView,
    JobRecommendationsView,
    SimilarJobsView,
    TrainRecommendationModelView,
)

urlpatterns = [
    # Main search endpoint
    path("jobs/", JobSearchView.as_view(), name="search-jobs"),
    
    # Autocomplete endpoint
    path("autocomplete/", JobAutocompleteView.as_view(), name="search-autocomplete"),
    
    # Facets endpoint
    path("facets/", JobFacetsView.as_view(), name="search-facets"),
    
    # Health check endpoint
    path("health/", SearchHealthView.as_view(), name="search-health"),
    
    # Recommendation endpoints
    path("recommendations/", JobRecommendationsView.as_view(), name="search-recommendations"),
    path("similar-jobs/<str:job_uuid>/", SimilarJobsView.as_view(), name="search-similar-jobs"),
    path("train-recommendation-model/", TrainRecommendationModelView.as_view(), name="train-recommendation-model"),
]
