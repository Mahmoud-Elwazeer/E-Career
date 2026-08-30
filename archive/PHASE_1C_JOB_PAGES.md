# PHASE 1C: Job Pages Enhancement

> **Dependencies:** Phase 1A, Phase 1B complete  
> **Duration:** 3-4 hours  
> **Status:** Ready for GLM execution

---

## 🎯 Objectives

Enhance job listing and detail pages with:
- Advanced search and filtering
- Job match percentage display (when user has profile)
- Responsive design improvements
- "Ask Rashid about this job" quick action
- Salary transparency
- Company insights
- Direct apply button prominence

---

## 📦 Dependencies

### Backend
```bash
# Already installed from previous phases
pip install django-filter django-cors-headers
```

### Frontend
```bash
cd frontend
npm install @tanstack/react-query axios react-router-dom zustand
npm install lucide-react clsx tailwind-merge
```

---

## 🔧 Implementation

### Step 1: Enhanced Job Serializer

**File:** `backend/jobs/serializers.py`

```python
from rest_framework import serializers
from django.contrib.humanize.templatetags.humanize import naturaltime
from .models import Job, Company, Source, Category, JobApplication
from profiles.models import UserProfile
from profiles.services import MatchingService

class CompanySerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'logo_url', 'website',
            'industry', 'size', 'location', 'description'
        ]
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
        return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['id', 'name', 'icon', 'type']


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job listings"""
    company = CompanySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    source = SourceSerializer(read_only=True)
    match_score = serializers.SerializerMethodField()
    is_applied = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    posted_ago = serializers.SerializerMethodField()
    salary_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'slug', 'title', 'company', 'category', 'source',
            'location', 'workplace_type', 'employment_type',
            'experience_level', 'salary_display', 'posted_date',
            'posted_ago', 'is_featured', 'match_score', 'is_applied',
            'is_saved', 'is_legitimate', 'legitimacy_score'
        ]
    
    def get_match_score(self, obj):
        """Calculate job match percentage for authenticated users"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            profile = request.user.userprofile
            if not profile.is_complete:
                return None
            
            # Calculate match score (will use Rashid in Phase 2A)
            matcher = MatchingService()
            score = matcher.calculate_match_score(profile, obj)
            return round(score, 1)
        except UserProfile.DoesNotExist:
            return None
    
    def get_is_applied(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return JobApplication.objects.filter(user=request.user, job=obj).exists()
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.saved_by.filter(id=request.user.id).exists()
    
    def get_posted_ago(self, obj):
        return naturaltime(obj.posted_date)
    
    def get_salary_display(self, obj):
        if not obj.salary_min and not obj.salary_max:
            return "Not specified"
        
        currency = obj.salary_currency or 'EGP'
        period = obj.salary_period or 'month'
        
        if obj.salary_min and obj.salary_max:
            return f"{currency} {obj.salary_min:,.0f} - {obj.salary_max:,.0f}/{period}"
        elif obj.salary_min:
            return f"{currency} {obj.salary_min:,.0f}+/{period}"
        elif obj.salary_max:
            return f"Up to {currency} {obj.salary_max:,.0f}/{period}"
        return "Not specified"


class JobDetailSerializer(serializers.ModelSerializer):
    """Full serializer for job detail page"""
    company = CompanySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    source = SourceSerializer(read_only=True)
    match_score = serializers.SerializerMethodField()
    match_breakdown = serializers.SerializerMethodField()
    is_applied = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    posted_ago = serializers.SerializerMethodField()
    salary_display = serializers.SerializerMethodField()
    similar_jobs = serializers.SerializerMethodField()
    total_applicants = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'slug', 'title', 'company', 'category', 'source',
            'description', 'requirements', 'responsibilities',
            'benefits', 'location', 'workplace_type', 'employment_type',
            'experience_level', 'education_level', 'salary_display',
            'salary_min', 'salary_max', 'salary_currency', 'salary_period',
            'posted_date', 'posted_ago', 'expires_at', 'apply_url',
            'skills_required', 'languages_required', 'is_featured',
            'is_legitimate', 'legitimacy_score', 'legitimacy_flags',
            'match_score', 'match_breakdown', 'is_applied', 'is_saved',
            'similar_jobs', 'total_applicants', 'view_count'
        ]
    
    def get_match_score(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            profile = request.user.userprofile
            if not profile.is_complete:
                return None
            
            matcher = MatchingService()
            score = matcher.calculate_match_score(profile, obj)
            return round(score, 1)
        except UserProfile.DoesNotExist:
            return None
    
    def get_match_breakdown(self, obj):
        """Detailed breakdown of match score"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            profile = request.user.userprofile
            if not profile.is_complete:
                return None
            
            matcher = MatchingService()
            breakdown = matcher.get_match_breakdown(profile, obj)
            return breakdown
        except UserProfile.DoesNotExist:
            return None
    
    def get_is_applied(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return JobApplication.objects.filter(user=request.user, job=obj).exists()
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.saved_by.filter(id=request.user.id).exists()
    
    def get_posted_ago(self, obj):
        return naturaltime(obj.posted_date)
    
    def get_salary_display(self, obj):
        if not obj.salary_min and not obj.salary_max:
            return "Not specified"
        
        currency = obj.salary_currency or 'EGP'
        period = obj.salary_period or 'month'
        
        if obj.salary_min and obj.salary_max:
            return f"{currency} {obj.salary_min:,.0f} - {obj.salary_max:,.0f}/{period}"
        elif obj.salary_min:
            return f"{currency} {obj.salary_min:,.0f}+/{period}"
        elif obj.salary_max:
            return f"Up to {currency} {obj.salary_max:,.0f}/{period}"
        return "Not specified"
    
    def get_similar_jobs(self, obj):
        """Get 5 similar jobs based on category and skills"""
        similar = Job.objects.filter(
            is_active=True,
            category=obj.category
        ).exclude(
            id=obj.id
        ).order_by('-posted_date')[:5]
        
        return JobListSerializer(
            similar,
            many=True,
            context=self.context
        ).data
```

