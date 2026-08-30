from django.db import models
from django.db.models import QuerySet
from apps.core.models import UUIDModel


class JobQuerySet(QuerySet):
    def active(self):
        return self.filter(quality_state__in=("active", "probably_active", "direct_verified"))

    def visible(self):
        return self.filter(quality_state__in=("active", "probably_active", "direct_verified", "needs_verification"))


JobManager = models.Manager.from_queryset(JobQuerySet)


class Company(UUIDModel):
    """A company that posts jobs."""

    INDUSTRY_CHOICES = [
        ("technology", "Technology"),
        ("finance", "Finance"),
        ("healthcare", "Healthcare"),
        ("education", "Education"),
        ("marketing", "Marketing"),
        ("engineering", "Engineering"),
        ("design", "Design"),
        ("sales", "Sales"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    logo_url = models.URLField(max_length=500, blank=True)
    snippet = models.CharField(max_length=300, blank=True, help_text="Short company description")
    about = models.TextField(blank=True, help_text="Full company description")
    industry = models.CharField(
        max_length=50, choices=INDUSTRY_CHOICES, default="other", db_index=True
    )
    website = models.URLField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # ============ NEW FIELDS - ADD THESE ============

    # Visual branding
    logo = models.ImageField(
        upload_to='company_logos/', 
        null=True, 
        blank=True
    )

    # Company information
    domain = models.CharField(
        max_length=100, 
        blank=True, 
        db_index=True,
        help_text="Company website domain (e.g., google.com)"
    )
    description = models.TextField(blank=True)
    size = models.CharField(
        max_length=20, 
        blank=True,
        help_text="1-10, 11-50, 51-200, etc."
    )
    headquarters = models.CharField(max_length=100, blank=True)
    
    # External links
    linkedin_url = models.URLField(blank=True)
    careers_page_url = models.URLField(
        blank=True,
        help_text="Company's official careers page"
    )
    github_org = models.CharField(
        max_length=100,
        blank=True,
        help_text="GitHub organization handle (e.g., 'google' for github.com/google)"
    )
    
    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text="Admin-verified company"
    )

    # ============ END NEW FIELDS ============

    class Meta:
        db_table = "jobs_company"
        ordering = ["name"]
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class Source(UUIDModel):
    """A job board or source website where jobs are scraped/imported from."""

    SOURCE_TYPE_CHOICES = [
        ("manual", "Manual"),
        ("scraper", "Scraper"),
        ("api", "API"),
    ]

    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    url = models.URLField(max_length=300)
    logo_url = models.URLField(max_length=500, blank=True)
    type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default="manual")
    is_active = models.BooleanField(default=True, db_index=True)

    # ============ NEW FIELDS - ADD THESE ============

    # Scraper configuration
    scraper_class = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Python class name for this scraper"
    )
    schedule_cron = models.CharField(
        max_length=50, 
        default='0 */6 * * *',
        help_text="Cron expression for scraping schedule"
    )
    requires_playwright = models.BooleanField(
        default=False,
        help_text="Whether this source needs headless browser"
    )
    
    # Run status tracking
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(
        max_length=20, 
        default='never',
        choices=[
            ('never', 'Never Run'),
            ('running', 'Running'),
            ('success', 'Success'),
            ('failed', 'Failed'),
        ]
    )
    jobs_found_last_run = models.IntegerField(default=0)
    jobs_added_last_run = models.IntegerField(default=0)
    
    # ATS metadata
    ats_platform = models.CharField(
        max_length=30, 
        blank=True,
        help_text="greenhouse, lever, ashby, etc."
    )
    
    # Error tracking
    error_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)

    # ============ END NEW FIELDS ============

    class Meta:
        db_table = "jobs_source"
        ordering = ["name"]
        verbose_name = "Source"
        verbose_name_plural = "Sources"

    def __str__(self):
        return self.name


