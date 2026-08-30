> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# PHASE 3A: Employer Portal

> **Dependencies:** Phase 1A complete  
> **Duration:** 4-5 hours  
> **Status:** Ready for GLM execution

---

## 🎯 Objectives

Implement employer self-service portal:
- Employer registration and verification
- Job posting management (CRUD)
- Applicant tracking
- Company profile management
- URL validation for employer-posted jobs

---

## 🔧 Implementation

### Step 1: Employer Models

**File:** `backend/employers/models.py`

```python
from django.db import models
from django.contrib.auth import get_user_model
from jobs.models import Company, Job
import uuid

User = get_user_model()

class EmployerProfile(models.Model):
    """Employer user profile"""
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employer_profiles')
    
    # Verification
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="Your position at the company")
    
    # Company email verification
    work_email = models.EmailField(help_text="Official company email for verification")
    work_email_verified = models.BooleanField(default=False)
    
    # Permissions
    can_post_jobs = models.BooleanField(default=False)
    can_view_applicants = models.BooleanField(default=True)
    can_edit_company = models.BooleanField(default=False)
    
    # Stats
    jobs_posted = models.IntegerField(default=0)
    total_applicants = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['verification_status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} @ {self.company.name}"
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'


class EmployerJobPost(models.Model):
    """Employer-created job posting"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('closed', 'Closed'),
    ]
    
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='job_posts')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='employer_post', null=True, blank=True)
    
    # Job Details
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    
    # Classification
    category = models.ForeignKey('jobs.Category', on_delete=models.SET_NULL, null=True)
    location = models.CharField(max_length=255)
    workplace_type = models.CharField(max_length=20, choices=Job.WORKPLACE_CHOICES)
    employment_type = models.CharField(max_length=20, choices=Job.EMPLOYMENT_CHOICES)
    experience_level = models.CharField(max_length=20, choices=Job.EXPERIENCE_CHOICES)
    
    # Salary
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='EGP')
    salary_period = models.CharField(max_length=10, default='month')
    
    # Application
    apply_url = models.URLField(help_text="Direct application URL (must be company domain)")
    application_email = models.EmailField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Review
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_jobs')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Metadata
    view_count = models.IntegerField(default=0)
    application_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employer', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} @ {self.employer.company.name}"
    
    def save(self, *args, **kwargs):
        # Validate apply_url matches company domain
        if self.apply_url:
            from urllib.parse import urlparse
            url_domain = urlparse(self.apply_url).netloc
            company_domain = urlparse(self.employer.company.website).netloc if self.employer.company.website else None
            
            if company_domain and company_domain not in url_domain:
                raise ValueError("Apply URL must be on company domain")
        
        super().save(*args, **kwargs)


class JobApplication(models.Model):
    """Track applications to employer jobs"""
    
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('viewed', 'Viewed by Employer'),
        ('shortlisted', 'Shortlisted'),
        ('interviewed', 'Interviewed'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    job_post = models.ForeignKey(EmployerJobPost, on_delete=models.CASCADE, related_name='applications')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    cover_letter = models.TextField(blank=True)
    
    # Employer notes
    employer_notes = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True, help_text="Employer rating 1-5")
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'job_post']
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['job_post', 'status']),
            models.Index(fields=['user', '-applied_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} → {self.job_post.title}"
```

### Step 2: Serializers

**File:** `backend/employers/serializers.py`

