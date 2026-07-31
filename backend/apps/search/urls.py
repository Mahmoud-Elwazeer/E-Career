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
]