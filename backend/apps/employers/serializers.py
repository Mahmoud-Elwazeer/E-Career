"""
Employer Portal Serializers
Phase 3A: Employer self-service portal
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmployerProfile, JobPosting, JobApplication, KnockoutQuestion, CandidateRanking, TalentDiscovery, TalentPool, TalentPoolCandidate
from apps.jobs.serializers import CompanySerializer

User = get_user_model()


class EmployerProfileSerializer(serializers.ModelSerializer):
    """Serializer for employer profile"""
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True, required=False)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = EmployerProfile
        fields = [
            'id', 'user_email', 'user_name', 'company', 'company_id',
            'job_title', 'phone', 'is_verified', 'verified_at',
            'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'verified_at', 'created_at']


class EmployerProfileWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employer profile"""
    
    class Meta:
        model = EmployerProfile
        fields = ['company', 'job_title', 'phone']
    
    def validate_company(self, value):
        """Ensure company exists and is active"""
        if not value.is_active:
            raise serializers.ValidationError("This company is not active.")
        return value


class JobPostingListSerializer(serializers.ModelSerializer):
    """Serializer for listing job postings"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_logo = serializers.CharField(source='company.logo_url', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    remote_type_display = serializers.CharField(source='get_remote_type_display', read_only=True)
    salary_display = serializers.SerializerMethodField()
    applications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobPosting
        fields = [
            'id', 'uuid', 'title', 'company_name', 'company_logo',
            'location', 'employment_type', 'employment_type_display',
            'remote_type', 'remote_type_display', 'experience_level',
            'salary_min', 'salary_max', 'salary_currency', 'salary_display',
            'status', 'status_display', 'published_at', 'expires_at',
            'views_count', 'clicks_count', 'applications_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uuid', 'status', 'published_at', 'views_count',
            'clicks_count', 'created_at', 'updated_at'
        ]
    
    def get_salary_display(self, obj):
        """Format salary for display"""
        if not obj.salary_min and not obj.salary_max:
            return None
        
        currency = obj.salary_currency or 'EGP'
        
        if obj.salary_min and obj.salary_max:
            return f"{currency} {obj.salary_min:,} - {obj.salary_max:,}"
        elif obj.salary_min:
            return f"{currency} {obj.salary_min:,}+"
        elif obj.salary_max:
            return f"Up to {currency} {obj.salary_max:,}"
        return None
    
    def get_applications_count(self, obj):
        """Get count of applications"""
        return obj.applications.count() if hasattr(obj, 'applications') else 0


class JobPostingDetailSerializer(JobPostingListSerializer):
    """Detailed serializer for job posting"""
    company = CompanySerializer(read_only=True)
    employer = EmployerProfileSerializer(read_only=True)

    class Meta(JobPostingListSerializer.Meta):
        fields = JobPostingListSerializer.Meta.fields + [
            'company', 'employer', 'description', 'requirements',
            'apply_url', 'apply_url_verified', 'rejected_reason',
            'custom_form_fields'
        ]


class JobPostingWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating job postings"""

    class Meta:
        model = JobPosting
        fields = [
            'title', 'description', 'requirements',
            'employment_type', 'experience_level', 'remote_type', 'location',
            'salary_min', 'salary_max', 'salary_currency',
            'apply_url', 'custom_form_fields'
        ]
    
    def validate_apply_url(self, value):
        """Validate apply URL is on company domain"""
        from urllib.parse import urlparse
        
        employer = self.context['request'].user.employer_profile
        company_website = employer.company.website
        
        if not company_website:
            raise serializers.ValidationError(
                "Company website must be set before posting jobs"
            )
        
        url_domain = urlparse(value).netloc.lower()
        company_domain = urlparse(company_website).netloc.lower()
        
        # Remove www. prefix for comparison
        url_domain = url_domain.replace('www.', '')
        company_domain = company_domain.replace('www.', '')
        
        if company_domain not in url_domain:
            raise serializers.ValidationError(
                f"Apply URL must be on company domain ({company_domain})"
            )
        
        return value
    
    def validate(self, data):
        """Validate salary range"""
        if data.get('salary_min') and data.get('salary_max'):
            if data['salary_min'] > data['salary_max']:
                raise serializers.ValidationError({
                    'salary_min': 'Minimum salary cannot exceed maximum salary'
                })
        return data