### Step 2: Enhanced Job ViewSet

**File:** `backend/jobs/views.py`

```python
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import timedelta

from .models import Job, Company, Category, Source, JobApplication
from .serializers import JobListSerializer, JobDetailSerializer
from .filters import JobFilter

class JobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Job listing and detail endpoints
    
    GET /api/jobs/ - List jobs with filters
    GET /api/jobs/{slug}/ - Job detail
    POST /api/jobs/{slug}/save/ - Save job
    POST /api/jobs/{slug}/unsave/ - Unsave job
    POST /api/jobs/{slug}/apply/ - Track application
    GET /api/jobs/{slug}/ask-rashid/ - Get Rashid analysis
    """
    queryset = Job.objects.filter(is_active=True).select_related(
        'company', 'category', 'source'
    ).prefetch_related('skills_required', 'languages_required')
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'description', 'company__name', 'location']
    ordering_fields = ['posted_date', 'salary_min', 'view_count']
    ordering = ['-posted_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobDetailSerializer
        return JobListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Annotate with applicant count
        queryset = queryset.annotate(
            total_applicants=Count('applications', distinct=True)
        )
        
        # Filter by legitimacy (hide scams unless explicitly requested)
        if not self.request.query_params.get('show_all'):
            queryset = queryset.filter(is_legitimate=True)
        
        # If user is authenticated, personalize results
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.userprofile
                if profile.is_complete:
                    # Boost jobs matching user's preferences
                    if profile.preferred_locations:
                        queryset = queryset.annotate(
                            location_match=Count('id', filter=Q(
                                location__in=profile.preferred_locations
                            ))
                        ).order_by('-location_match', '-posted_date')
            except:
                pass
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Get job detail and increment view count"""
        instance = self.get_object()
        
        # Increment view count (async task in production)
        instance.view_count = F('view_count') + 1
        instance.save(update_fields=['view_count'])
        instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def save(self, request, slug=None):
        """Save job to user's saved jobs"""
        job = self.get_object()
        request.user.saved_jobs.add(job)
        return Response({'status': 'saved'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unsave(self, request, slug=None):
        """Remove job from saved jobs"""
        job = self.get_object()
        request.user.saved_jobs.remove(job)
        return Response({'status': 'unsaved'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def apply(self, request, slug=None):
        """Track job application"""
        job = self.get_object()
        
        # Check if already applied
        if JobApplication.objects.filter(user=request.user, job=job).exists():
            return Response(
                {'error': 'Already applied to this job'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create application record
        application = JobApplication.objects.create(
            user=request.user,
            job=job,
            status='applied'
        )
        
        return Response({
            'status': 'success',
            'message': 'Application tracked successfully',
            'application_id': application.id
        })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def ask_rashid(self, request, slug=None):
        """Get Rashid's analysis of this job (Phase 2B integration)"""
        job = self.get_object()
        
        # This will be fully implemented in Phase 2B
        # For now, return a placeholder
        return Response({
            'message': 'Rashid analysis will be available after Phase 2B',
            'job_id': job.id,
            'job_title': job.title
        })
```

