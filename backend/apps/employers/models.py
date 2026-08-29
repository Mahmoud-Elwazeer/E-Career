from django.db import models
from django.conf import settings
from apps.core.models import UUIDModel


class EmployerProfile(models.Model):
    """
    Employer user profile linked to a Company.
    Must be verified by admin before posting jobs.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employer_profile'
    )
    company = models.ForeignKey(
        'jobs.Company',
        on_delete=models.CASCADE,
        related_name='employers'
    )
    
    job_title = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employer_verifications_done'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Employer Profile'
        verbose_name_plural = 'Employer Profiles'
    
    def __str__(self):
        return f"{self.user.email} @ {self.company.name}"




class EmployerTeamMember(models.Model):
    """Multi-seat employer: links additional users to a Company with roles."""

    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('recruiter', 'Recruiter'),
        ('hiring_manager', 'Hiring Manager'),
        ('viewer', 'Viewer'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employer_team_memberships',
    )
    company = models.ForeignKey(
        'jobs.Company',
        on_delete=models.CASCADE,
        related_name='team_members',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='team_invitations_sent',
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-invited_at']
        unique_together = [('user', 'company')]
        verbose_name = 'Employer Team Member'
        verbose_name_plural = 'Employer Team Members'

    def __str__(self):
        return f"{self.user.email} @ {self.company.name} ({self.role})"

class JobPosting(UUIDModel):
    """
    Employer-managed job posting.
    When published, it's mirrored to the main Job model.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('published', 'Published'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
    ]
    
    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='job_postings'
    )
    company = models.ForeignKey(
        'jobs.Company',
        on_delete=models.CASCADE,
        related_name='employer_postings'
    )
    
    # Link to mirrored job (created on publish)
    mirrored_job = models.OneToOneField(
        'jobs.Job',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employer_posting'
    )
    
    # Job content
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    
    # MUST be company's own URL, not aggregator
    apply_url = models.URLField(
        max_length=2000,
        help_text="Direct link to your company's application page"
    )
    apply_url_verified = models.BooleanField(default=False)
    apply_url_checked_at = models.DateTimeField(null=True, blank=True)
    
    # Classification
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('freelance', 'Freelance'),
        ]
    )
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('student', 'Student'),
            ('entry', 'Entry Level'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior'),
            ('director', 'Director'),
            ('c_level', 'C-Level'),
        ]
    )
    remote_type = models.CharField(
        max_length=10,
        choices=[
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
            ('onsite', 'On-site'),
        ]
    )
    location = models.CharField(max_length=200)
    
    # Salary (optional)
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='EGP')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)
    
    # Dynamic application form fields (JSON schema)
    # Each field: {id, type, label, required, options?, placeholder?, validation?}
    # Types: text, textarea, select, multiselect, yes_no, number, date, file, url
    custom_form_fields = models.JSONField(
        default=list,
        blank=True,
        help_text="Custom application form fields as JSON schema"
    )

    # Analytics
    views_count = models.IntegerField(default=0)
    clicks_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'

    def __str__(self):
        return f"{self.title} @ {self.company.name} ({self.status})"


