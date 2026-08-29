"""
Profile views for API endpoints.

Uses CareerProfile as the canonical model (UserProfile is deprecated).
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.career.models import CareerProfile
from apps.users.models import JobMatchScore
from apps.jobs.models import Job
from apps.jobs.serializers import JobListSerializer
from .serializers import (
    UserProfileSerializer, UserProfileUpdateSerializer,
    CVUploadSerializer, JobMatchScoreSerializer,
    ProfileCompletionSerializer, SkillsUpdateSerializer,
    PreferencesUpdateSerializer
)
from .services import MatchingService, matching_service
from apps.events.emitter import emit
from apps.events.types import USER_PROFILE_UPDATED

logger = logging.getLogger(__name__)


class ProfileViewSet(viewsets.ModelViewSet):
    """
    User profile management (backed by CareerProfile).

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
        return CareerProfile.objects.filter(user=self.request.user)

    def get_object(self):
        profile, created = CareerProfile.objects.get_or_create(user=self.request.user)
        return profile

    def list(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = UserProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=kwargs.get('partial', False)
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(profile, serializer.validated_data)
        try:
            emit(
                event_type=USER_PROFILE_UPDATED,
                category="user",
                user=request.user,
                target_type="user",
                target_id=str(profile.uuid),
                data={"source": "profile_view", "fields": list(request.data.keys())},
                request=request,
            )
        except Exception:
            pass
        return Response(UserProfileSerializer(profile).data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload_cv(self, request):
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
        profile = self.get_object()
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
                    (profile.target_roles and len(profile.target_roles) > 0) or
                    (profile.target_locations and len(profile.target_locations) > 0)
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
        profile = self.get_object()
        serializer = SkillsUpdateSerializer(data=request.data)
        if serializer.is_valid():
            profile.skills = serializer.validated_data['skills']
            profile.save(update_fields=['skills', 'updated_at'])
            try:
                emit(
                    event_type=USER_PROFILE_UPDATED,
                    category="user",
                    user=request.user,
                    target_type="user",
                    target_id=str(profile.uuid),
                    data={"source": "profile_skills_view", "fields": ["skills"]},
                    request=request,
                )
            except Exception:
                pass
            return Response({
                'status': 'success',
                'skills': profile.skills
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def preferences(self, request):
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
            try:
                emit(
                    event_type=USER_PROFILE_UPDATED,
                    category="user",
                    user=request.user,
                    target_type="user",
                    target_id=str(profile.uuid),
                    data={"source": "profile_preferences_view", "fields": list(data.keys())},
                    request=request,
                )
            except Exception:
                pass
            return Response(UserProfileSerializer(profile).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def matches(self, request):
        profile = self.get_object()
        limit = int(request.query_params.get('limit', 20))
        min_score = int(request.query_params.get('min_score', 50))
        matches = JobMatchScore.objects.filter(
            user=request.user,
            score__gte=min_score
        ).select_related('job', 'job__company').order_by('-score')[:limit]
        serializer = JobMatchScoreSerializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def calculate_matches(self, request):
        profile = self.get_object()
        if not profile.skills:
            return Response({
                'error': 'Profile must have skills to calculate matches'
            }, status=status.HTTP_400_BAD_REQUEST)

        jobs = Job.objects.filter(status='active').select_related('company')
        matching_svc = MatchingService()
        matches_created = 0

        for job in jobs[:100]:
            try:
                score = matching_svc.calculate_match_score(profile, job)
                breakdown = matching_svc.get_match_breakdown(profile, job)
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
    serializer_class = JobMatchScoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobMatchScore.objects.filter(
            user=self.request.user
        ).select_related('job', 'job__company').order_by('-score')

    def retrieve(self, request, *args, **kwargs):
        match = self.get_object()
        profile, _ = CareerProfile.objects.get_or_create(user=request.user)
        matching_svc = MatchingService()
        breakdown = matching_svc.get_match_breakdown(profile, match.job)
        return Response({
            'match': JobMatchScoreSerializer(match).data,
            'breakdown': breakdown
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_recommendations(request):
    """GET /api/recommendations/?limit=20&min_score=60"""
    try:
        profile, _ = CareerProfile.objects.get_or_create(user=request.user)

        if not profile.skills or len(profile.skills) < 3:
            return Response({
                'error': 'Please add at least 3 skills to your profile to get recommendations',
                'completion_url': '/app/profile'
            }, status=status.HTTP_400_BAD_REQUEST)

        limit = int(request.query_params.get('limit', 20))
        min_score = float(request.query_params.get('min_score', 60))

        recommendations = matching_service.get_recommended_jobs(
            profile=profile,
            limit=limit,
            min_score=min_score
        )

        results = []
        for rec in recommendations:
            job_data = JobListSerializer(
                rec['job'],
                context={'request': request}
            ).data
            results.append({
                'job': job_data,
                'match_score': rec['score'],
                'reasoning': rec['reasoning']
            })

        return Response({
            'count': len(results),
            'recommendations': results
        })

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_match_breakdown(request, job_id):
    """GET /api/jobs/{job_id}/match-breakdown/"""
    try:
        profile, _ = CareerProfile.objects.get_or_create(user=request.user)
        job = Job.objects.get(id=job_id)
        breakdown = matching_service.get_match_breakdown(profile, job)
        return Response(breakdown)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting match breakdown: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_similar_jobs(request, job_id):
    """GET /api/jobs/{job_id}/similar/"""
    try:
        job = Job.objects.get(id=job_id)
        similar_jobs = matching_service.get_similar_jobs(job, limit=5)
        jobs_data = JobListSerializer(
            similar_jobs,
            many=True,
            context={'request': request}
        ).data
        return Response({
            'count': len(jobs_data),
            'jobs': jobs_data
        })
    except Job.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting similar jobs: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