### Step 3: Job Filters

**File:** `backend/jobs/filters.py`

```python
import django_filters
from django.db.models import Q
from .models import Job, Category, Company

class JobFilter(django_filters.FilterSet):
    """Advanced filtering for job listings"""
    
    # Text search
    search = django_filters.CharFilter(method='filter_search')
    
    # Category
    category = django_filters.ModelMultipleChoiceFilter(
        field_name='category__slug',
        to_field_name='slug',
        queryset=Category.objects.all()
    )
    
    # Location
    location = django_filters.CharFilter(lookup_expr='icontains')
    location_in = django_filters.CharFilter(method='filter_location_in')
    
    # Workplace type
    workplace_type = django_filters.MultipleChoiceFilter(
        choices=Job.WORKPLACE_CHOICES
    )
    
    # Employment type
    employment_type = django_filters.MultipleChoiceFilter(
        choices=Job.EMPLOYMENT_CHOICES
    )
    
    # Experience level
    experience_level = django_filters.MultipleChoiceFilter(
        choices=Job.EXPERIENCE_CHOICES
    )
    
    # Salary
    salary_min = django_filters.NumberFilter(
        field_name='salary_min',
        lookup_expr='gte'
    )
    salary_max = django_filters.NumberFilter(
        field_name='salary_max',
        lookup_expr='lte'
    )
    has_salary = django_filters.BooleanFilter(method='filter_has_salary')
    
    # Company
    company = django_filters.ModelMultipleChoiceFilter(
        field_name='company__slug',
        to_field_name='slug',
        queryset=Company.objects.all()
    )
    company_size = django_filters.MultipleChoiceFilter(
        field_name='company__size',
        choices=Company.SIZE_CHOICES
    )
    
    # Source
    source = django_filters.CharFilter(field_name='source__slug')
    
    # Date posted
    posted_within = django_filters.NumberFilter(method='filter_posted_within')
    
    # Featured
    is_featured = django_filters.BooleanFilter()
    
    # Skills
    skills = django_filters.CharFilter(method='filter_skills')
    
    class Meta:
        model = Job
        fields = [
            'category', 'location', 'workplace_type', 'employment_type',
            'experience_level', 'is_featured', 'company'
        ]
    
    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields"""
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(company__name__icontains=value) |
            Q(location__icontains=value)
        )
    
    def filter_location_in(self, queryset, name, value):
        """Filter by multiple locations (comma-separated)"""
        locations = [loc.strip() for loc in value.split(',')]
        query = Q()
        for loc in locations:
            query |= Q(location__icontains=loc)
        return queryset.filter(query)
    
    def filter_has_salary(self, queryset, name, value):
        """Filter jobs that have salary information"""
        if value:
            return queryset.filter(
                Q(salary_min__isnull=False) | Q(salary_max__isnull=False)
            )
        return queryset.filter(salary_min__isnull=True, salary_max__isnull=True)
    
    def filter_posted_within(self, queryset, name, value):
        """Filter jobs posted within N days"""
        from django.utils import timezone
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=value)
        return queryset.filter(posted_date__gte=cutoff_date)
    
    def filter_skills(self, queryset, name, value):
        """Filter by skills (comma-separated)"""
        skills = [skill.strip() for skill in value.split(',')]
        for skill in skills:
            queryset = queryset.filter(skills_required__name__icontains=skill)
        return queryset
```

### Step 4: URL Configuration

**File:** `backend/jobs/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet

router = DefaultRouter()
router.register(r'', JobViewSet, basename='job')

urlpatterns = [
    path('', include(router.urls)),
]
```

**File:** `backend/ecareer/urls.py` (add to existing)

```python
urlpatterns = [
    # ... existing paths
    path('api/jobs/', include('jobs.urls')),
]
```

