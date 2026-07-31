"""
Knowledge Graph URL Configuration

This module defines the URL patterns for the skill knowledge graph.
"""

from django.urls import path
from apps.skills.graph_views import (
    RelatedSkillsView,
    SkillPathView,
    SkillDistanceView,
    SkillHierarchyView,
    OccupationSkillsView,
    CareerPathsView,
)

urlpatterns = [
    # Related skills
    path("graph/skills/<int:skill_id>/related/", RelatedSkillsView.as_view(), name="graph-related-skills"),
    
    # Skill paths
    path("graph/skills/<int:skill_id>/path/<int:to_skill_id>/", SkillPathView.as_view(), name="graph-skill-path"),
    
    # Skill distance
    path("graph/skills/<int:skill_id>/distance/<int:to_skill_id>/", SkillDistanceView.as_view(), name="graph-skill-distance"),
    
    # Skill hierarchy
    path("graph/skills/<int:skill_id>/hierarchy/", SkillHierarchyView.as_view(), name="graph-skill-hierarchy"),
    
    # Occupation skills
    path("graph/occupations/<int:occupation_id>/skills/", OccupationSkillsView.as_view(), name="graph-occupation-skills"),
    
    # Career paths
    path("graph/occupations/<int:occupation_id>/career-paths/", CareerPathsView.as_view(), name="graph-career-paths"),
]