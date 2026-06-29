"""
Profile views for API endpoints
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.users.models import UserProfile, JobMatchScore
from apps.jobs.models import Job
from .serializers import (
    UserProfileSerializer, UserProfileUpdateSerializer,
    CVUploadSerializer, JobMatchScoreSerializer,
    ProfileCompletionSerializer, SkillsUpdateSerializer,
    PreferencesUpdateSerializer
)
from .services import MatchingService

logger = logging.getLogger(__name__)


class ProfileViewSet(viewsets.ModelViewSet):
    """
    User profile management

    GET /api/profile/ - Get current user profile
    PUT /api/profile/ - Update profile
    PATCH /api/profile/ - Partial update profile
    POST /api/profile/upload-cv/ - Upload and parse CV
    GET /api/profile/completion/ - Get profile completion status
    POST /api/profile/skills/ - Update skills manually
    POST /api/profile/preferences/ - Update job preferences
    GET /api/profile/matches/ - Get job matches for profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create profile for current user"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def list(self, request, *args, **kwargs):
        """Get current user's profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update profile"""
        profile = self.get_object()
        serializer = UserProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=kwargs.get('partial', False)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(profile).data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload_cv(self, request):
        """Upload and parse CV"""
        serializer = CVUploadSerializer(data=request.data)

        if serializer.is_valid():
            try:
                profile = serializer.save(user=request.user)
                return Response({
                    'status': 'success',
                    'message': 'CV uploaded and parsed successfully',
                    'profile': UserProfileSerializer(profile, context={'request': request}).data
                })
            except Exception as e:
                logger.error(f"CV upload failed: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def completion(self, request):
        """Get profile completion status"""
        profile = self.get_object()

        # Calculate completion by section
        sections = {
            'cv': {
                'complete': bool(profile.cv_file),
                'weight': 30,
                'label': 'CV Upload'
            },
            'skills': {
                'complete': bool(profile.skills and len(profile.skills) >= 5),
                'weight': 20,
                'label': 'Skills'
            },
            'experience': {
                'complete': bool(profile.experience_years and profile.experience_years > 0),
                'weight': 15,
                'label': 'Experience'
            },
            'education': {
                'complete': bool(profile.education and len(profile.education) > 0),
                'weight': 15,
                'label': 'Education'
            },
            'preferences': {
                'complete': bool(
                    (profile.desired_roles and len(profile.desired_roles) > 0) or
                    (profile.desired_locations and len(profile.desired_locations) > 0)
                ),
                'weight': 10,
                'label': 'Job Preferences'
            },
            'portfolio': {
                'complete': bool(profile.portfolio_url),
                'weight': 5,
                'label': 'Portfolio'
            },
            'languages': {
                'complete': bool(profile.languages and len(profile.languages) > 0),
                'weight': 5,
                'label': 'Languages'
            }
        }

        total_score = sum(
            section['weight'] for section in sections.values() if section['complete']
        )

        return Response({
            'total_score': min(total_score, 100),
            'is_complete': total_score >= 60,
            'sections': sections
        })

    @action(detail=False, methods=['post'])
    def skills(self, request):
        """Update skills manually"""
        profile = self.get_object()
        serializer = SkillsUpdateSerializer(data=request.data)

        if serializer.is_valid():
            profile.skills = serializer.validated_data['skills']
            profile.save(update_fields=['skills', 'updated_at'])
            return Response({
                'status': 'success',
                'skills': profile.skills
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def preferences(self, request):
        """Update job preferences"""
        profile = self.get_object()
        serializer = PreferencesUpdateSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            if 'desired_roles' in data:
                profile.desired_roles = data['desired_roles'] or []
            if 'desired_locations' in data:
                profile.desired_locations = data['desired_locations'] or []
            if 'preferred_type' in data:
                profile.preferred_type = data.get('preferred_type', '')
            if 'open_to_remote' in data:
                profile.open_to_remote = data['open_to_remote']
            if 'min_salary' in data:
                profile.min_salary = data.get('min_salary')
            if 'salary_currency' in data:
                profile.salary_currency = data.get('salary_currency', 'EGP')

            profile.save()
            return Response(UserProfileSerializer(profile).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def matches(self, request):
        """Get job matches for profile"""
        profile = self.get_object()

        # Get limit from query params
        limit = int(request.query_params.get('limit', 20))
        min_score = int(request.query_params.get('min_score', 50))

        # Get existing match scores
        matches = JobMatchScore.objects.filter(
            user=request.user,
            score__gte=min_score
        ).select_related('job', 'job__company').order_by('-score')[:limit]

        serializer = JobMatchScoreSerializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def calculate_matches(self, request):
        """Calculate match scores for all active jobs"""
        profile = self.get_object()

        if not profile.skills:
            return Response({
                'error': 'Profile must have skills to calculate matches'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get active jobs
        jobs = Job.objects.filter(is_active=True).select_related('company')

        matching_service = MatchingService()
        matches_created = 0

        for job in jobs[:100]:  # Limit to 100 jobs for performance
            try:
                score = matching_service.calculate_match_score(profile, job)
                breakdown = matching_service.get_match_breakdown(profile, job)

                JobMatchScore.objects.update_or_create(
                    user=request.user,
                    job=job,
                    defaults={
                        'score': int(score),
                        'breakdown': breakdown.get('components', {})
                    }
                )
                matches_created += 1
            except Exception as e:
                logger.warning(f"Failed to calculate match for job {job.id}: {e}")

        return Response({
            'status': 'success',
            'matches_calculated': matches_created
        })


class JobMatchViewSet(viewsets.ReadOnlyModelViewSet):
    """View job match scores"""

    serializer_class = JobMatchScoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobMatchScore.objects.filter(
            user=self.request.user
        ).select_related('job', 'job__company').order_by('-score')

    def retrieve(self, request, *args, **kwargs):
        """Get detailed match for a specific job"""
        match = self.get_object()

        # Get full breakdown
        profile = request.user.profile
        matching_service = MatchingService()
        breakdown = matching_service.get_match_breakdown(profile, match.job)

        return Response({
            'match': JobMatchScoreSerializer(match).data,
            'breakdown': breakdown
        })