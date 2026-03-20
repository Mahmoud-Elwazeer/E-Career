from django.db import models
from apps.core.models import UUIDModel


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
        ("archived", "Archived"),
    ]

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

    class Meta:
        db_table = "jobs_job"
        ordering = ["-posted_at", "-created_at"]
        verbose_name = "Job"
        verbose_name_plural = "Jobs"

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