### Step 5: Matching Service (Placeholder for Phase 2A)

**File:** `backend/profiles/services.py`

```python
"""
Job matching service
Will be enhanced with AWS Bedrock in Phase 2A
"""

class MatchingService:
    """Calculate job-profile match scores"""
    
    def calculate_match_score(self, profile, job):
        """
        Basic matching algorithm (will be AI-powered in Phase 2A)
        
        Weights:
        - Skills match: 40%
        - Location match: 20%
        - Experience level match: 15%
        - Salary match: 15%
        - Industry match: 10%
        """
        score = 0.0
        
        # Skills match (40%)
        if profile.skills and job.skills_required.exists():
            profile_skills = set(skill.lower() for skill in profile.skills)
            job_skills = set(
                skill.name.lower() for skill in job.skills_required.all()
            )
            
            if job_skills:
                skills_match = len(profile_skills & job_skills) / len(job_skills)
                score += skills_match * 40
        
        # Location match (20%)
        if profile.preferred_locations and job.location:
            location_match = any(
                loc.lower() in job.location.lower()
                for loc in profile.preferred_locations
            )
            if location_match:
                score += 20
        
        # Experience level match (15%)
        if profile.years_of_experience and job.experience_level:
            exp_mapping = {
                'entry': (0, 2),
                'junior': (1, 3),
                'mid': (3, 6),
                'senior': (6, 10),
                'lead': (8, None),
                'executive': (10, None)
            }
            
            min_exp, max_exp = exp_mapping.get(job.experience_level, (0, None))
            user_exp = profile.years_of_experience
            
            if max_exp is None:
                if user_exp >= min_exp:
                    score += 15
            elif min_exp <= user_exp <= max_exp:
                score += 15
            elif user_exp >= min_exp:
                score += 10  # Over-qualified but still a match
        
        # Salary match (15%)
        if profile.desired_salary_min and job.salary_min:
            if job.salary_min >= profile.desired_salary_min:
                score += 15
            elif job.salary_max and job.salary_max >= profile.desired_salary_min:
                score += 10
        
        # Industry match (10%)
        if profile.preferred_industries and job.company and job.company.industry:
            if job.company.industry in profile.preferred_industries:
                score += 10
        
        return min(score, 100)  # Cap at 100
    
    def get_match_breakdown(self, profile, job):
        """Detailed breakdown of match components"""
        breakdown = {
            'overall_score': self.calculate_match_score(profile, job),
            'components': {}
        }
        
        # Skills
        if profile.skills and job.skills_required.exists():
            profile_skills = set(skill.lower() for skill in profile.skills)
            job_skills = set(
                skill.name.lower() for skill in job.skills_required.all()
            )
            matched_skills = profile_skills & job_skills
            
            breakdown['components']['skills'] = {
                'score': len(matched_skills) / len(job_skills) * 100 if job_skills else 0,
                'matched': list(matched_skills),
                'missing': list(job_skills - profile_skills)
            }
        
        # Location
        location_match = False
        if profile.preferred_locations and job.location:
            location_match = any(
                loc.lower() in job.location.lower()
                for loc in profile.preferred_locations
            )
        breakdown['components']['location'] = {
            'score': 100 if location_match else 0,
            'user_preference': profile.preferred_locations,
            'job_location': job.location
        }
        
        # Experience
        breakdown['components']['experience'] = {
            'user_years': profile.years_of_experience,
            'job_requirement': job.experience_level
        }
        
        # Salary
        breakdown['components']['salary'] = {
            'user_expectation': profile.desired_salary_min,
            'job_offer_min': job.salary_min,
            'job_offer_max': job.salary_max
        }
        
        return breakdown
```

---

## 🎨 Frontend Implementation

### Step 6: Job Listing Page

**File:** `frontend/src/pages/JobListingPage.jsx`

```jsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, MapPin, Briefcase, Clock, Star } from 'lucide-react';
import axios from 'axios';
import JobCard from '../components/jobs/JobCard';
import JobFilters from '../components/jobs/JobFilters';

const JobListingPage = () => {
  const [filters, setFilters] = useState({
    search: '',
    category: [],
    location: '',
    workplace_type: [],
    employment_type: [],
    experience_level: [],
    has_salary: false,
    posted_within: null
  });
  
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  // Fetch jobs
  const { data, isLoading, error } = useQuery({
    queryKey: ['jobs', filters, page],
    queryFn: async () => {
      const params = new URLSearchParams();
      
      if (filters.search) params.append('search', filters.search);
      if (filters.location) params.append('location', filters.location);
      if (filters.category.length) {
        filters.category.forEach(cat => params.append('category', cat));
      }
      if (filters.workplace_type.length) {
        filters.workplace_type.forEach(wt => params.append('workplace_type', wt));
      }
      if (filters.employment_type.length) {
        filters.employment_type.forEach(et => params.append('employment_type', et));
      }
      if (filters.experience_level.length) {
        filters.experience_level.forEach(el => params.append('experience_level', el));
      }
      if (filters.has_salary) params.append('has_salary', 'true');
      if (filters.posted_within) params.append('posted_within', filters.posted_within);
      
      params.append('page', page);
      
      const response = await axios.get(`/api/jobs/?${params.toString()}`);
      return response.data;
    }
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Find Your Next Job</h1>
          <p className="mt-2 text-gray-600">
            {data?.count || 0} direct opportunities from top companies
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Filters Sidebar */}
          <aside className={`
            w-80 flex-shrink-0
            ${showFilters ? 'block' : 'hidden lg:block'}
          `}>
            <div className="bg-white rounded-lg shadow p-6 sticky top-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                <button
                  onClick={() => setFilters({
                    search: '',
                    category: [],
                    location: '',
                    workplace_type: [],
                    employment_type: [],
                    experience_level: [],
                    has_salary: false,
                    posted_within: null
                  })}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Clear all
                </button>
              </div>
              
              <JobFilters
                filters={filters}
                onChange={setFilters}
              />
            </div>
          </aside>

          {/* Job Listings */}
          <main className="flex-1 min-w-0">
            {/* Search Bar */}
            <div className="bg-white rounded-lg shadow p-4 mb-6">
              <div className="flex gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Search jobs, companies, or keywords..."
                    value={filters.search}
                    onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="lg:hidden px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                >
                  <Filter className="w-5 h-5" />
                  Filters
                </button>
              </div>
            </div>

            {/* Quick Filters */}
            <div className="flex flex-wrap gap-2 mb-6">
              <button
                onClick={() => setFilters({ ...filters, posted_within: 7 })}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filters.posted_within === 7
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border'
                }`}
              >
                Last 7 days
              </button>
              
              <button
                onClick={() => setFilters({ ...filters, workplace_type: ['remote'] })}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filters.workplace_type.includes('remote')
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border'
                }`}
              >
                Remote
              </button>
              
              <button
                onClick={() => setFilters({ ...filters, has_salary: !filters.has_salary })}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filters.has_salary
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border'
                }`}
              >
                Has Salary
              </button>
            </div>

            {/* Results */}
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
                    <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <p className="text-red-800">Failed to load jobs. Please try again.</p>
              </div>
            ) : data?.results?.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <p className="text-gray-600 mb-4">No jobs found matching your criteria.</p>
                <button
                  onClick={() => setFilters({
                    search: '',
                    category: [],
                    location: '',
                    workplace_type: [],
                    employment_type: [],
                    experience_level: [],
                    has_salary: false,
                    posted_within: null
                  })}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  Clear all filters
                </button>
              </div>
            ) : (
              <>
                <div className="space-y-4 mb-8">
                  {data?.results?.map(job => (
                    <JobCard key={job.id} job={job} />
                  ))}
                </div>

                {/* Pagination */}
                {data?.count > 20 && (
                  <div className="flex justify-center gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Previous
                    </button>
                    
                    <span className="px-4 py-2">
                      Page {page} of {Math.ceil(data.count / 20)}
                    </span>
                    
                    <button
                      onClick={() => setPage(p => p + 1)}
                      disabled={!data?.next}
                      className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default JobListingPage;
```

### Step 7: Job Card Component

**File:** `frontend/src/components/jobs/JobCard.jsx`

```jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Briefcase, Clock, Star, Bookmark, ExternalLink } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const JobCard = ({ job }) => {
  const queryClient = useQueryClient();
  
  const saveJobMutation = useMutation({
    mutationFn: async (jobSlug) => {
      if (job.is_saved) {
        await axios.post(`/api/jobs/${jobSlug}/unsave/`);
      } else {
        await axios.post(`/api/jobs/${jobSlug}/save/`);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['jobs']);
    }
  });

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition p-6 border border-gray-200">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-4 flex-1">
          {/* Company Logo */}
          {job.company?.logo_url ? (
            <img
              src={job.company.logo_url}
              alt={job.company.name}
              className="w-16 h-16 rounded-lg object-cover border"
            />
          ) : (
            <div className="w-16 h-16 rounded-lg bg-gray-100 flex items-center justify-center border">
              <Briefcase className="w-8 h-8 text-gray-400" />
            </div>
          )}

          {/* Job Info */}
          <div className="flex-1 min-w-0">
            <Link
              to={`/jobs/${job.slug}`}
              className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition block"
            >
              {job.title}
            </Link>
            
            <p className="text-gray-600 mt-1">
              {job.company?.name || 'Company Name'}
            </p>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                <MapPin className="w-4 h-4" />
                {job.location}
              </span>
              
              <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm capitalize">
                {job.workplace_type}
              </span>
              
              <span className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm capitalize">
                {job.employment_type}
              </span>
              
              {job.experience_level && (
                <span className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm capitalize">
                  {job.experience_level}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col items-end gap-3 ml-4">
          {/* Match Score */}
          {job.match_score !== null && (
            <div className="flex items-center gap-2 px-3 py-1 bg-green-50 border border-green-200 rounded-lg">
              <Star className="w-4 h-4 text-green-600" />
              <span className="text-green-700 font-semibold">
                {job.match_score}% Match
              </span>
            </div>
          )}

          {/* Save Button */}
          <button
            onClick={() => saveJobMutation.mutate(job.slug)}
            className={`p-2 rounded-lg transition ${
              job.is_saved
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title={job.is_saved ? 'Unsave job' : 'Save job'}
          >
            <Bookmark className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Salary */}
      {job.salary_display !== 'Not specified' && (
        <div className="mb-4">
          <p className="text-lg font-semibold text-gray-900">
            {job.salary_display}
          </p>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {job.posted_ago}
          </span>
          
          {job.is_featured && (
            <span className="flex items-center gap-1 text-yellow-600">
              <Star className="w-4 h-4 fill-current" />
              Featured
            </span>
          )}
          
          <span className="flex items-center gap-1">
            <img
              src={`/icons/${job.source?.icon || 'default.png'}`}
              alt={job.source?.name}
              className="w-4 h-4"
              onError={(e) => e.target.style.display = 'none'}
            />
            {job.source?.name}
          </span>
        </div>

        <Link
          to={`/jobs/${job.slug}`}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium flex items-center gap-2"
        >
          View Details
          <ExternalLink className="w-4 h-4" />
        </Link>
      </div>

      {/* Warning for low legitimacy */}
      {job.legitimacy_score < 50 && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⚠️ This job posting has been flagged for potential issues. Please verify before applying.
          </p>
        </div>
      )}
    </div>
  );
};

export default JobCard;
```

### Step 8: Job Filters Component

**File:** `frontend/src/components/jobs/JobFilters.jsx`

```jsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const JobFilters = ({ filters, onChange }) => {
  // Fetch filter options
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await axios.get('/api/categories/');
      return response.data;
    }
  });

  const workplaceTypes = [
    { value: 'remote', label: 'Remote' },
    { value: 'onsite', label: 'On-site' },
    { value: 'hybrid', label: 'Hybrid' }
  ];

  const employmentTypes = [
    { value: 'full_time', label: 'Full Time' },
    { value: 'part_time', label: 'Part Time' },
    { value: 'contract', label: 'Contract' },
    { value: 'freelance', label: 'Freelance' },
    { value: 'internship', label: 'Internship' }
  ];

  const experienceLevels = [
    { value: 'entry', label: 'Entry Level' },
    { value: 'junior', label: 'Junior' },
    { value: 'mid', label: 'Mid Level' },
    { value: 'senior', label: 'Senior' },
    { value: 'lead', label: 'Lead' },
    { value: 'executive', label: 'Executive' }
  ];

  const handleCheckbox = (field, value) => {
    const current = filters[field] || [];
    const updated = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value];
    onChange({ ...filters, [field]: updated });
  };

  return (
    <div className="space-y-6">
      {/* Location */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Location
        </label>
        <input
          type="text"
          placeholder="e.g., Cairo, Remote"
          value={filters.location || ''}
          onChange={(e) => onChange({ ...filters, location: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Category */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Category
        </label>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {categories?.map(category => (
            <label key={category.id} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.category?.includes(category.slug)}
                onChange={() => handleCheckbox('category', category.slug)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">{category.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Workplace Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Workplace Type
        </label>
        <div className="space-y-2">
          {workplaceTypes.map(type => (
            <label key={type.value} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.workplace_type?.includes(type.value)}
                onChange={() => handleCheckbox('workplace_type', type.value)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">{type.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Employment Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Employment Type
        </label>
        <div className="space-y-2">
          {employmentTypes.map(type => (
            <label key={type.value} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.employment_type?.includes(type.value)}
                onChange={() => handleCheckbox('employment_type', type.value)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">{type.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Experience Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Experience Level
        </label>
        <div className="space-y-2">
          {experienceLevels.map(level => (
            <label key={level.value} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.experience_level?.includes(level.value)}
                onChange={() => handleCheckbox('experience_level', level.value)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">{level.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Posted Within */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Posted Within
        </label>
        <select
          value={filters.posted_within || ''}
          onChange={(e) => onChange({ ...filters, posted_within: e.target.value ? parseInt(e.target.value) : null })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Any time</option>
          <option value="1">Last 24 hours</option>
          <option value="7">Last 7 days</option>
          <option value="14">Last 14 days</option>
          <option value="30">Last 30 days</option>
        </select>
      </div>

      {/* Has Salary */}
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={filters.has_salary || false}
            onChange={(e) => onChange({ ...filters, has_salary: e.target.checked })}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="ml-2 text-sm text-gray-700">Only show jobs with salary</span>
        </label>
      </div>
    </div>
  );
};

export default JobFilters;
```

---

## ✅ Phase 1C Verification

### Backend Tests

```bash
# Test job listing endpoint
curl http://localhost:8000/api/jobs/

# Test with filters
curl "http://localhost:8000/api/jobs/?workplace_type=remote&posted_within=7"

# Test job detail
curl http://localhost:8000/api/jobs/senior-python-developer-company-xyz/

# Test search
curl "http://localhost:8000/api/jobs/?search=python"
```

### Frontend Tests

1. **Visit job listing page**
   - Navigate to `/jobs`
   - Verify jobs load correctly
   - Test search functionality
   - Test filters (category, location, workplace type)
   - Test quick filters (Last 7 days, Remote, Has Salary)

2. **Test job card interactions**
   - Click save/unsave button
   - Verify match score displays (if logged in with profile)
   - Click "View Details" button

3. **Test pagination**
   - Scroll to bottom
   - Click "Next" to load more jobs
   - Click "Previous" to go back

4. **Test responsive design**
   - Resize browser window
   - Verify mobile menu works
   - Verify filters sidebar toggles on mobile

### Success Criteria

- [ ] Job listing page loads with all jobs
- [ ] Search works across title, description, company, location
- [ ] All filters work correctly
- [ ] Match score displays for users with profiles
- [ ] Save/unsave functionality works
- [ ] Job cards display all required information
- [ ] Pagination works
- [ ] Responsive design works on mobile
- [ ] No console errors
- [ ] Direct apply URLs are validated

---

## 🔄 Integration with Previous Phases

This phase builds on:
- **Phase 1A:** Uses Job, Company, Category, Source models
- **Phase 1B:** Displays jobs scraped by the pipeline

Prepares for:
- **Phase 2A:** Match score calculation will be enhanced with AI
- **Phase 2B:** "Ask Rashid about this job" button will be functional

---

## 🐛 Troubleshooting

**Issue:** Jobs not loading
**Solution:** Verify Phase 1B scrapers have populated the database

**Issue:** Match scores not showing
**Solution:** User must be logged in and have a completed profile (Phase 2A)

**Issue:** Filters not working
**Solution:** Check django-filter is installed and configured in settings.py

**Issue:** Images not loading
**Solution:** Verify MEDIA_URL and MEDIA_ROOT are configured correctly

---

**Phase 1C Complete! ✅**
Proceed to Phase 2A: User Profiles & CV Intelligence