class Tag(UUIDModel):
    """A skill or keyword tag that can be associated with jobs."""

    CATEGORY_CHOICES = [
        ("skill", "Skill"),
        ("tool", "Tool"),
        ("language", "Language"),
        ("framework", "Framework"),
        ("general", "General"),
    ]

    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general", db_index=True)

    class Meta:
        db_table = "jobs_tag"
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class Job(UUIDModel):
    """A job listing."""

    LOCATION_TYPE_CHOICES = [
        ("remote", "Remote"),
        ("onsite", "On-Site"),
        ("hybrid", "Hybrid"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("entry", "Entry"),
        ("mid", "Mid"),
        ("senior", "Senior"),
        ("lead", "Lead"),
    ]

    INDUSTRY_CHOICES = [
        ("technology", "Technology"),
        ("finance", "Finance"),
        ("healthcare", "Healthcare"),
        ("education", "Education"),
        ("marketing", "Marketing"),
        ("engineering", "Engineering"),
        ("design", "Design"),
        ("sales", "Sales"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("pending", "Pending Review"),
        ("rejected", "Rejected"),
        ("archived", "Archived"),
        ("expired", "Expired"),
    ]

    QUALITY_STATE_CHOICES = [
        ("active", "Active"),
        ("probably_active", "Probably Active"),
        ("needs_verification", "Needs Verification"),
        ("expired", "Expired"),
        ("archived", "Archived"),
        ("broken", "Broken"),
        ("duplicate", "Duplicate"),
        ("rejected", "Rejected"),
        ("direct_verified", "Direct-source Verified"),
    ]

    QUALITY_ACTIVE_STATES = ("active", "probably_active", "direct_verified")
    QUALITY_VISIBLE_STATES = ("active", "probably_active", "direct_verified", "needs_verification")

    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="jobs", db_index=True
    )
    location = models.CharField(max_length=200, db_index=True)
    location_type = models.CharField(
        max_length=20, choices=LOCATION_TYPE_CHOICES, db_index=True
    )
    industry = models.CharField(
        max_length=50, choices=INDUSTRY_CHOICES, db_index=True
    )
    experience_level = models.CharField(
        max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, db_index=True
    )
    description = models.TextField()
    tags = models.ManyToManyField(Tag, through="JobTag", blank=True, related_name="jobs")
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, blank=True, default="USD")
    source_url = models.URLField(max_length=500)
    source = models.ForeignKey(
        Source, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="jobs", db_index=True
    )
    also_on_sources = models.ManyToManyField(
        Source, through="JobAlsoOnSource", blank=True, related_name="also_on_jobs"
    )
    posted_at = models.DateField(db_index=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", db_index=True
    )
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)

    # ============ NEW FIELDS - ADD THESE ============

    # Core pipeline fields
    direct_apply_url = models.URLField(
        max_length=2000, 
        blank=True,
        db_index=True,
        help_text="Direct link to company's application page (no aggregators)"
    )
    apply_url_verified = models.BooleanField(default=False)
    apply_url_checked_at = models.DateTimeField(null=True, blank=True)
    apply_url_status_code = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Last HTTP status code from URL check"
    )
    
    # Source type classification
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('scraped', 'Scraped from ATS'),
            ('employer_posted', 'Employer Posted'),
        ],
        default='scraped',
        db_index=True
    )
    
    # Job classification
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('freelance', 'Freelance'),
        ],
        null=True, 
        blank=True, 
        db_index=True
    )
    
    # Work arrangement (consolidated from location_type + remote_type)
    WORK_ARRANGEMENT_CHOICES = [
        ('onsite', 'On-site'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    ]
    work_arrangement = models.CharField(
        max_length=10,
        choices=WORK_ARRANGEMENT_CHOICES,
        null=True, 
        blank=True, 
        db_index=True
    )
    
    # Salary information (duplicate fields - kept for backward compatibility during migration)
    # TODO: Remove these after migration is complete
    salary_min_new = models.IntegerField(null=True, blank=True)
    salary_max_new = models.IntegerField(null=True, blank=True)
    salary_currency_new = models.CharField(max_length=3, default='EGP', blank=True)
    
    # Pipeline metadata
    scraped_at = models.DateTimeField(null=True, blank=True)
    source_raw_url = models.URLField(
        max_length=2000, 
        blank=True,
        help_text="Original aggregator URL (not shown to users)"
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False, db_index=True)

    quality_state = models.CharField(
        max_length=20,
        choices=QUALITY_STATE_CHOICES,
        default="needs_verification",
        db_index=True,
    )
    last_verified_at = models.DateTimeField(null=True, blank=True)
    expired_reason = models.CharField(max_length=50, blank=True)
    
    # Legitimacy scoring (Block G)
    legitimacy_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Score from 0.0 to 1.0, higher is more legitimate"
    )
    legitimacy_flags = models.JSONField(
        default=list,
        help_text="List of flags raised by legitimacy checker"
    )
    
    # ATS metadata
    raw_data = models.JSONField(
        null=True, 
        blank=True,
        help_text="Original scraped payload for debugging"
    )
    ats_platform = models.CharField(
        max_length=30, 
        blank=True,
        help_text="greenhouse, lever, ashby, workday, etc."
    )
    ats_job_id = models.CharField(
        max_length=100, 
        blank=True, 
        db_index=True,
        help_text="ATS's own internal job ID"
    )

    # ============ END NEW FIELDS ============

    objects = JobManager()

    class Meta:
        db_table = "jobs_job"
        ordering = ["-posted_at", "-created_at"]
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        # Database indexes for common query patterns
        indexes = [
            models.Index(fields=['company', 'status'], name='jobs_job_company_status_idx'),
            models.Index(fields=['source', 'status'], name='jobs_job_source_status_idx'),
            models.Index(fields=['ats_platform', 'ats_job_id'], name='jobs_job_ats_idx'),
            models.Index(fields=['legitimacy_score'], name='jobs_job_legitimacy_idx'),
            models.Index(fields=['expires_at', 'is_expired'], name='jobs_job_expiry_idx'),
            models.Index(fields=['scraped_at'], name='jobs_job_scraped_idx'),
            models.Index(fields=['direct_apply_url'], name='jobs_job_direct_apply_idx'),
            models.Index(fields=['quality_state'], name='jobs_job_quality_state_idx'),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"


class JobTag(models.Model):
    """Through model for Job ↔ Tag many-to-many."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        db_table = "jobs_jobtag"
        unique_together = [("job", "tag")]

    def __str__(self):
        return f"{self.job} → {self.tag}"


class JobAlsoOnSource(models.Model):
    """Through model for Job ↔ Source also_on_sources many-to-many."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    class Meta:
        db_table = "jobs_jobalsoonsource"
        unique_together = [("job", "source")]

    def __str__(self):
        return f"{self.job} also on {self.source}"