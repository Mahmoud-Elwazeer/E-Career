"""
Career Intelligence Views

This module defines DRF views for career profile, skills, learning,
talent scoring, and interview features.
"""

import logging
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.skills.models import Skill, Occupation, OccupationSkill
from apps.jobs.models import Job
from apps.vectors.service import get_vector_service, JOBS_COLLECTION, USERS_COLLECTION

from .models import (
    CareerProfile,
    CareerUserSkill,
    CareerLearning,
    TalentScore,
    InterviewSession,
)
from .serializers import (
    CareerProfileSerializer,
    CareerProfileUpdateSerializer,
    CareerUserSkillSerializer,
    CareerUserSkillCreateSerializer,
    CareerLearningSerializer,
    TalentScoreSerializer,
    InterviewSessionSerializer,
    InterviewSessionCreateSerializer,
    ProfileCompletenessSerializer,
    SkillGapSerializer,
)

logger = logging.getLogger(__name__)


class CareerProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for CareerProfile model."""
    
    queryset = CareerProfile.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CareerProfile.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'update':
            return CareerProfileUpdateSerializer
        return CareerProfileSerializer
    
    def get_object(self):
        obj, _ = CareerProfile.objects.get_or_create(user=self.request.user)
        return obj
    
    def retrieve(self, request, *args, **kwargs):
        """Get or create career profile for the current user."""
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update career profile and recalculate completeness."""
        partial = kwargs.pop('partial', False)
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Recalculate completeness
        obj.update_completeness()
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_completeness(self, request, pk=None):
        """Manually trigger completeness score recalculation."""
        obj = self.get_object()
        result = obj.update_completeness()
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def skills(self, request, pk=None):
        """Get user's skills with proficiency levels."""
        obj = self.get_object()
        skills = CareerUserSkill.objects.filter(user=obj.user).select_related('skill')
        serializer = CareerUserSkillSerializer(skills, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_skill(self, request, pk=None):
        """Add a skill to the user's profile."""
        obj = self.get_object()
        serializer = CareerUserSkillCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        skill_id = serializer.validated_data['skill_id']
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        career_skill, created = CareerUserSkill.objects.get_or_create(
            user=obj.user,
            skill=skill,
            defaults={
                'proficiency': serializer.validated_data.get('proficiency', 'intermediate'),
                'years_experience': serializer.validated_data.get('years_experience', 0),
                'verified': serializer.validated_data.get('verified', False),
                'verification_source': serializer.validated_data.get('verification_source', ''),
                'source': serializer.validated_data.get('source', 'self_reported'),
                'confidence': serializer.validated_data.get('confidence', 0.5),
            }
        )
        
        if not created:
            for field in ['proficiency', 'years_experience', 'verified', 'verification_source', 'source', 'confidence']:
                if field in serializer.validated_data:
                    setattr(career_skill, field, serializer.validated_data[field])
            career_skill.save()
        
        obj.update_completeness()
        
        return Response(
            CareerUserSkillSerializer(career_skill).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['delete'])
    def remove_skill(self, request, pk=None):
        """Remove a skill from the user's profile."""
        obj = self.get_object()
        skill_id = request.data.get('skill_id')
        
        if not skill_id:
            return Response(
                {'error': 'skill_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return Response(
                {'error': 'Skill not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        CareerUserSkill.objects.filter(user=obj.user, skill=skill).delete()
        obj.update_completeness()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def learning(self, request, pk=None):
        """Get user's learning history."""
        obj = self.get_object()
        learning = CareerLearning.objects.filter(user=obj.user)
        serializer = CareerLearningSerializer(learning, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_learning(self, request, pk=None):
        """Add a learning entry to the user's profile."""
        obj = self.get_object()
        serializer = CareerLearningSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        learning = CareerLearning.objects.create(
            user=obj.user,
            **serializer.validated_data
        )
        
        return Response(
            CareerLearningSerializer(learning).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def talent_score(self, request, pk=None):
        """Get user's talent score."""
        obj = self.get_object()
        try:
            talent_score = TalentScore.objects.get(user=obj.user)
        except TalentScore.DoesNotExist:
            return Response(
                {'error': 'Talent score not calculated yet'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TalentScoreSerializer(talent_score)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def skill_gap(self, request, pk=None):
        """Get skill gap analysis for target roles."""
        obj = self.get_object()
        
        if not obj.target_roles:
            return Response(
                {'error': 'No target roles set'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the first target role for analysis
        target_role = obj.target_roles[0].get('role', '')
        
        # Find matching occupation
        occupations = Occupation.objects.filter(
            Q(name__icontains=target_role) | Q(name_ar__icontains=target_role)
        )[:5]
        
        if not occupations:
            return Response({
                'target_role': target_role,
                'missing_skills': [],
                'skill_importance': {},
                'learning_resources': [],
                'message': 'No matching occupation found. Please try a different role.',
            })
        
        # Get required skills for the occupation
        occupation = occupations[0]
        required_skills = OccupationSkill.objects.filter(
            occupation=occupation
        ).select_related('skill').order_by('-importance')[:20]
        
        # Get user's skills
        user_skills = CareerUserSkill.objects.filter(
            user=obj.user
        ).values_list('skill_id', flat=True)
        
        # Calculate gaps
        missing_skills = []
        skill_importance = {}
        
        for req_skill in required_skills:
            if req_skill.skill_id not in user_skills:
                missing_skills.append({
                    'skill_id': str(req_skill.skill.id),
                    'skill_name': req_skill.skill.name,
                    'importance': req_skill.importance,
                })
            skill_importance[str(req_skill.skill.id)] = req_skill.importance
        
        # Get learning resources (placeholder - would integrate with course API)
        learning_resources = [
            {
                'title': f'Learn {skill["skill_name"]}',
                'platform': 'Coursera',
                'url': f'https://coursera.org/search?query={skill["skill_name"]}',
                'difficulty': 'beginner' if skill['importance'] < 3 else 'intermediate',
            }
            for skill in missing_skills[:5]
        ]
        
        return Response({
            'target_role': target_role,
            'missing_skills': missing_skills,
            'skill_importance': skill_importance,
            'learning_resources': learning_resources,
            'total_required_skills': len(required_skills),
            'missing_count': len(missing_skills),
        })


class JobMatchingView(APIView):
    """Semantic job matching endpoint using vector similarity."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get jobs matching user's profile using vector similarity.
        
        - Generates user embedding from profile
        - Queries Qdrant for similar jobs
        - Filters by user preferences
        - Returns top-N matches with similarity scores
        """
        try:
            # Get user's career profile
            try:
                profile = CareerProfile.objects.get(user=request.user)
            except CareerProfile.DoesNotExist:
                return Response(
                    {'error': 'Career profile not found. Please complete your profile first.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get user preferences
            user_preferences = {
                'locations': [loc.get('city') for loc in profile.target_locations if loc.get('city')],
                'salary_min': profile.target_salary_min,
                'open_to_remote': profile.open_to_remote,
                'min_match_score': profile.min_match_score,
            }
            
            # Get vector service
            vector_service = get_vector_service()
            
            # Generate user embedding
            profile_text = profile.get_profile_text()
            if not profile_text.strip():
                return Response(
                    {'error': 'Profile is not complete enough for matching. Please add more information.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate embedding using vector service
            embeddings = vector_service.generate_embeddings([profile_text], input_type="search_query")
            if not embeddings:
                return Response(
                    {'error': 'Failed to generate embedding'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            user_embedding = embeddings[0]
            
            # Search jobs using vector service
            results = vector_service.semantic_search(
                collection=JOBS_COLLECTION,
                query_text=profile_text,
                limit=20,
                filters={
                    'trust_score': {'gte': 0.4},
                    'open_to_remote': user_preferences.get('open_to_remote', True),
                }
            )
            
            # Format results
            matches = []
            for result in results.results:
                matches.append({
                    'job_id': result.payload.get('job_id'),
                    'title': result.payload.get('title'),
                    'company': result.payload.get('company'),
                    'location': result.payload.get('location'),
                    'similarity_score': result.score,
                })
            
            return Response({
                'user_profile_id': str(profile.id),
                'match_count': len(matches),
                'matches': matches,
            })
            
        except Exception as e:
            logger.error(f"Job matching error: {e}")
            return Response(
                {'error': 'Failed to perform job matching'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoalSettingView(APIView):
    """Goal setting API for career profiles."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Set or update career goals.
        
        - Set target role, salary, location, timeline
        - Emit GoalSet / GoalUpdated events
        """
        profile, created = CareerProfile.objects.get_or_create(user=request.user)
        
        # Update profile with goal data
        target_roles = request.data.get('target_roles', [])
        target_locations = request.data.get('target_locations', [])
        target_salary_min = request.data.get('target_salary_min')
        timeline = request.data.get('timeline')
        
        if target_roles:
            profile.target_roles = target_roles
        if target_locations:
            profile.target_locations = target_locations
        if target_salary_min is not None:
            profile.target_salary_min = target_salary_min
        
        profile.save()
        
        # Emit event (placeholder - would integrate with event system)
        event_data = {
            'event_type': 'GoalSet' if created else 'GoalUpdated',
            'user_id': str(request.user.id),
            'timestamp': timezone.now().isoformat(),
            'goals': {
                'roles': target_roles,
                'locations': target_locations,
                'salary_min': target_salary_min,
                'timeline': timeline,
            }
        }
        
        return Response({
            'success': True,
            'message': 'Goals updated successfully',
            'event': event_data,
            'profile': CareerProfileSerializer(profile).data,
        })


class SkillGapAnalysisView(APIView):
    """Skill gap analysis endpoint."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get skill gap analysis for a specific target role.
        
        - Query: what skills does target_role require?
        - Compare: user has vs role needs
        - Return: missing skills + importance + learning resources
        """
        target_role = request.query_params.get('role', '')
        
        if not target_role:
            return Response(
                {'error': 'role parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            profile = CareerProfile.objects.get(user=request.user)
        except CareerProfile.DoesNotExist:
            return Response(
                {'error': 'Career profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find matching occupation
        occupations = Occupation.objects.filter(
            Q(name__icontains=target_role) | Q(name_ar__icontains=target_role)
        )[:5]
        
        if not occupations:
            return Response({
                'target_role': target_role,
                'missing_skills': [],
                'skill_importance': {},
                'learning_resources': [],
                'message': 'No matching occupation found. Please try a different role.',
            })
        
        # Get required skills for the occupation
        occupation = occupations[0]
        required_skills = OccupationSkill.objects.filter(
            occupation=occupation
        ).select_related('skill').order_by('-importance')[:20]
        
        # Get user's skills
        user_skills = CareerUserSkill.objects.filter(
            user=profile.user
        ).values_list('skill_id', flat=True)
        
        # Calculate gaps
        missing_skills = []
        skill_importance = {}
        
        for req_skill in required_skills:
            if req_skill.skill_id not in user_skills:
                missing_skills.append({
                    'skill_id': str(req_skill.skill.id),
                    'skill_name': req_skill.skill.name,
                    'importance': req_skill.importance,
                    'level_required': 'expert' if req_skill.importance >= 4 else 'advanced',
                })
            skill_importance[str(req_skill.skill.id)] = {
                'importance': req_skill.importance,
                'level_required': 'expert' if req_skill.importance >= 4 else 'advanced',
            }
        
        # Get learning resources (placeholder - would integrate with course API)
        learning_resources = [
            {
                'skill_id': skill['skill_id'],
                'skill_name': skill['skill_name'],
                'title': f'Learn {skill["skill_name"]}',
                'platform': 'Coursera',
                'url': f'https://coursera.org/search?query={skill["skill_name"]}',
                'difficulty': 'beginner' if skill['importance'] < 3 else 'intermediate',
                'estimated_hours': int(skill['importance'] * 10),
            }
            for skill in missing_skills[:10]
        ]
        
        return Response({
            'target_role': target_role,
            'target_occupation': occupation.name,
            'missing_skills': missing_skills,
            'skill_importance': skill_importance,
            'learning_resources': learning_resources,
            'total_required_skills': len(required_skills),
            'missing_count': len(missing_skills),
            'user_skills_count': len(user_skills),
        })


class ProfileCompletenessView(APIView):
    """Profile completeness calculator endpoint."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get profile completeness score and missing fields."""
        try:
            profile = CareerProfile.objects.get(user=request.user)
        except CareerProfile.DoesNotExist:
            return Response({
                'score': 0.0,
                'missing_fields': ['target_roles', 'target_locations', 'experience_years', 'current_role'],
                'total_fields': 12,
                'completed_fields': 0,
            })
        
        result = profile.update_completeness()
        return Response(result)


class TalentScoreView(APIView):
    """Talent score calculation endpoint."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get or calculate talent score for the user."""
        try:
            profile = CareerProfile.objects.get(user=request.user)
        except CareerProfile.DoesNotExist:
            return Response(
                {'error': 'Career profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        talent_score, created = TalentScore.objects.get_or_create(user=request.user)
        
        # Calculate scores based on profile data
        self._calculate_scores(talent_score, profile)
        
        serializer = TalentScoreSerializer(talent_score)
        return Response(serializer.data)
    
    def _calculate_scores(self, talent_score, profile):
        """Calculate talent scores based on profile data."""
        # Skill score (based on verified skills and proficiency)
        verified_skills = CareerUserSkill.objects.filter(
            user=profile.user, verified=True
        ).count()
        total_skills = CareerUserSkill.objects.filter(user=profile.user).count()
        
        if total_skills > 0:
            skill_score = min(1.0, (verified_skills / max(total_skills, 1)) * 0.7 + (total_skills / 20) * 0.3)
        else:
            skill_score = 0.0
        
        # Experience score (based on experience_years)
        experience_score = min(1.0, profile.experience_years / 15)
        
        # Education score (placeholder - would parse education from CV)
        education_score = 0.5  # Default
        
        # Portfolio score (based on portfolio_url and github_data)
        portfolio_score = 0.0
        if profile.portfolio_url:
            portfolio_score += 0.5
        if profile.github_data:
            portfolio_score += 0.5
        
        # Interview score (placeholder - would use interview sessions)
        interview_score = 0.0
        
        # Growth score (based on learning history)
        learning_count = CareerLearning.objects.filter(user=profile.user).count()
        growth_score = min(1.0, learning_count / 10)
        
        # Communication score (placeholder - would analyze CV text)
        communication_score = 0.5
        
        # Calculate overall score
        overall_score = (
            skill_score * 0.30 +
            experience_score * 0.25 +
            education_score * 0.15 +
            portfolio_score * 0.10 +
            interview_score * 0.10 +
            growth_score * 0.05 +
            communication_score * 0.05
        )
        
        # Update talent score
        talent_score.skill_score = skill_score
        talent_score.experience_score = experience_score
        talent_score.education_score = education_score
        talent_score.portfolio_score = portfolio_score
        talent_score.interview_score = interview_score
        talent_score.growth_score = growth_score
        talent_score.communication_score = communication_score
        talent_score.overall_score = overall_score
        talent_score.ai_confidence = 0.7
        talent_score.save()


class InterviewSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for InterviewSession model."""
    
    queryset = InterviewSession.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return InterviewSession.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return InterviewSessionCreateSerializer
        return InterviewSessionSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)