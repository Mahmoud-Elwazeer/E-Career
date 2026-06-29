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

from .models import EmployerProfile, JobPosting, JobApplication
from .serializers import (
    EmployerProfileSerializer,
    EmployerProfileWriteSerializer,
    JobPostingListSerializer,
    JobPostingDetailSerializer,
    JobPostingWriteSerializer,
    JobApplicationSerializer,
    JobApplicationDetailSerializer,
    EmployerRegistrationSerializer,
)
from .permissions import (
    IsEmployer,
    IsVerifiedEmployer,
    IsOwnerEmployer,
    CanPostJobs,
    CanViewApplicants,
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
            job__employer=employer
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
        employer = self.request.user.employer_profile
        serializer.save(
            employer=employer,
            company=employer.company
        )
    
    def perform_update(self, serializer):
        """Only allow updates if job is in draft status"""
        instance = self.get_object()
        if instance.status not in ['draft', 'rejected']:
            return Response(
                {'error': 'Can only edit draft or rejected jobs'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().perform_update(serializer)
    
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
        
        # Update linked Job if exists
        if job_post.mirrored_job:
            job_post.mirrored_job.status = 'archived'
            job_post.mirrored_job.save()
        
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
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def shortlist(self, request, pk=None):
        """Shortlist an application"""
        application = self.get_object()
        application.status = 'shortlisted'
        application.save()
        
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