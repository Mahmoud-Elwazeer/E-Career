"""
Graph API Views

This module contains the Django REST Framework views for the skill knowledge graph.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from apps.skills.graph import SkillGraph

logger = logging.getLogger(__name__)


@extend_schema(tags=["Knowledge Graph"])
class RelatedSkillsView(APIView):
    """GET /api/v1/graph/skills/<id>/related/ — Get related skills."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, skill_id, *args, **kwargs):
        """Get skills related to the given skill."""
        graph = SkillGraph()
        related_skills = graph.find_related_skills(skill_id)
        return Response({
            "success": True,
            "data": related_skills,
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Knowledge Graph"])
class SkillPathView(APIView):
    """GET /api/v1/graph/skills/<id>/path/<to_id>/ — Get paths between skills."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, skill_id, to_skill_id, *args, **kwargs):
        """Get paths between two skills."""
        graph = SkillGraph()
        paths = graph.find_skill_path(skill_id, to_skill_id)
        return Response({
            "success": True,
            "data": paths,
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Knowledge Graph"])
class SkillDistanceView(APIView):
    """GET /api/v1/graph/skills/<id>/distance/<to_id>/ — Get distance between skills."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, skill_id, to_skill_id, *args, **kwargs):
        """Get shortest path distance between two skills."""
        graph = SkillGraph()
        distance = graph.get_skill_distance(skill_id, to_skill_id)
        return Response({
            "success": True,
            "data": {
                "skill_id_1": skill_id,
                "skill_id_2": to_skill_id,
                "distance": distance,
            },
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Knowledge Graph"])
class SkillHierarchyView(APIView):
    """GET /api/v1/graph/skills/<id>/hierarchy/ — Get skill hierarchy."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, skill_id, *args, **kwargs):
        """Get the full hierarchy path for a skill."""
        graph = SkillGraph()
        hierarchy = graph.get_skill_hierarchy(skill_id)
        return Response({
            "success": True,
            "data": hierarchy,
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Knowledge Graph"])
class OccupationSkillsView(APIView):
    """GET /api/v1/graph/occupations/<id>/skills/ — Get skills for an occupation."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, occupation_id, *args, **kwargs):
        """Get all skills required for an occupation."""
        graph = SkillGraph()
        skills = graph.get_occupation_skills(occupation_id)
        return Response({
            "success": True,
            "data": skills,
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Knowledge Graph"])
class CareerPathsView(APIView):
    """GET /api/v1/graph/occupations/<id>/career-paths/ — Get career paths."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, occupation_id, *args, **kwargs):
        """Get all career paths from an occupation."""
        graph = SkillGraph()
        paths = graph.get_career_paths(occupation_id)
        return Response({
            "success": True,
            "data": paths,
            "message": "",
            "errors": None,
        })