```python
from rest_framework import serializers
from .models import EmployerProfile, EmployerJobPost, JobApplication
from jobs.serializers import CompanySerializer, CategorySerializer

class EmployerProfileSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    
    class Meta:
        model = EmployerProfile
        fields = [
            'id', 'company', 'phone', 'position', 'work_email',
            'work_email_verified', 'verification_status',
            'can_post_jobs', 'can_view_applicants', 'can_edit_company',
            'jobs_posted', 'total_applicants', 'created_at'
        ]
        read_only_fields = [
            'work_email_verified', 'verification_status',
            'can_post_jobs', 'can_view_applicants', 'can_edit_company',
            'jobs_posted', 'total_applicants'
        ]


class EmployerJobPostSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    
    class Meta:
        model = EmployerJobPost
        fields = [
            'id', 'title', 'description', 'requirements', 'responsibilities',
            'benefits', 'category', 'category_id', 'location', 'workplace_type',
            'employment_type', 'experience_level', 'salary_min', 'salary_max',
            'salary_currency', 'salary_period', 'apply_url', 'application_email',
            'status', 'expires_at', 'view_count', 'application_count',
            'company', 'created_at', 'updated_at', 'rejection_reason'
        ]
        read_only_fields = [
            'status', 'view_count', 'application_count', 'created_at',
            'updated_at', 'rejection_reason'
        ]
    
    def get_company(self, obj):
        return CompanySerializer(obj.employer.company).data
    
    def validate_apply_url(self, value):
        """Validate apply URL is on company domain"""
        from urllib.parse import urlparse
        
        employer = self.context['request'].user.employer_profile
        company_website = employer.company.website
        
        if not company_website:
            raise serializers.ValidationError(
                "Company website must be set before posting jobs"
            )
        
        url_domain = urlparse(value).netloc
        company_domain = urlparse(company_website).netloc
        
        if company_domain not in url_domain:
            raise serializers.ValidationError(
                f"Apply URL must be on company domain ({company_domain})"
            )
        
        return value


class JobApplicationSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job_post.title', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'user', 'job_post', 'job_title', 'status',
            'cover_letter', 'employer_notes', 'rating',
            'applied_at', 'viewed_at', 'updated_at'
        ]
        read_only_fields = ['applied_at', 'viewed_at']
    
    def get_user(self, obj):
        """Return user profile info (respecting privacy)"""
        profile = obj.user.userprofile
        return {
            'id': obj.user.id,
            'name': obj.user.get_full_name(),
            'email': obj.user.email,
            'phone': profile.phone if profile else None,
            'location': profile.location if profile else None,
            'current_position': profile.current_position if profile else None,
            'years_of_experience': profile.years_of_experience if profile else None,
            'cv_url': profile.cv_file.url if profile and profile.cv_file else None,
        }
```

### Step 3: Views