class JobApplicationSerializer(serializers.ModelSerializer):
    """Serializer for job applications (employer view)"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_id = serializers.IntegerField(source='job.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cv_url = serializers.SerializerMethodField()

    class Meta:
        model = JobApplication
        fields = [
            'id', 'user_name', 'user_email', 'job_title', 'job_id',
            'status', 'status_display', 'cv_snapshot', 'cv_url',
            'custom_form_responses', 'applied_at'
        ]
        read_only_fields = ['id', 'applied_at', 'cv_snapshot', 'custom_form_responses']
    
    def get_cv_url(self, obj):
        """Get CV URL if available"""
        if obj.cv_snapshot:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cv_snapshot.url)
        return None


class JobApplicationDetailSerializer(JobApplicationSerializer):
    """Detailed serializer for job application"""
    
    # User profile info (for employer to review)
    user_phone = serializers.SerializerMethodField()
    user_profile = serializers.SerializerMethodField()
    
    class Meta(JobApplicationSerializer.Meta):
        fields = JobApplicationSerializer.Meta.fields + [
            'user_phone', 'user_profile'
        ]
    
    def get_user_phone(self, obj):
        """Get user phone if available"""
        try:
            return obj.user.userprofile.phone
        except Exception:
            return None
    
    def get_user_profile(self, obj):
        """Get user profile summary"""
        try:
            profile = obj.user.userprofile
            return {
                'current_position': profile.current_position,
                'years_of_experience': profile.years_of_experience,
                'location': profile.location,
                'skills': profile.skills[:10] if profile.skills else [],
            }
        except Exception:
            return None


class EmployerRegistrationSerializer(serializers.Serializer):
    """Serializer for employer registration"""
    company_id = serializers.IntegerField()
    job_title = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_company_id(self, value):
        """Ensure company exists and is active"""
        from apps.jobs.models import Company
        try:
            company = Company.objects.get(id=value, is_active=True)
            return value
        except Company.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive company.")
    
    def validate(self, data):
        """Check if user already has employer profile"""
        user = self.context['request'].user
        if hasattr(user, 'employer_profile'):
            raise serializers.ValidationError(
                "You already have an employer profile."
            )
        return data


# ============================================================================
# Employer Intelligence Serializers (Phase 4)
# ============================================================================


class KnockoutQuestionSerializer(serializers.ModelSerializer):
    """Serializer for KnockoutQuestion model."""
    
    employer_name = serializers.CharField(source='employer.company.name', read_only=True)
    
    class Meta:
        model = KnockoutQuestion
        fields = [
            'id',
            'employer',
            'employer_name',
            'question_text',
            'question_type',
            'required_answer',
            'pass_if_matches',
            'weight',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'employer_name']


class KnockoutQuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating KnockoutQuestion."""
    
    class Meta:
        model = KnockoutQuestion
        fields = [
            'question_text',
            'question_type',
            'required_answer',
            'pass_if_matches',
            'weight',
            'is_active',
        ]


class CandidateRankingSerializer(serializers.ModelSerializer):
    """Serializer for CandidateRanking model."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    employer_name = serializers.CharField(source='employer.company.name', read_only=True)
    
    class Meta:
        model = CandidateRanking
        fields = [
            'id',
            'job',
            'job_title',
            'employer',
            'employer_name',
            'user',
            'user_name',
            'user_email',
            'overall_score',
            'skill_match_score',
            'experience_score',
            'education_score',
            'salary_expectation_score',
            'knockout_passed',
            'knockout_failures',
            'explanations',
            'status',
            'ranked_at',
        ]
        read_only_fields = ['id', 'ranked_at', 'user_name', 'user_email']


class CandidateRankingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating CandidateRanking status."""
    
    class Meta:
        model = CandidateRanking
        fields = ['status']


class TalentDiscoverySerializer(serializers.ModelSerializer):
    """Serializer for TalentDiscovery model."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    employer_name = serializers.CharField(source='employer.company.name', read_only=True)
    
    class Meta:
        model = TalentDiscovery
        fields = [
            'id',
            'employer',
            'employer_name',
            'user',
            'user_name',
            'user_email',
            'source',
            'search_query',
            'matched_skills',
            'viewed_at',
            'saved',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'user_name', 'user_email']


class TalentDiscoveryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TalentDiscovery."""
    
    class Meta:
        model = TalentDiscovery
        fields = [
            'user',
            'source',
            'search_query',
            'matched_skills',
            'saved',
            'notes',
        ]


class EmployerRankingRequestSerializer(serializers.Serializer):
    """Serializer for ranking candidates for a job."""
    
    job_id = serializers.IntegerField(required=True)
    candidate_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    rank_all = serializers.BooleanField(
        default=False,
        help_text="Rank all candidates for this job"
    )


class EmployerRankingResponseSerializer(serializers.Serializer):
    """Serializer for ranking response."""

    job_id = serializers.IntegerField()
    candidates_ranked = serializers.IntegerField()
    rankings = serializers.ListField(
        child=serializers.DictField()
    )


# ============================================================================
# Talent Pool Serializers
# ============================================================================


class TalentPoolCandidateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = TalentPoolCandidate
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'tags', 'notes', 'rating', 'source', 'added_at',
        ]
        read_only_fields = ['id', 'added_at', 'user_name', 'user_email']


class TalentPoolSerializer(serializers.ModelSerializer):
    candidate_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TalentPool
        fields = [
            'id', 'name', 'description', 'is_active',
            'candidate_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'candidate_count', 'created_at', 'updated_at']


class TalentPoolDetailSerializer(serializers.ModelSerializer):
    candidates = TalentPoolCandidateSerializer(many=True, read_only=True)
    candidate_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TalentPool
        fields = [
            'id', 'name', 'description', 'is_active',
            'candidate_count', 'candidates', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'candidate_count', 'created_at', 'updated_at']


class AddCandidateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    notes = serializers.CharField(required=False, default='')
    source = serializers.ChoiceField(
        choices=['manual', 'search', 'application', 'recommendation'],
        default='manual'
    )
