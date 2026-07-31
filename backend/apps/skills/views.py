"""
Skills API Views

This module contains the Django REST Framework views for the skill taxonomy.
"""

import logging
from typing import Any, Dict, List, Optional
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.skills.models import Skill, SkillRelationship, Occupation, OccupationSkill, CareerPath
from apps.skills.serializers import (
    SkillSerializer,
    SkillWriteSerializer,
    SkillRelationshipSerializer,
    OccupationSerializer,
    OccupationSkillSerializer,
    CareerPathSerializer,
    SkillHierarchySerializer,
    OccupationWithSkillsSerializer,
)

logger = logging.getLogger(__name__)


# ── Skill Views ──────────────────────────────────────────────────────────────────

@extend_schema(tags=["Skills"])
class SkillListView(generics.ListCreateAPIView):
    """GET /api/v1/skills/ — List skills. POST — Create (admin)."""
    
    queryset = Skill.objects.all().order_by("name")
    serializer_class = SkillSerializer
    pagination_class = None  # Return all skills for taxonomy browsing
    filter_backends = []
    
    def get_permissions(self):
        if self.request.method == "POST":
            from apps.core.permissions import IsAdminRole
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(tags=["Skills"])
class SkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/skills/<id>/ — Skill detail."""
    
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    lookup_field = "id"
    
    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            from apps.core.permissions import IsAdminRole
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(tags=["Skills"])
class SkillHierarchyView(APIView):
    """GET /api/v1/skills/hierarchy/ — Get skill hierarchy tree."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """Get skill hierarchy as a tree structure."""
        top_level_skills = Skill.objects.filter(parent__isnull=True).order_by("name")
        serializer = SkillHierarchySerializer(top_level_skills, many=True)
        return Response({
            "success": True,
            "data": serializer.data,
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Skills"])
class SkillSearchView(APIView):
    """GET /api/v1/skills/search/ — Search skills by name."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """Search skills by name."""
        query = request.query_params.get("q", "")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        
        if not query:
            return Response({
                "success": True,
                "data": {"results": [], "total": 0, "page": page, "page_size": page_size},
                "message": "",
                "errors": None,
            })
        
        # Search by name (case-insensitive)
        skills = Skill.objects.filter(name__icontains=query).order_by("name")
        total = skills.count()
        
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = SkillSerializer(skills[start:end], many=True)
        
        return Response({
            "success": True,
            "data": {"results": serializer.data, "total": total, "page": page, "page_size": page_size},
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Skills"])
class RelatedSkillsView(APIView):
    """GET /api/v1/skills/<id>/related/ — Get related skills."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, skill_id, *args, **kwargs):
        """Get skills related to the given skill."""
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return Response({
                "success": False,
                "data": None,
                "message": "Skill not found",
                "errors": None,
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get skills related through relationships
        outgoing = SkillRelationship.objects.filter(from_skill=skill).select_related("to_skill")
        incoming = SkillRelationship.objects.filter(to_skill=skill).select_related("from_skill")
        
        related_skills = []
        for rel in outgoing:
            related_skills.append({
                "id": rel.to_skill.id,
                "name": rel.to_skill.name,
                "relationship_type": rel.relationship_type,
                "weight": rel.weight,
            })
        for rel in incoming:
            related_skills.append({
                "id": rel.from_skill.id,
                "name": rel.from_skill.name,
                "relationship_type": f"incoming_{rel.relationship_type}",
                "weight": rel.weight,
            })
        
        return Response({
            "success": True,
            "data": {
                "skill_id": skill.id,
                "skill_name": skill.name,
                "related_skills": related_skills,
            },
            "message": "",
            "errors": None,
        })


# ── Occupation Views ─────────────────────────────────────────────────────────────

@extend_schema(tags=["Occupations"])
class OccupationListView(generics.ListCreateAPIView):
    """GET /api/v1/occupations/ — List occupations. POST — Create (admin)."""
    
    queryset = Occupation.objects.all().order_by("name")
    serializer_class = OccupationSerializer
    pagination_class = None
    filter_backends = []
    
    def get_permissions(self):
        if self.request.method == "POST":
            from apps.core.permissions import IsAdminRole
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(tags=["Occupations"])
class OccupationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/occupations/<id>/ — Occupation detail."""
    
    queryset = Occupation.objects.all()
    serializer_class = OccupationSerializer
    lookup_field = "id"
    
    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            from apps.core.permissions import IsAdminRole
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(tags=["Occupations"])
class OccupationWithSkillsView(APIView):
    """GET /api/v1/occupations/<id>/skills/ — Get occupation with required skills."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, occupation_id, *args, **kwargs):
        """Get occupation with its required skills."""
        try:
            occupation = Occupation.objects.get(id=occupation_id)
        except Occupation.DoesNotExist:
            return Response({
                "success": False,
                "data": None,
                "message": "Occupation not found",
                "errors": None,
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OccupationWithSkillsSerializer(occupation)
        return Response({
            "success": True,
            "data": serializer.data,
            "message": "",
            "errors": None,
        })


@extend_schema(tags=["Occupations"])
class OccupationSearchView(APIView):
    """GET /api/v1/occupations/search/ — Search occupations by name."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """Search occupations by name."""
        query = request.query_params.get("q", "")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        
        if not query:
            return Response({
                "success": True,
                "data": {"results": [], "total": 0, "page": page, "page_size": page_size},
                "message": "",
                "errors": None,
            })
        
        occupations = Occupation.objects.filter(name__icontains=query).order_by("name")
        total = occupations.count()
        
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = OccupationSerializer(occupations[start:end], many=True)
        
        return Response({
            "success": True,
            "data": {"results": serializer.data, "total": total, "page": page, "page_size": page_size},
            "message": "",
            "errors": None,
        })


# ── Career Path Views ────────────────────────────────────────────────────────────

@extend_schema(tags=["Career Paths"])
class CareerPathListView(generics.ListCreateAPIView):
    """GET /api/v1/career-paths/ — List career paths. POST — Create (admin)."""
    
    queryset = CareerPath.objects.all().order_by("from_occupation__name")
    serializer_class = CareerPathSerializer
    pagination_class = None
    filter_backends = []
    
    def get_permissions(self):
        if self.request.method == "POST":
            from apps.core.permissions import IsAdminRole
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(tags=["Career Paths"])
class CareerPathDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/career-paths/<id>/ — Career path detail."""
    
    queryset = CareerPath.objects.all()
    serializer_class = CareerPathSerializer
    lookup_field = "id"
    
    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            from apps.core.permissions import IsAdminRole
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(tags=["Career Paths"])
class CareerPathsFromOccupationView(APIView):
    """GET /api/v1/occupations/<id>/career-paths/ — Get career paths from an occupation."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, occupation_id, *args, **kwargs):
        """Get career paths starting from the given occupation."""
        try:
            occupation = Occupation.objects.get(id=occupation_id)
        except Occupation.DoesNotExist:
            return Response({
                "success": False,
                "data": None,
                "message": "Occupation not found",
                "errors": None,
            }, status=status.HTTP_404_NOT_FOUND)
        
        career_paths = CareerPath.objects.filter(from_occupation=occupation).select_related("to_occupation")
        serializer = CareerPathSerializer(career_paths, many=True)
        
        return Response({
            "success": True,
            "data": {
                "occupation_id": occupation.id,
                "occupation_name": occupation.name,
                "career_paths": serializer.data,
            },
            "message": "",
            "errors": None,
        })