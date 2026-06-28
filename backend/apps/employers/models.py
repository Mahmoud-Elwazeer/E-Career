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
    
    class Meta:
        ordering = ['-applied_at']
        unique_together = ('user', 'job')
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
    
    def __str__(self):
        return f"{self.user.email} → {self.job.title}"