**File:** `backend/employers/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import EmployerProfile, EmployerJobPost, JobApplication
from .serializers import (
    EmployerProfileSerializer,
    EmployerJobPostSerializer,
    JobApplicationSerializer
)
from .permissions import IsEmployer, IsVerifiedEmployer

class EmployerProfileViewSet(viewsets.ModelViewSet):
    """
    Employer profile management
    
    GET /api/employer/profile/ - Get employer profile
    PUT /api/employer/profile/ - Update profile
    POST /api/employer/profile/request-verification/ - Request verification
    """
    serializer_class = EmployerProfileSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        return self.request.user.employer_profile
    
    @action(detail=False, methods=['post'])
    def request_verification(self, request):
        """Request employer verification"""
        employer = request.user.employer_profile
        
        if employer.verification_status == 'verified':
            return Response(
                {'error': 'Already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        employer.verification_status = 'pending'
        employer.save()
        
        # TODO: Send notification to admin
        
        return Response({
            'message': 'Verification request submitted',
            'status': employer.verification_status
        })


class EmployerJobPostViewSet(viewsets.ModelViewSet):
    """
    Employer job posting management
    
    GET /api/employer/jobs/ - List employer's jobs
    POST /api/employer/jobs/ - Create job post
    GET /api/employer/jobs/{id}/ - Get job detail
    PUT /api/employer/jobs/{id}/ - Update job
    DELETE /api/employer/jobs/{id}/ - Delete job
    POST /api/employer/jobs/{id}/publish/ - Submit for review
    POST /api/employer/jobs/{id}/close/ - Close job
    """
    serializer_class = EmployerJobPostSerializer
    permission_classes = [IsAuthenticated, IsVerifiedEmployer]
    
    def get_queryset(self):
        return EmployerJobPost.objects.filter(
            employer=self.request.user.employer_profile
        )
    
    def perform_create(self, serializer):
        serializer.save(employer=self.request.user.employer_profile)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Submit job for admin review"""
        job_post = self.get_object()
        
        if job_post.status != 'draft':
            return Response(
                {'error': 'Only draft jobs can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job_post.status = 'pending_review'
        job_post.save()
        
        # TODO: Notify admin
        
        return Response({
            'message': 'Job submitted for review',
            'status': job_post.status
        })
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close job posting"""
        job_post = self.get_object()
        
        job_post.status = 'closed'
        job_post.save()
        
        # Update linked Job if exists
        if job_post.job:
            job_post.job.is_active = False
            job_post.job.save()
        
        return Response({
            'message': 'Job closed successfully',
            'status': job_post.status
        })
    
    @action(detail=True, methods=['get'])
    def applicants(self, request, pk=None):
        """Get applicants for this job"""
        job_post = self.get_object()
        
        applications = JobApplication.objects.filter(job_post=job_post)
        serializer = JobApplicationSerializer(applications, many=True)
        
        return Response(serializer.data)


class JobApplicationViewSet(viewsets.ModelViewSet):
    """
    Job application management (employer view)
    
    GET /api/employer/applications/ - List all applications
    GET /api/employer/applications/{id}/ - Get application detail
    PUT /api/employer/applications/{id}/ - Update application status
    """
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated, IsVerifiedEmployer]
    
    def get_queryset(self):
        employer = self.request.user.employer_profile
        return JobApplication.objects.filter(
            job_post__employer=employer
        ).select_related('user', 'job_post')
    
    def update(self, request, *args, **kwargs):
        """Update application status"""
        application = self.get_object()
        
        # Mark as viewed if not already
        if not application.viewed_at:
            application.viewed_at = timezone.now()
        
        return super().update(request, *args, **kwargs)
```

### Step 4: Permissions

**File:** `backend/employers/permissions.py`

```python
from rest_framework import permissions

class IsEmployer(permissions.BasePermission):
    """Check if user has employer profile"""
    
    def has_permission(self, request, view):
        return hasattr(request.user, 'employer_profile')


class IsVerifiedEmployer(permissions.BasePermission):
    """Check if employer is verified"""
    
    def has_permission(self, request, view):
        if not hasattr(request.user, 'employer_profile'):
            return False
        
        return request.user.employer_profile.is_verified and \
               request.user.employer_profile.can_post_jobs
```

### Step 5: Admin Approval Interface

**File:** `backend/employers/admin.py`

```python
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import EmployerProfile, EmployerJobPost, JobApplication

@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'verification_status', 'work_email_verified', 'jobs_posted', 'created_at']
    list_filter = ['verification_status', 'work_email_verified', 'can_post_jobs']
    search_fields = ['user__email', 'company__name', 'work_email']
    
    actions = ['approve_employers', 'reject_employers']
    
    def approve_employers(self, request, queryset):
        queryset.update(
            verification_status='verified',
            can_post_jobs=True,
            verified_at=timezone.now()
        )
    approve_employers.short_description = "Approve selected employers"
    
    def reject_employers(self, request, queryset):
        queryset.update(verification_status='rejected', can_post_jobs=False)
    reject_employers.short_description = "Reject selected employers"


@admin.register(EmployerJobPost)
class EmployerJobPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer_company', 'status', 'application_count', 'created_at']
    list_filter = ['status', 'workplace_type', 'employment_type']
    search_fields = ['title', 'employer__company__name']
    
    actions = ['approve_jobs', 'reject_jobs']
    
    def employer_company(self, obj):
        return obj.employer.company.name
    
    def approve_jobs(self, request, queryset):
        from jobs.models import Job
        
        for job_post in queryset.filter(status='pending_review'):
            # Create Job from EmployerJobPost
            job = Job.objects.create(
                title=job_post.title,
                company=job_post.employer.company,
                description=job_post.description,
                requirements=job_post.requirements,
                responsibilities=job_post.responsibilities,
                benefits=job_post.benefits,
                location=job_post.location,
                workplace_type=job_post.workplace_type,
                employment_type=job_post.employment_type,
                experience_level=job_post.experience_level,
                salary_min=job_post.salary_min,
                salary_max=job_post.salary_max,
                apply_url=job_post.apply_url,
                is_active=True,
                is_legitimate=True,
                legitimacy_score=100
            )
            
            job_post.job = job
            job_post.status = 'published'
            job_post.reviewed_by = request.user
            job_post.reviewed_at = timezone.now()
            job_post.save()
    
    approve_jobs.short_description = "Approve and publish selected jobs"
    
    def reject_jobs(self, request, queryset):
        queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
    reject_jobs.short_description = "Reject selected jobs"


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_post', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['user__email', 'job_post__title']
```

