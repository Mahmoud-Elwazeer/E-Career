"""
Skills URL Configuration

This module defines the URL patterns for the skill taxonomy.
"""

from django.urls import path, include
from apps.skills.views import (
    SkillListView,
    SkillDetailView,
    SkillHierarchyView,
    SkillSearchView,
    RelatedSkillsView,
    OccupationListView,
    OccupationDetailView,
    OccupationWithSkillsView,
    OccupationSearchView,
    CareerPathListView,
    CareerPathDetailView,
    CareerPathsFromOccupationView,
)

urlpatterns = [
    # Skills
    path("skills/", SkillListView.as_view(), name="skill-list"),
    path("skills/<int:id>/", SkillDetailView.as_view(), name="skill-detail"),
    path("skills/hierarchy/", SkillHierarchyView.as_view(), name="skill-hierarchy"),
    path("skills/search/", SkillSearchView.as_view(), name="skill-search"),
    path("skills/<int:skill_id>/related/", RelatedSkillsView.as_view(), name="related-skills"),
    
    # Occupations
    path("occupations/", OccupationListView.as_view(), name="occupation-list"),
    path("occupations/<int:id>/", OccupationDetailView.as_view(), name="occupation-detail"),
    path("occupations/<int:occupation_id>/skills/", OccupationWithSkillsView.as_view(), name="occupation-skills"),
    path("occupations/search/", OccupationSearchView.as_view(), name="occupation-search"),
    
    # Career Paths
    path("career-paths/", CareerPathListView.as_view(), name="career-path-list"),
    path("career-paths/<int:id>/", CareerPathDetailView.as_view(), name="career-path-detail"),
    path("occupations/<int:occupation_id>/career-paths/", CareerPathsFromOccupationView.as_view(), name="occupation-career-paths"),
    
    # Knowledge Graph
    path("", include("apps.skills.graph_urls")),
]
