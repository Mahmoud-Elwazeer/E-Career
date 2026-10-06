from django.conf import settings
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
    """An organization that posts jobs / hires on the platform.

    `org_type` is the Organization-layer dimension: the SAME Company +
    EmployerProfile + EmployerTeamMember + CompanySubscription stack serves a
    business, a government body, a university, or an NGO — distinguished by this
    field, not by a parallel model or a second auth system. New audiences reuse
    the single User identity and the existing team/role/billing/entitlement
    machinery; only product copy and (optionally) entitlement plans differ.
    """

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

    ORG_TYPE_CHOICES = [
        ("business", "Business"),
        ("government", "Government"),
        ("university", "University"),
        ("ngo", "NGO / Non-profit"),
    ]

    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    org_type = models.CharField(
        max_length=20, choices=ORG_TYPE_CHOICES, default="business", db_index=True,
        help_text="Organization kind — reuses the same hiring/team/billing stack for all audiences",
    )
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


class CompanyResolutionIdentity(UUIDModel):
    """A cached, evidence-backed mapping from (ATS platform, tenant slug) to
    the ONE canonical Company (§11 Company Resolution Service).

    This is the persisted memory of CompanyResolutionService
    (apps/jobs/company_resolution.py). Without it, every ingestion run has to
    re-derive "which Company is this?" from a slug/name heuristic every time,
    and two different ATS tenants for the SAME real employer (e.g. a company
    scraped via both -greenhouse and, after a later ATS migration, -lever)
    have no way to collapse onto one Company short of exact slug luck. Once a
    (platform, tenant_slug) pair has been resolved once, this table makes the
    next resolution a direct, explainable lookup instead of a fresh guess —
    and it is also the evidence trail a future "claim this company" workflow
    needs (which ATS tenants were ever observed for this canonical Company,
    and on what basis).
    """

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="resolution_identities",
    )
    platform = models.CharField(
        max_length=30, db_index=True,
        help_text="ATS platform this tenant was observed on (greenhouse, lever, ashby, ...)",
    )
    tenant_slug = models.CharField(
        max_length=150, db_index=True,
        help_text="The company's slug/tenant id on that ATS platform",
    )
    domain = models.CharField(
        max_length=255, blank=True,
        help_text="Company domain observed at the time this identity was resolved, if any",
    )
    source = models.ForeignKey(
        "jobs.Source", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resolved_company_identities",
        help_text="The scraper Source this identity was first resolved from, if any",
    )
    confidence = models.FloatField(
        default=1.0, help_text="How confident this (platform, tenant_slug) -> Company mapping is",
    )
    matched_by = models.CharField(
        max_length=20, blank=True,
        help_text="How this identity's Company was determined: domain | slug | created",
    )
    evidence = models.JSONField(
        default=dict, blank=True, help_text="Supporting evidence for this resolution (auditability)",
    )

    class Meta:
        db_table = "jobs_company_resolution_identity"
        unique_together = [("platform", "tenant_slug")]
        verbose_name = "Company Resolution Identity"
        verbose_name_plural = "Company Resolution Identities"
        indexes = [
            models.Index(fields=["company"], name="jobs_cri_company_idx"),
        ]

    def __str__(self):
        return f"{self.platform}:{self.tenant_slug} -> {self.company.name}"


