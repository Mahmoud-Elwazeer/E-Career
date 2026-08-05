"""
Employer Portal Admin using django-unfold.
Phase 3A: Employer self-service portal
Phase 3C: Admin Dashboard Extensions
"""
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from unfold.admin import ModelAdmin
from unfold.decorators import display
try:
    from unfold.enums import Color
except ImportError:
    class Color:
        GREEN = "green"
        GRAY = "gray"
        RED = "red"
        YELLOW = "yellow"
        BLUE = "blue"
        PURPLE = "purple"

from .models import EmployerProfile, JobPosting, JobApplication, KnockoutQuestion, CandidateRanking, TalentDiscovery


@admin.register(EmployerProfile)
class EmployerProfileAdmin(ModelAdmin):
    """
    Admin interface for employer profiles.
    Enhanced with unfold styling.
    """
    
    list_display = [
        'user_email',
        'company',
        'job_title',
        'is_verified',
        'verified_at',
        'created_at'
    ]
    list_filter = ['is_verified', 'company__industry', 'created_at']
    search_fields = ['user__email', 'company__name', 'job_title']
    readonly_fields = ['created_at', 'verified_at', 'verified_by']
    
    fieldsets = (
        ('User & Company', {
            'fields': ('user', 'company', 'job_title', 'phone')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verified_by')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_employers', 'reject_employers']
    
    @display(description='Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    @admin.action(description="Approve selected employers")
    def approve_employers(self, request, queryset):
        """Approve selected employers"""
        count = queryset.filter(is_verified=False).update(
            is_verified=True,
            verified_at=timezone.now(),
            verified_by=request.user
        )
        self.message_user(request, f'{count} employer(s) approved.', messages.SUCCESS)
    
    @admin.action(description="Reject/unverify selected employers")
    def reject_employers(self, request, queryset):
        """Reject/unverify selected employers"""
        count = queryset.filter(is_verified=True).update(
            is_verified=False,
            verified_at=None,
            verified_by=None
        )
        self.message_user(request, f'{count} employer(s) rejected.', messages.WARNING)


@admin.register(JobPosting)
class JobPostingAdmin(ModelAdmin):
    """
    Admin interface for employer job postings.
    Enhanced with unfold styling.
    """
    
    list_display = [
        'title',
        'employer_company',
        'status_badge',
        'employment_type',
        'location',
        'views_count',
        'clicks_count',
        'created_at'
    ]
    list_filter = ['status', 'employment_type', 'remote_type', 'experience_level', 'created_at']
    search_fields = ['title', 'employer__company__name', 'location']
    readonly_fields = [
        'uuid', 'employer', 'company', 'views_count', 'clicks_count',
        'published_at', 'created_at', 'updated_at', 'mirrored_job'
    ]
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'description', 'requirements')
        }),
        ('Employer & Company', {
            'fields': ('employer', 'company', 'mirrored_job')
        }),
        ('Classification', {
            'fields': ('employment_type', 'experience_level', 'remote_type', 'location')
        }),
        ('Salary', {
            'fields': ('salary_min', 'salary_max', 'salary_currency'),
            'classes': ('collapse',)
        }),
        ('Application', {
            'fields': ('apply_url', 'apply_url_verified', 'apply_url_checked_at')
        }),
        ('Status', {
            'fields': ('status', 'published_at', 'expires_at', 'rejected_reason')
        }),
        ('Analytics', {
            'fields': ('views_count', 'clicks_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('uuid', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_jobs', 'reject_jobs', 'verify_apply_urls']
    
    @display(description='Company', ordering='employer__company__name')
    def employer_company(self, obj):
        return obj.employer.company.name
    
    @display(
        description='Status',
        label={
            'published': Color.GREEN,
            'pending_review': Color.YELLOW,
            'rejected': Color.RED,
            'draft': Color.GRAY,
            'expired': Color.GRAY,
        }
    )
    def status_badge(self, obj):
        return obj.get_status_display()
    
    @admin.action(description="Approve and publish selected jobs")
    def approve_jobs(self, request, queryset):
        """Approve and publish selected jobs"""
        from apps.jobs.models import Job
        from apps.core.utils import make_unique_slug
        
        approved_count = 0
        for job_post in queryset.filter(status='pending_review'):
            # Create Job from JobPosting
            job = Job.objects.create(
                title=job_post.title,
                slug=make_unique_slug(Job, job_post.title),
                company=job_post.company,
                description=job_post.description,
                location=job_post.location,
                location_type=job_post.remote_type,
                experience_level=job_post.experience_level,
                employment_type=job_post.employment_type,
                salary_min=job_post.salary_min,
                salary_max=job_post.salary_max,
                salary_currency=job_post.salary_currency,
                source_url=job_post.apply_url,
                direct_apply_url=job_post.apply_url,
                apply_url_verified=job_post.apply_url_verified,
                source_type='employer_posted',
                status='active',
                posted_at=timezone.now().date(),
                is_legitimate=True,
                legitimacy_score=1.0,
            )
            
            # Link the job posting to the job
            job_post.mirrored_job = job
            job_post.status = 'published'
            job_post.published_at = timezone.now()
            job_post.save()
            
            approved_count += 1
        
        self.message_user(
            request,
            f'{approved_count} job(s) approved and published.',
            messages.SUCCESS
        )
    
    @admin.action(description="Reject selected job postings")
    def reject_jobs(self, request, queryset):
        """Reject selected job postings"""
        count = queryset.filter(status='pending_review').update(
            status='rejected'
        )
        self.message_user(request, f'{count} job(s) rejected.', messages.WARNING)
    
    @admin.action(description="Verify apply URLs")
    def verify_apply_urls(self, request, queryset):
        """Mark apply URLs as verified"""
        count = queryset.update(
            apply_url_verified=True,
            apply_url_checked_at=timezone.now()
        )
        self.message_user(request, f'{count} job(s) apply URL verified.', messages.SUCCESS)


@admin.register(JobApplication)
class JobApplicationAdmin(ModelAdmin):
    """
    Admin interface for job applications.
    Enhanced with unfold styling.
    """
    
    list_display = [
        'user_email',
        'job_title',
        'status_badge',
        'applied_at'
    ]
    list_filter = ['status', 'applied_at']
    search_fields = ['user__email', 'job__title']
    readonly_fields = ['user', 'job', 'applied_at', 'cv_snapshot']
    
    fieldsets = (
        ('Application', {
            'fields': ('user', 'job', 'status')
        }),
        ('CV Snapshot', {
            'fields': ('cv_snapshot',)
        }),
        ('Timestamps', {
            'fields': ('applied_at',),
        }),
    )
    
    @display(description='Applicant Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    @display(description='Job', ordering='job__title')
    def job_title(self, obj):
        return obj.job.title
    
    @display(
        description='Status',
        label={
            'pending': Color.YELLOW,
            'reviewed': Color.BLUE,
            'shortlisted': Color.GREEN,
            'rejected': Color.RED,
            'hired': Color.PURPLE,
        }
    )
    def status_badge(self, obj):
        return obj.get_status_display()


def get_pending_verifications_count():
    """Badge count for pending employer verifications"""
    return EmployerProfile.objects.filter(is_verified=False).count()


def get_pending_jobs_count():
    """Badge count for pending job approvals"""
    return JobPosting.objects.filter(status='pending_review').count()


# ============================================================================
# Employer Intelligence Admin (Phase 4)
# ============================================================================


@admin.register(KnockoutQuestion)
class KnockoutQuestionAdmin(ModelAdmin):
    """Admin for KnockoutQuestion model."""
    
    list_display = [
        'question_text',
        'employer_company',
        'question_type',
        'pass_if_matches',
        'weight',
        'is_active',
        'created_at',
    ]
    list_filter = ['question_type', 'pass_if_matches', 'is_active', 'created_at']
    search_fields = ['question_text', 'employer__company__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Question', {
            'fields': ('question_text', 'question_type', 'required_answer')
        }),
        ('Evaluation', {
            'fields': ('pass_if_matches', 'weight')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )
    
    @display(description='Company', ordering='employer__company__name')
    def employer_company(self, obj):
        return obj.employer.company.name


@admin.register(CandidateRanking)
class CandidateRankingAdmin(ModelAdmin):
    """Admin for CandidateRanking model."""
    
    list_display = [
        'user_email',
        'job_title',
        'overall_score',
        'skill_match_score',
        'experience_score',
        'knockout_passed',
        'status',
        'ranked_at',
    ]
    list_filter = ['status', 'knockout_passed', 'ranked_at']
    search_fields = ['user__email', 'job__title']
    readonly_fields = ['ranked_at']
    
    fieldsets = (
        ('Candidate & Job', {
            'fields': ('user', 'job', 'employer')
        }),
        ('Scores', {
            'fields': (
                'overall_score', 'skill_match_score', 'experience_score',
                'education_score', 'salary_expectation_score'
            )
        }),
        ('Knockout Evaluation', {
            'fields': ('knockout_passed', 'knockout_failures')
        }),
        ('Explanations', {
            'fields': ('explanations',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'ranked_at')
        }),
    )
    
    @display(description='Applicant Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    @display(description='Job', ordering='job__title')
    def job_title(self, obj):
        return obj.job.title


@admin.register(TalentDiscovery)
class TalentDiscoveryAdmin(ModelAdmin):
    """Admin for TalentDiscovery model."""
    
    list_display = [
        'user_email',
        'employer_company',
        'source',
        'search_query',
        'matched_skills_count',
        'viewed_at',
        'saved',
        'created_at',
    ]
    list_filter = ['source', 'saved', 'created_at']
    search_fields = ['user__email', 'search_query', 'employer__company__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Discovery', {
            'fields': ('user', 'employer', 'source')
        }),
        ('Search Context', {
            'fields': ('search_query', 'matched_skills')
        }),
        ('Interaction', {
            'fields': ('viewed_at', 'saved', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )
    
    @display(description='Applicant Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    @display(description='Company', ordering='employer__company__name')
    def employer_company(self, obj):
        return obj.employer.company.name
    
    @display(description='Matched Skills')
    def matched_skills_count(self, obj):
        return len(obj.matched_skills) if obj.matched_skills else 0
