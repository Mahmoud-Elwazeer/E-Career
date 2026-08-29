from django.db import models
from apps.core.models import UUIDModel


class VerificationResult(UUIDModel):
    """Stores the full verification outcome for a job listing."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]

    job = models.OneToOneField(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="verification",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    trust_score = models.FloatField(default=0.0, db_index=True)

    # Stage 1: ATS Fingerprinting
    ats_platform_detected = models.CharField(max_length=50, blank=True)
    ats_confidence = models.FloatField(default=0.0)

    # Stage 2: Redirect Resolution
    final_url = models.URLField(max_length=2000, blank=True)
    redirect_chain = models.JSONField(default=list)
    redirect_count = models.IntegerField(default=0)

    # Stage 3: Domain Verification
    domain_trust = models.FloatField(default=0.0)
    domain_matches_company = models.BooleanField(default=False)
    ssl_valid = models.BooleanField(default=False)

    # Stage 4: Legitimacy Scoring
    legitimacy_score = models.FloatField(default=0.0)
    legitimacy_flags = models.JSONField(default=list)

    # Stage 5: Freshness & Liveness
    url_accessible = models.BooleanField(default=False)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.IntegerField(default=0)
    http_status_code = models.IntegerField(null=True, blank=True)

    # Stage 6: Deduplication
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.ForeignKey(
        "jobs.Job",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicates",
    )
    content_hash = models.CharField(max_length=64, blank=True, db_index=True)

    # Admin Override
    admin_override = models.BooleanField(
        default=False,
        help_text="Admin manually approved/rejected this verification"
    )
    override_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_overrides'
    )
    override_reason = models.TextField(blank=True)
    override_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_duration_ms = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "verification_result"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "trust_score"]),
            models.Index(fields=["content_hash"]),
        ]

    def __str__(self):
        return f"Verification({self.job_id}) → {self.status} ({self.trust_score:.2f})"


class BlockedDomain(UUIDModel):
    """
    Admin-managed list of blocked application domains.
    
    Jobs with apply URLs on these domains are automatically rejected
    because they redirect to intermediary application platforms instead
    of the actual employer.
    """
    
    domain = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Blocked domain (e.g., apply.indeed.com, linkedin.com/jobs/apply)"
    )
    
    reason = models.TextField(
        help_text="Why this domain is blocked (e.g., 'Intermediary application platform')"
    )
    
    added_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blocked_domains_added'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to temporarily disable this block"
    )
    
    class Meta:
        db_table = "verification_blocked_domain"
        ordering = ['domain']
        verbose_name = "Blocked Domain"
        verbose_name_plural = "Blocked Domains"
    
    def __str__(self):
        return f"Blocked: {self.domain}"


class ApprovedATS(UUIDModel):
    """
    Admin-managed list of approved ATS (Applicant Tracking System) domains.
    
    Jobs with apply URLs on these domains are automatically verified
    because they are known legitimate employer-owned ATS platforms.
    """
    
    domain = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Approved ATS domain (e.g., greenhouse.io, lever.co)"
    )
    
    name = models.CharField(
        max_length=100,
        help_text="ATS platform name (e.g., 'Greenhouse', 'Lever')"
    )
    
    url_pattern = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional URL pattern regex for matching (e.g., 'boards.greenhouse.io/*')"
    )
    
    added_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_ats_added'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to temporarily disable this approval"
    )
    
    class Meta:
        db_table = "verification_approved_ats"
        ordering = ['name']
        verbose_name = "Approved ATS"
        verbose_name_plural = "Approved ATS Platforms"
    
    def __str__(self):
        return f"{self.name} ({self.domain})"


_blocked_cache = None
_blocked_cache_ts = 0


def get_blocked_domains():
    """Return the set of blocked domains, cached for 5 minutes."""
    import time
    global _blocked_cache, _blocked_cache_ts
    now = time.monotonic()
    if _blocked_cache is None or (now - _blocked_cache_ts) > 300:
        _blocked_cache = set(
            BlockedDomain.objects.filter(is_active=True)
            .values_list('domain', flat=True)
        )
        _blocked_cache_ts = now
    return _blocked_cache


def is_blocked_domain(domain: str) -> bool:
    """Check if a domain (or any of its parents) is in the blocklist."""
    blocked = get_blocked_domains()
    return any(b in domain for b in blocked)