class CompanyClaim(UUIDModel):
    """An employer user's claim of ownership over an existing (usually
    scraper-created) Company row (Task #12, Company Claim workflow).

    Why this exists: EmployerRegistrationView already lets any authenticated
    user attach themselves to ANY existing active Company by id with zero
    proof of ownership (see apps/employers/views.py). CompanyClaim is the
    evidence-gated alternative for claiming a company that was discovered via
    scraping (has scraper-sourced jobs already) rather than created fresh by
    an employer — the attach-with-no-proof path remains for brand-new
    companies an employer creates themselves (create_company), which is a
    different, already-self-evident case (you can't "claim" what you just
    created).

    Evidence types (per the directive — same-name or free-mail claims are
    NEVER sufficient on their own):
      - corporate_email: claimant's account email domain matches
        Company.domain (or a domain discovered for this company via
        CompanyResolutionIdentity). Auto-approvable only when domain match is
        exact and the email is not a known free-mail provider.
      - dns_txt: claimant adds a TXT record under their own domain containing
        a verification token this platform generated (website-ownership
        proof independent of email). Verified via a live DNS TXT lookup.
      - document: claimant uploads a document (incorporation certificate,
        business registration, letterhead) for manual admin review. Always
        requires VERIFICATION_REQUIRED -> UNDER_REVIEW -> admin decision.
      - admin_manual: an admin creates/approves a claim directly (e.g. after
        an out-of-band support conversation), bypassing automated evidence.

    State machine (directive-specified): PENDING -> VERIFICATION_REQUIRED ->
    UNDER_REVIEW -> APPROVED | REJECTED. An APPROVED claim can later be
    REVOKED by an admin (company sold, fraud discovered after the fact, etc).
    Approval does NOT delete or alter the Company's existing scraped jobs or
    CompanyResolutionIdentity history — it only grants the claimant an
    EmployerProfile/EmployerTeamMember(role='owner') on that SAME Company row
    (see apps/jobs/company_claim.py::CompanyClaimService.approve), so already
    -ingested jobs are retroactively "theirs" with no duplication.
    """

    STATUS_PENDING = "pending"
    STATUS_VERIFICATION_REQUIRED = "verification_required"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_VERIFICATION_REQUIRED, "Verification Required"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_REVOKED, "Revoked"),
    ]

    EVIDENCE_CORPORATE_EMAIL = "corporate_email"
    EVIDENCE_DNS_TXT = "dns_txt"
    EVIDENCE_DOCUMENT = "document"
    EVIDENCE_ADMIN_MANUAL = "admin_manual"
    EVIDENCE_CHOICES = [
        (EVIDENCE_CORPORATE_EMAIL, "Corporate Email Domain Match"),
        (EVIDENCE_DNS_TXT, "DNS TXT Record Challenge"),
        (EVIDENCE_DOCUMENT, "Uploaded Document (Manual Review)"),
        (EVIDENCE_ADMIN_MANUAL, "Admin Manual Verification"),
    ]

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="claims",
    )
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_claims",
    )
    status = models.CharField(
        max_length=25, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True,
    )
    evidence_type = models.CharField(
        max_length=20, choices=EVIDENCE_CHOICES, db_index=True,
        help_text="How the claimant is proving ownership",
    )
    claimant_email_domain = models.CharField(
        max_length=255, blank=True,
        help_text="Domain portion of claimant's account email at claim time (for corporate_email evidence)",
    )
    is_free_mail_domain = models.BooleanField(
        default=False,
        help_text="True if claimant_email_domain is a known free/consumer mail provider (gmail.com, etc) - such a match is NEVER sufficient evidence on its own",
    )
    dns_challenge_token = models.CharField(
        max_length=64, blank=True,
        help_text="Random token the claimant must publish as a TXT record (dns_txt evidence only)",
    )
    dns_verified_at = models.DateTimeField(null=True, blank=True)
    confidence = models.FloatField(
        default=0.0,
        help_text="Automated confidence this claim's evidence proves real ownership (0.0-1.0); NEVER auto-approves above a conservative threshold - admin review is always the final gate for anything but an exact dns_txt or corporate_email match on a non-free domain",
    )
    evidence = models.JSONField(
        default=dict, blank=True,
        help_text="Supporting evidence detail (domain comparison, DNS lookup result, document reference, admin note)",
    )
    document = models.FileField(
        upload_to="company_claim_documents/", null=True, blank=True,
        help_text="Uploaded proof document for 'document' evidence type",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="company_claims_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    class Meta:
        db_table = "jobs_company_claim"
        ordering = ["-created_at"]
        verbose_name = "Company Claim"
        verbose_name_plural = "Company Claims"
        indexes = [
            models.Index(fields=["company", "status"], name="jobs_claim_company_status_idx"),
        ]
        constraints = [
            # A claimant may have at most one ACTIVE (non-terminal) claim per
            # company at a time - resubmission after rejection is allowed
            # (rejected/revoked are terminal, not "active"), but you can't
            # have two pending claims for the same company simultaneously.
            models.UniqueConstraint(
                fields=["company", "claimant"],
                condition=models.Q(status__in=["pending", "verification_required", "under_review"]),
                name="uniq_active_claim_per_company_claimant",
            ),
        ]

    def __str__(self):
        return f"{self.claimant} claims {self.company.name} ({self.status})"


class CompanyEnrichment(UUIDModel):
    """Persisted provenance for Company Discovery Engine enrichment
    decisions (Task #13 — Company Discovery Engine).

    Append-only evidence log: one row per enrichment attempt for a given
    field on a given run, whether or not it was actually applied. A recorded
    conflict is as valuable as a recorded application — it tells an admin
    "we found evidence of X but your existing value Y was left alone",
    rather than silently either overwriting or discarding the signal.

    Hard invariant: `applied=True` only ever happens for a Company field
    that was BLANK at the time this row was written. This service NEVER
    overwrites an existing value, regardless of how confident the new
    evidence is — the same conservative, additive-only policy already used
    by CompanyResolutionService._backfill_name_if_placeholder (only backfill
    a placeholder, never clobber a real value) and by CompanyClaimService
    (evidence informs, a human always decides). A `conflict=True` row means
    the field already has a value AND the newly observed evidence disagrees
    with it — flagged for human review, nothing is touched automatically.
    """

    FIELD_CHOICES = [
        ("domain", "Domain"),
        ("careers_page_url", "Careers Page URL"),
        ("industry", "Industry"),
        ("headquarters", "Headquarters"),
    ]

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="enrichments",
    )
    field_name = models.CharField(max_length=30, choices=FIELD_CHOICES, db_index=True)
    value = models.CharField(max_length=500)
    method = models.CharField(
        max_length=40,
        help_text=(
            "How this value was derived: resolution_identity_domain | "
            "ats_board_url_pattern | source_industry_backfill | "
            "job_location_majority. Every method reuses evidence this "
            "platform already ingested — none of them scrape or fabricate "
            "new external data."
        ),
    )
    confidence = models.FloatField(default=0.0)
    evidence = models.JSONField(default=dict, blank=True)
    applied = models.BooleanField(
        default=False,
        help_text="True if this value was actually written to the Company field (only ever happens when that field was blank)",
    )
    conflict = models.BooleanField(
        default=False,
        help_text="True if this evidence disagrees with an existing non-blank Company field value (flagged for admin review, never auto-overwritten)",
    )

    class Meta:
        db_table = "jobs_company_enrichment"
        ordering = ["-created_at"]
        verbose_name = "Company Enrichment"
        verbose_name_plural = "Company Enrichments"
        indexes = [
            models.Index(fields=["company", "field_name"], name="jobs_enrich_company_field_idx"),
        ]

    def __str__(self):
        return f"{self.company.name}.{self.field_name} = {self.value} ({self.method})"


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

    # ── §4 Source registry field audit (production-scale directive) ──
    # Added ONLY fields with a real, wired consumer in this same change (or
    # the immediately-following anomaly-detection work) — NOT a blind copy of
    # the directive's full wishlist. Fields deliberately NOT added, with the
    # reason, so the omission is a decision rather than a silent gap:
    #   priority            - no priority-aware dispatch loop exists; sources
    #                         are processed in Source.objects order today.
    #                         Adding this field with nothing reading it would
    #                         be exactly the "dead metadata" anti-pattern the
    #                         directive itself warns against.
    #   trust_level         - already COMPUTED per-job from real evidence by
    #                         legitimacy.calculate_source_trust() (ats
    #                         platform + job id + apply url presence). A
    #                         stored per-Source field would duplicate and
    #                         could drift from the authoritative computed
    #                         value - the computed version is strictly
    #                         better, so no field was added.
    #   acquisition_strategy - this is exactly what StrategyRouter.decide_route()
    #                         computes dynamically from ats_platform/
    #                         requires_playwright/type. Storing a parallel
    #                         static field would let it desync from the real
    #                         routing decision.
    #   discovery_only, AI_allowed - no discovery-only source or Tier-4 AI
    #                         runner exists yet in this codebase (Crawl4AI/
    #                         ScrapeGraphAI remain DEFER per the audit doc) -
    #                         there is nothing to read these flags yet. Will
    #                         add when a real consumer exists, not before.
    #   rediscovery_state   - redundant with the existing lifecycle_state
    #                         (active/degraded/migrated/disabled/invalid) +
    #                         last_discovery_at, added in the §9/§10 work.
    #   consecutive_failures - redundant with existing error_count, which
    #                         tasks.py already resets to 0 on every success -
    #                         it already IS a consecutive-failure counter.
    #   zero_yield_count    - redundant with existing
    #                         consecutive_zero_yield_runs (§9/§10).
    country = models.CharField(
        max_length=80, blank=True, db_index=True,
        help_text="Primary country this source's postings target (admin/matrix metadata)",
    )
    region = models.CharField(
        max_length=80, blank=True,
        help_text="Region/market grouping (e.g. MENA, EU, NA) - admin/matrix metadata",
    )
    industry = models.CharField(
        max_length=80, blank=True,
        help_text="Industry focus if this source is industry-specific (free text, admin metadata)",
    )
    adaptive_allowed = models.BooleanField(
        default=True,
        help_text=(
            "If False, this source's Tier-3 adaptive (Scrapling) fallback is "
            "disabled even if its platform is unstructured - an admin "
            "kill-switch for a specific flaky/legal-sensitive source without "
            "having to disable adaptive extraction platform-wide. Read by "
            "apps.scraper.tasks._adaptive_fallback_runner."
        ),
    )
    rate_limit_override = models.IntegerField(
        null=True, blank=True,
        help_text=(
            "Requests/minute override for this source, replacing the "
            "platform-wide default in ScraperOrchestrator.RATE_LIMITS. "
            "Null = use the platform default."
        ),
    )
    max_jobs_per_run = models.IntegerField(
        null=True, blank=True,
        help_text=(
            "Hard cap on jobs persisted from a single run of this source "
            "(bounded-ingestion control for scale testing / a newly-added "
            "source). Null = no cap."
        ),
    )
    last_success_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Last run that completed without a fetch/dispatch exception "
                  "(distinct from last_run_at, which also records failed runs)",
    )
    last_failure_at = models.DateTimeField(null=True, blank=True)
    last_nonzero_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Last run where jobs_found_last_run > 0 - lets anomaly "
                  "detection measure exactly how long a source has been "
                  "silently zero, not just whether its LAST run was zero.",
    )
    historical_average_jobs = models.FloatField(
        default=0.0,
        help_text=(
            "Exponential moving average of jobs_found_last_run across runs, "
            "updated each run. Consumed by anomaly detection to flag "
            "'historical average 700, current run 0' style regressions "
            "instead of comparing against a hardcoded threshold."
        ),
    )
    TERMS_REVIEW_CHOICES = [
        ("not_required", "Not Required"),
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    terms_review_status = models.CharField(
        max_length=20, choices=TERMS_REVIEW_CHOICES, default="not_required",
        help_text="ToS/robots.txt compliance review status for this source",
    )
    legal_review_status = models.CharField(
        max_length=20, choices=TERMS_REVIEW_CHOICES, default="not_required",
        help_text="Legal review status (e.g. required before enabling an "
                  "aggregator-adjacent or outreach-adjacent source)",
    )
    notes = models.TextField(
        blank=True, help_text="Free-text admin notes about this source",
    )

    # ── §9/§10 Source lifecycle state + migration tracking ──
    # ACTIVE     : healthy, ingesting normally
    # DEGRADED   : fetching but not persisting (zero-yield / all-rejected)
    # MIGRATED   : the employer moved ATS; superseded by another Source
    # DISABLED   : intentionally turned off (kept for history)
    # INVALID    : endpoint permanently gone / not a supported provider
    LIFECYCLE_STATE_CHOICES = [
        ("active", "Active"),
        ("degraded", "Degraded"),
        ("migrated", "Migrated"),
        ("disabled", "Disabled"),
        ("invalid", "Invalid"),
    ]
    lifecycle_state = models.CharField(
        max_length=20, choices=LIFECYCLE_STATE_CHOICES, default="active",
        db_index=True,
        help_text="Source health lifecycle (distinct from is_active on/off flag)",
    )
    consecutive_zero_yield_runs = models.IntegerField(
        default=0,
        help_text="Runs in a row that fetched volume but persisted nothing new; "
                  "drives auto-DEGRADED and rediscovery triggers",
    )
    # When this source migrated to another ATS, point at the successor + keep
    # the evidence (old provider/tenant -> new provider/tenant, detected when).
    migrated_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="migrated_from", help_text="Successor source after ATS migration",
    )
    migration_history = models.JSONField(
        default=list, blank=True,
        help_text="Append-only list of migration/rediscovery events with evidence",
    )
    last_discovery_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "jobs_source"
        ordering = ["name"]
        verbose_name = "Source"
        verbose_name_plural = "Sources"
        indexes = [
            models.Index(fields=["lifecycle_state"], name="jobs_source_lifecycle_idx"),
        ]

    def __str__(self):
        return self.name

    def record_migration_event(self, event: dict) -> None:
        """Append a migration/rediscovery event (evidence) without overwriting."""
        history = list(self.migration_history or [])
        history.append(event)
        self.migration_history = history


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
    field_provenance = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Per-field lineage for extracted data. Maps a field name to "
            "{value, source, method, confidence}. Additive; the raw source "
            "payload is preserved separately in raw_data."
        ),
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