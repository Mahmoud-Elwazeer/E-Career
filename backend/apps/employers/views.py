"""
Employer Portal Views
Phase 3A: Employer self-service portal
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Q

from .models import EmployerProfile, JobPosting, JobApplication, KnockoutQuestion, CandidateRanking, TalentDiscovery, TalentPool, TalentPoolCandidate
from .serializers import (
    EmployerProfileSerializer,
    EmployerProfileWriteSerializer,
    JobPostingListSerializer,
    JobPostingDetailSerializer,
    JobPostingWriteSerializer,
    JobApplicationSerializer,
    JobApplicationDetailSerializer,
    EmployerRegistrationSerializer,
    KnockoutQuestionSerializer,
    KnockoutQuestionCreateSerializer,
    CandidateRankingSerializer,
    CandidateRankingUpdateSerializer,
    TalentDiscoverySerializer,
    TalentDiscoveryCreateSerializer,
    EmployerRankingRequestSerializer,
    EmployerRankingResponseSerializer,
    TalentPoolSerializer,
    TalentPoolDetailSerializer,
    TalentPoolCandidateSerializer,
    AddCandidateSerializer,
)
from .permissions import (
    IsEmployer,
    IsVerifiedEmployer,
    IsOwnerEmployer,
    CanPostJobs,
    CanViewApplicants,
)
from apps.events.emitter import emit
from apps.events.types import (
    EMPLOYER_JOB_POSTED,
    EMPLOYER_JOB_UPDATED,
    EMPLOYER_JOB_CLOSED,
    EMPLOYER_CANDIDATE_VIEWED,
    EMPLOYER_CANDIDATE_SHORTLISTED,
)


class EmployerRegistrationView(generics.CreateAPIView):
    """
    Register as an employer.
    POST /api/v1/employer/register/
    """
    serializer_class = EmployerRegistrationSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        from apps.jobs.models import Company

        company = Company.objects.get(id=serializer.validated_data['company_id'])

        employer = EmployerProfile.objects.create(
            user=self.request.user,
            company=company,
            job_title=serializer.validated_data.get('job_title', ''),
            phone=serializer.validated_data.get('phone', ''),
        )

        self.request.user.role = 'employer'
        self.request.user.save(update_fields=['role'])

        return employer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user already has employer profile
        if hasattr(request.user, 'employer_profile'):
            return Response(
                {'error': 'You already have an employer profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        employer = self.perform_create(serializer)
        
        return Response(
            {
                'message': 'Employer profile created. Awaiting verification.',
                'employer': EmployerProfileSerializer(employer).data
            },
            status=status.HTTP_201_CREATED
        )


class EmployerProfileViewSet(viewsets.ModelViewSet):
    """
    Employer profile management.
    
    GET /api/v1/employer/profile/ - Get employer profile
    PUT /api/v1/employer/profile/ - Update profile
    POST /api/v1/employer/profile/request_verification/ - Request verification
    """
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EmployerProfileWriteSerializer
        return EmployerProfileSerializer
    
    def get_object(self):
        """Always return the current user's employer profile"""
        return self.request.user.employer_profile
    
    def list(self, request):
        """Return the current user's employer profile"""
        try:
            profile = request.user.employer_profile
            serializer = EmployerProfileSerializer(profile)
            return Response(serializer.data)
        except EmployerProfile.DoesNotExist:
            return Response(
                {'error': 'Employer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def request_verification(self, request):
        """Request employer verification"""
        try:
            employer = request.user.employer_profile
        except EmployerProfile.DoesNotExist:
            return Response(
                {'error': 'Employer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if employer.is_verified:
            return Response(
                {'error': 'Already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # In a real system, this would trigger a notification to admins
        # For now, we just mark that they requested it
        # Admin will verify through Django admin
        
        return Response({
            'message': 'Verification request submitted. An admin will review your profile.',
            'status': 'pending'
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get employer statistics"""
        try:
            employer = request.user.employer_profile
        except EmployerProfile.DoesNotExist:
            return Response(
                {'error': 'Employer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get job posting stats
        job_stats = JobPosting.objects.filter(employer=employer).aggregate(
            total_jobs=Count('id'),
            active_jobs=Count('id', filter=Q(status='published')),
            draft_jobs=Count('id', filter=Q(status='draft')),
            pending_jobs=Count('id', filter=Q(status='pending_review')),
        )
        
        # Get application stats
        application_stats = JobApplication.objects.filter(
            job__employer_posting__employer=employer
        ).aggregate(
            total_applications=Count('id'),
            new_applications=Count('id', filter=Q(status='applied')),
            viewed_applications=Count('id', filter=Q(status='viewed')),
            shortlisted=Count('id', filter=Q(status='shortlisted')),
            rejected=Count('id', filter=Q(status='rejected')),
        )
        
        # Get total views and clicks
        engagement_stats = JobPosting.objects.filter(
            employer=employer
        ).aggregate(
            total_views=Sum('views_count'),
            total_clicks=Sum('clicks_count'),
        )
        
        return Response({
            'jobs': job_stats,
            'applications': application_stats,
            'engagement': engagement_stats,
            'is_verified': employer.is_verified,
        })


class JobPostingViewSet(viewsets.ModelViewSet):
    """
    Employer job posting management.
    
    GET /api/v1/employer/jobs/ - List employer's jobs
    POST /api/v1/employer/jobs/ - Create job post
    GET /api/v1/employer/jobs/{id}/ - Get job detail
    PUT /api/v1/employer/jobs/{id}/ - Update job
    DELETE /api/v1/employer/jobs/{id}/ - Delete job
    POST /api/v1/employer/jobs/{id}/publish/ - Submit for review
    POST /api/v1/employer/jobs/{id}/close/ - Close job
    GET /api/v1/employer/jobs/{id}/applicants/ - Get applicants
    """
    permission_classes = [IsAuthenticated, IsVerifiedEmployer]
    
    def get_queryset(self):
        return JobPosting.objects.filter(
            employer=self.request.user.employer_profile
        ).select_related('company', 'employer', 'employer__user')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return JobPostingListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return JobPostingWriteSerializer
        return JobPostingDetailSerializer
    
    def perform_create(self, serializer):
        from .domain_verification import verify_job_posting_url

        employer = self.request.user.employer_profile
        job_post = serializer.save(
            employer=employer,
            company=employer.company
        )

        # Run domain verification
        verification_result = verify_job_posting_url(job_post)

        # Store verification result in job posting metadata (if you have JSONField)
        # For now, it's just logged

        # Emit EMPLOYER_JOB_POSTED event
        try:
            emit(
                event_type=EMPLOYER_JOB_POSTED,
                category="employer",
                user=employer.user,
                target_type="job_posting",
                target_id=str(job_post.id),
                data={
                    "job_title": job_post.title,
                    "company": job_post.company.name,
                    "url_verified": verification_result['is_valid']
                },
                request=None,
            )
        except Exception:
            pass
    
    def perform_update(self, serializer):
        """Only allow updates if job is in draft status"""
        instance = serializer.instance
        if instance.status not in ['draft', 'rejected']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Can only edit draft or rejected jobs.')
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Submit job for admin review"""
        job_post = self.get_object()
        
        if job_post.status != 'draft':
            return Response(
                {'error': 'Only draft jobs can be submitted for review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required fields
        if not job_post.title or not job_post.description or not job_post.requirements:
            return Response(
                {'error': 'Please fill in all required fields (title, description, requirements)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not job_post.apply_url:
            return Response(
                {'error': 'Apply URL is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_post.status = 'pending_review'
        job_post.save()
        
        # TODO: Send notification to admin
        
        return Response({
            'message': 'Job submitted for review. You will be notified once it is approved.',
            'status': job_post.status
        })
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close job posting"""
        job_post = self.get_object()
        
        if job_post.status != 'published':
            return Response(
                {'error': 'Only published jobs can be closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_post.status = 'closed'
        job_post.save()
        
        # Emit EMPLOYER_JOB_CLOSED event
        try:
            emit(
                event_type=EMPLOYER_JOB_CLOSED,
                category="employer",
                user=job_post.employer.user,
                target_type="job_posting",
                target_id=str(job_post.id),
                data={"job_title": job_post.title, "company": job_post.company.name},
                request=None,
            )
        except Exception:
            pass
        
        # Update linked Job if exists
        if job_post.mirrored_job:
            job_post.mirrored_job.status = 'archived'
            job_post.mirrored_job.quality_state = 'archived'
            job_post.mirrored_job.save(update_fields=['status', 'quality_state'])
        
        return Response({
            'message': 'Job closed successfully',
            'status': job_post.status
        })
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen a closed job"""
        job_post = self.get_object()
        
        if job_post.status != 'closed':
            return Response(
                {'error': 'Only closed jobs can be reopened'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_post.status = 'draft'
        job_post.save()
        
        return Response({
            'message': 'Job reopened as draft. Submit for review to publish.',
            'status': job_post.status
        })
    
    @action(detail=True, methods=['get'])
    def applicants(self, request, pk=None):
        """Get applicants for this job"""
        job_post = self.get_object()
        
        applications = JobApplication.objects.filter(
            job=job_post.mirrored_job
        ).select_related('user').order_by('-applied_at')
        
        serializer = JobApplicationSerializer(
            applications,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'job_title': job_post.title,
            'total_applicants': applications.count(),
            'applicants': serializer.data
        })


class JobApplicationViewSet(viewsets.ModelViewSet):
    """
    Job application management (employer view).
    
    GET /api/v1/employer/applications/ - List all applications
    GET /api/v1/employer/applications/{id}/ - Get application detail
    PUT /api/v1/employer/applications/{id}/ - Update application status
    """
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated, IsVerifiedEmployer]
    
    def get_queryset(self):
        employer = self.request.user.employer_profile
        queryset = JobApplication.objects.filter(
            job__employer_posting__employer=employer
        ).select_related('user', 'job')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by job
        job_id = self.request.query_params.get('job_id')
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        
        return queryset.order_by('-applied_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobApplicationDetailSerializer
        return JobApplicationSerializer
    
    def update(self, request, *args, **kwargs):
        """Update application status"""
        application = self.get_object()
        
        # Mark as viewed if not already
        if application.status == 'applied':
            application.status = 'viewed'
            application.save()
            
            # Emit EMPLOYER_CANDIDATE_VIEWED event
            try:
                emit(
                    event_type=EMPLOYER_CANDIDATE_VIEWED,
                    category="employer",
                    user=application.job.employer.employer.user,
                    target_type="job_application",
                    target_id=str(application.id),
                    data={
                        "candidate_name": f"{application.user.first_name} {application.user.last_name}",
                        "candidate_email": application.user.email,
                        "job_title": application.job.title,
                    },
                    request=None,
                )
            except Exception:
                pass
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def shortlist(self, request, pk=None):
        """Shortlist an application"""
        application = self.get_object()
        application.status = 'shortlisted'
        application.save()
        
        # Emit EMPLOYER_CANDIDATE_SHORTLISTED event
        try:
            emit(
                event_type=EMPLOYER_CANDIDATE_SHORTLISTED,
                category="employer",
                user=application.job.employer.employer.user,
                target_type="job_application",
                target_id=str(application.id),
                data={
                    "candidate_name": f"{application.user.first_name} {application.user.last_name}",
                    "candidate_email": application.user.email,
                    "job_title": application.job.title,
                },
                request=None,
            )
        except Exception:
            pass
        
        return Response({
            'message': 'Application shortlisted',
            'status': application.status
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an application"""
        application = self.get_object()
        application.status = 'rejected'
        application.save()
        
        return Response({
            'message': 'Application rejected',
            'status': application.status
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def company_search(request):
    """
    Search for companies.
    GET /api/v1/employer/companies/search/?q=<query>
    Used in employer registration to find their company.
    """
    from apps.jobs.models import Company
    
    query = request.query_params.get('q', '')
    if len(query) < 2:
        return Response({'companies': []})
    
    companies = Company.objects.filter(
        name__icontains=query,
        is_active=True
    ).values('id', 'name', 'website', 'industry')[:10]
    
    return Response({
        'companies': list(companies)
    })


# ============================================================================
# Employer Intelligence Views (Phase 4)
# ============================================================================


class KnockoutQuestionViewSet(viewsets.ModelViewSet):
    """
    Knockout question management for employers.
    
    GET /api/v1/employer/knockout-questions/ - List questions
    POST /api/v1/employer/knockout-questions/ - Create question
    PUT /api/v1/employer/knockout-questions/{id}/ - Update question
    DELETE /api/v1/employer/knockout-questions/{id}/ - Delete question
    """
    permission_classes = [IsAuthenticated, IsVerifiedEmployer]
    
    def get_queryset(self):
        return KnockoutQuestion.objects.filter(
            employer=self.request.user.employer_profile
        )
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return KnockoutQuestionCreateSerializer
        return KnockoutQuestionSerializer
    
    def perform_create(self, serializer):
        serializer.save(employer=self.request.user.employer_profile)


class CandidateRankingViewSet(viewsets.ModelViewSet):
    """
    AI-powered candidate ranking for employers.
    
    GET /api/v1/employer/rankings/ - List rankings
    POST /api/v1/employer/rankings/rank/ - Rank candidates for a job
    PUT /api/v1/employer/rankings/{id}/ - Update ranking status
    """
    permission_classes = [IsAuthenticated, IsVerifiedEmployer]
    
    def get_queryset(self):
        return CandidateRanking.objects.filter(
            employer=self.request.user.employer_profile
        ).select_related('user', 'job')
    
    def get_serializer_class(self):
        if self.action == 'update':
            return CandidateRankingUpdateSerializer
        return CandidateRankingSerializer
    
    @action(detail=False, methods=['post'])
    def rank(self, request):
        """
        Rank candidates for a job.
        
        POST /api/v1/employer/rankings/rank/
        Body: {
            "job_id": 123,
            "candidate_ids": [1, 2, 3],
            "rank_all": false
        }
        """
        serializer = EmployerRankingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        job_id = serializer.validated_data['job_id']
        candidate_ids = serializer.validated_data.get('candidate_ids', [])
        rank_all = serializer.validated_data.get('rank_all', False)
        
        employer = self.request.user.employer_profile
        
        # Get job
        from apps.jobs.models import Job
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get candidates to rank
        if rank_all:
            # Rank all applicants for this job (applicants have implicitly consented)
            from apps.jobs.models import JobApplication
            candidates = JobApplication.objects.filter(
                job=job
            ).select_related('user').values_list('user_id', flat=True)
        else:
            # Filter to only discoverable users
            from apps.career.models import CareerProfile
            discoverable_ids = set(
                CareerProfile.objects.filter(
                    user_id__in=candidate_ids, is_discoverable=True
                ).values_list('user_id', flat=True)
            )
            candidates = [uid for uid in candidate_ids if uid in discoverable_ids]
        
        # Use AI ranking service
        from apps.employers.ranking_service import ranking_service
        rankings = ranking_service.rank_candidates(
            job_id=job.id,
            candidate_ids=list(candidates),
            employer=employer,
        )
        
        return Response({
            'job_id': job_id,
            'candidates_ranked': len(rankings),
            'rankings': rankings,
        })


class TalentDiscoveryViewSet(viewsets.ModelViewSet):
    """
    Talent discovery tracking for employers.
    
    GET /api/v1/employer/talent-discoveries/ - List discoveries
    POST /api/v1/employer/talent-discoveries/ - Create discovery
    """
    permission_classes = [IsAuthenticated, IsVerifiedEmployer]
    
    def get_queryset(self):
        from apps.career.models import CareerProfile
        discoverable_user_ids = CareerProfile.objects.filter(
            is_discoverable=True
        ).values_list('user_id', flat=True)
        return TalentDiscovery.objects.filter(
            employer=self.request.user.employer_profile,
            user_id__in=discoverable_user_ids
        ).select_related('user')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TalentDiscoveryCreateSerializer
        return TalentDiscoverySerializer

    def perform_create(self, serializer):
        from apps.career.models import CareerProfile
        user = serializer.validated_data.get('user')
        if user and not CareerProfile.objects.filter(user=user, is_discoverable=True).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError('This user has not opted in to employer discovery.')
        serializer.save(employer=self.request.user.employer_profile)


class TalentPoolViewSet(viewsets.ModelViewSet):
    """
    Talent Pool management for employers.

    list: GET /api/v1/employer/talent-pools/
    create: POST /api/v1/employer/talent-pools/
    retrieve: GET /api/v1/employer/talent-pools/{id}/
    update: PUT /api/v1/employer/talent-pools/{id}/
    destroy: DELETE /api/v1/employer/talent-pools/{id}/
    """
    permission_classes = [IsAuthenticated, IsVerifiedEmployer]

    def get_queryset(self):
        return TalentPool.objects.filter(
            employer=self.request.user.employer_profile
        ).annotate(candidate_count=Count('candidates'))

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TalentPoolDetailSerializer
        return TalentPoolSerializer

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user.employer_profile)

    @action(detail=True, methods=['post'])
    def add_candidate(self, request, pk=None):
        """Add a candidate to this pool (only discoverable users)."""
        pool = self.get_object()
        serializer = AddCandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.contrib.auth import get_user_model
        from apps.career.models import CareerProfile
        User = get_user_model()
        user = get_object_or_404(User, id=serializer.validated_data['user_id'])

        if not CareerProfile.objects.filter(user=user, is_discoverable=True).exists():
            return Response(
                {'error': 'This user has not opted in to employer discovery.'},
                status=status.HTTP_403_FORBIDDEN
            )

        candidate, created = TalentPoolCandidate.objects.get_or_create(
            pool=pool,
            user=user,
            defaults={
                'tags': serializer.validated_data.get('tags', []),
                'notes': serializer.validated_data.get('notes', ''),
                'source': serializer.validated_data.get('source', 'manual'),
            }
        )

        if not created:
            return Response(
                {'error': 'Candidate already in this pool'},
                status=status.HTTP_409_CONFLICT
            )

        return Response(
            TalentPoolCandidateSerializer(candidate).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'], url_path='remove-candidate/(?P<user_id>[0-9]+)')
    def remove_candidate(self, request, pk=None, user_id=None):
        """Remove a candidate from this pool."""
        pool = self.get_object()
        deleted, _ = TalentPoolCandidate.objects.filter(pool=pool, user_id=user_id).delete()
        if deleted == 0:
            return Response({'error': 'Candidate not in pool'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'], url_path='update-candidate/(?P<user_id>[0-9]+)')
    def update_candidate(self, request, pk=None, user_id=None):
        """Update candidate notes/tags/rating in this pool."""
        pool = self.get_object()
        candidate = get_object_or_404(TalentPoolCandidate, pool=pool, user_id=user_id)

        if 'tags' in request.data:
            candidate.tags = request.data['tags']
        if 'notes' in request.data:
            candidate.notes = request.data['notes']
        if 'rating' in request.data:
            candidate.rating = request.data['rating']
        candidate.save()

        return Response(TalentPoolCandidateSerializer(candidate).data)

    @action(detail=True, methods=['post'], url_path='rank')
    def rank_pool(self, request, pk=None):
        """Rank all candidates in this pool against a job."""
        pool = self.get_object()
        job_id = request.data.get('job_id')
        if not job_id:
            return Response(
                {'error': 'job_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        candidate_ids = list(
            TalentPoolCandidate.objects.filter(pool=pool)
            .values_list('user_id', flat=True)
        )
        if not candidate_ids:
            return Response({'rankings': [], 'candidates_ranked': 0})

        from apps.employers.ranking_service import ranking_service
        employer = request.user.employer_profile
        rankings = ranking_service.rank_candidates(
            job_id=int(job_id),
            candidate_ids=candidate_ids,
            employer=employer,
        )
        return Response({
            'pool_id': str(pool.uuid),
            'job_id': job_id,
            'candidates_ranked': len(rankings),
            'rankings': rankings,
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVerifiedEmployer])
def ats_gap_analysis(request, posting_id):
    """
    Analyze a job posting for ATS quality gaps.

    GET /api/v1/employer/postings/{id}/ats-analysis/
    """
    from .ats_gap_service import ats_gap_analyzer

    posting = get_object_or_404(
        JobPosting,
        id=posting_id,
        employer=request.user.employer_profile
    )
    analysis = ats_gap_analyzer.analyze(posting)
    return Response({'success': True, 'data': analysis})