---

## 🎨 Frontend Implementation

### Step 6: Employer Dashboard

**File:** `frontend/src/pages/employer/EmployerDashboard.jsx`

```jsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Briefcase, Users, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const EmployerDashboard = () => {
  const { data: profile } = useQuery({
    queryKey: ['employer-profile'],
    queryFn: async () => {
      const response = await axios.get('/api/employer/profile/');
      return response.data;
    }
  });

  const { data: jobs } = useQuery({
    queryKey: ['employer-jobs'],
    queryFn: async () => {
      const response = await axios.get('/api/employer/jobs/');
      return response.data;
    }
  });

  if (!profile?.is_verified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow max-w-md text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Verification Pending
          </h2>
          <p className="text-gray-600 mb-6">
            Your employer account is pending verification. We'll notify you once approved.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Employer Dashboard</h1>
            <p className="text-gray-600 mt-2">{profile.company.name}</p>
          </div>
          
          <Link
            to="/employer/jobs/new"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Post New Job
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <Briefcase className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{profile.jobs_posted}</p>
                <p className="text-gray-600">Active Jobs</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-50 rounded-lg">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{profile.total_applicants}</p>
                <p className="text-gray-600">Total Applicants</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-50 rounded-lg">
                <Eye className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {jobs?.reduce((sum, job) => sum + job.view_count, 0) || 0}
                </p>
                <p className="text-gray-600">Total Views</p>
              </div>
            </div>
          </div>
        </div>

        {/* Jobs List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900">Your Job Postings</h2>
          </div>
          
          <div className="divide-y">
            {jobs?.map(job => (
              <Link
                key={job.id}
                to={`/employer/jobs/${job.id}`}
                className="block p-6 hover:bg-gray-50 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                    <p className="text-gray-600 mt-1">{job.location} • {job.workplace_type}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span>{job.application_count} applicants</span>
                      <span>{job.view_count} views</span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <span className={`
                      px-3 py-1 rounded-full text-sm font-medium
                      ${job.status === 'published' ? 'bg-green-100 text-green-800' : ''}
                      ${job.status === 'pending_review' ? 'bg-yellow-100 text-yellow-800' : ''}
                      ${job.status === 'draft' ? 'bg-gray-100 text-gray-800' : ''}
                    `}>
                      {job.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
            
            {jobs?.length === 0 && (
              <div className="p-12 text-center text-gray-500">
                No jobs posted yet. Create your first job posting!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployerDashboard;
```

---

## ✅ Phase 3A Verification

### Tests

```bash
# Test employer registration
curl -X POST http://localhost:8000/api/employer/register/ \
  -d '{"company_name": "Tech Corp", "work_email": "hr@techcorp.com"}'

# Test job creation
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/employer/jobs/ \
  -d '{"title": "Senior Developer", "apply_url": "https://techcorp.com/careers/apply"}'

# Test application listing
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/employer/applications/
```

### Success Criteria

- [ ] Employers can register and verify
- [ ] Job posting works with validation
- [ ] Apply URL must match company domain
- [ ] Admin can approve/reject jobs
- [ ] Applicant tracking works
- [ ] Employer dashboard displays stats

---

**Phase 3A Complete! ✅**
Proceed to Phase 3B: Recommendations