class JobApplication(models.Model):
    """
    Tracks when a user clicks Apply on a job.
    Optional on-platform application tracking.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications'
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    
    applied_at = models.DateTimeField(auto_now_add=True)
    
    # Snapshot of CV at time of application
    cv_snapshot = models.FileField(
        upload_to='application_cvs/%Y/%m/',
        null=True,
        blank=True
    )
    
    status = models.CharField(
        max_length=20,
        default='applied',
        choices=[
            ('applied', 'Applied'),
            ('viewed', 'Viewed by Employer'),
            ('shortlisted', 'Shortlisted'),
            ('rejected', 'Rejected'),
        ]
    )

    # Responses to custom form fields (keyed by field id)
    custom_form_responses = models.JSONField(
        default=dict,
        blank=True,
        help_text="Candidate responses to custom application form fields"
    )

    class Meta:
        ordering = ['-applied_at']
        unique_together = ('user', 'job')
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'

    def __str__(self):
        return f"{self.user.email} → {self.job.title}"


# ============================================================================
# Employer Intelligence (Phase 4)
# ============================================================================


class KnockoutQuestion(models.Model):
    """
    DEPRECATED: Use dynamic-form knockout questions on JobPosting.custom_form_fields instead.
    This model is retained for backward compatibility with existing data.
    No new KnockoutQuestion records should be created via the API.
    """
    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='knockout_questions'
    )
    
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text Answer'),
            ('yes_no', 'Yes/No'),
            ('select', 'Multiple Choice'),
        ]
    )
    
    # Evaluation criteria
    required_answer = models.JSONField(
        default=dict,
        help_text="Expected answer(s) for passing"
    )
    pass_if_matches = models.BooleanField(
        default=True,
        help_text="Pass if answer matches (True) or doesn't match (False)"
    )
    
    # Weight in overall scoring
    weight = models.FloatField(
        default=1.0,
        help_text="Weight of this question in overall score"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Knockout Question'
        verbose_name_plural = 'Knockout Questions'
    
    def __str__(self):
        return f"{self.question_text[:50]}... ({self.employer})"


class CandidateRanking(models.Model):
    """
    AI-powered candidate ranking for employer job postings.
    
    Stores computed rankings with explainability.
    """
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='candidate_rankings'
    )
    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='candidate_rankings'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rankings'
    )
    
    # AI-computed scores
    overall_score = models.FloatField(
        help_text="AI-computed match score (0-1)"
    )
    skill_match_score = models.FloatField(
        help_text="Skills match score (0-1)"
    )
    experience_score = models.FloatField(
        help_text="Experience match score (0-1)"
    )
    education_score = models.FloatField(
        help_text="Education match score (0-1)"
    )
    salary_expectation_score = models.FloatField(
        help_text="Salary expectation alignment (0-1)"
    )
    
    # Knockout evaluation
    knockout_passed = models.BooleanField(default=True)
    knockout_failures = models.JSONField(
        default=list,
        help_text="List of failed knockout questions"
    )
    
    # Explainability
    explanations = models.JSONField(
        default=dict,
        help_text="AI-generated explanations for ranking"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('ranked', 'Ranked'),
            ('shortlisted', 'Shortlisted'),
            ('rejected', 'Rejected'),
        ]
    )
    
    ranked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-overall_score', 'ranked_at']
        unique_together = ('job', 'user')
        verbose_name = 'Candidate Ranking'
        verbose_name_plural = 'Candidate Rankings'
    
    def __str__(self):
        return f"{self.user.email} → {self.job.title} ({self.overall_score:.0%})"


class TalentDiscovery(models.Model):
    """
    Proactive talent discovery tracking.
    
    Tracks when employers view candidate profiles
    outside of job applications.
    """
    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='talent_discoveries'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='talent_discoveries'
    )
    
    # Discovery context
    source = models.CharField(
        max_length=50,
        choices=[
            ('search', 'Search Results'),
            ('recommendation', 'AI Recommendation'),
            ('profile_view', 'Profile View'),
            ('skill_match', 'Skill Match Alert'),
        ]
    )
    
    search_query = models.TextField(blank=True)
    matched_skills = models.JSONField(
        default=list,
        help_text="Skills that triggered this discovery"
    )
    
    # Interaction
    viewed_at = models.DateTimeField(null=True, blank=True)
    saved = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Talent Discovery'
        verbose_name_plural = 'Talent Discoveries'
    
    def __str__(self):
        return f"{self.employer} discovered {self.user.email}"


class TalentPool(UUIDModel):
    """
    A named collection of candidates curated by an employer.
    Used for building hiring pipelines across multiple roles.
    """
    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='talent_pools'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('employer', 'name')

    def __str__(self):
        return f"{self.name} ({self.employer})"

    @property
    def candidate_count(self):
        return self.candidates.count()


class TalentPoolCandidate(models.Model):
    """A candidate in a talent pool with notes and tags."""
    pool = models.ForeignKey(
        TalentPool,
        on_delete=models.CASCADE,
        related_name='candidates'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='talent_pool_memberships'
    )
    tags = models.JSONField(default=list, help_text="Employer-defined tags")
    notes = models.TextField(blank=True)
    rating = models.IntegerField(
        null=True, blank=True,
        help_text="Employer rating 1-5"
    )
    source = models.CharField(
        max_length=30,
        choices=[
            ('manual', 'Manual Add'),
            ('search', 'From Search'),
            ('application', 'From Application'),
            ('recommendation', 'AI Recommendation'),
        ],
        default='manual'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        unique_together = ('pool', 'user')

    def __str__(self):
        return f"{self.user.email} in {self.pool.name}"
