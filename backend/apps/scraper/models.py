"""Scraper models.

Note: We use existing models from apps.jobs and apps.core:
- Job: stores scraped jobs
- Company: stores company information
- Source: stores scraping sources
- PipelineHealth: tracks scraping pipeline health
- PlatformConfig: stores platform configuration

ScraperRun (§5/§10 of the production-scale directive) is the one genuinely
new model here: a PERSISTED, per-run record of the full ingestion funnel
(fetch -> normalize -> direct-apply -> dedup -> persist -> verify -> index),
including Direct-Apply resolution metrics specifically. Everything it stores
was already being COMPUTED in-memory by RunMetrics
(apps/scraper/pipeline/run_metrics.py) and logged, but never queryable after
the fact — "which source produces the most VERIFIED DIRECT APPLY jobs?"
previously required grepping logs. This model makes that a real query.
"""
from django.db import models
from apps.core.models import UUIDModel


class ScraperRunQuerySet(models.QuerySet):
    def for_source(self, source):
        return self.filter(source=source)

    def recent(self, n: int = 20):
        return self.order_by("-started_at")[:n]


class ScraperRun(UUIDModel):
    """One record per orchestrator._process_jobs() invocation for a Source.

    Direct-Apply resolution metrics (§8) are the fields that answer the
    directive's two distinct questions:
      "Which source produces the most jobs?"              -> fetched
      "Which source produces the most VERIFIED DIRECT APPLY jobs?"
                                                            -> direct_apply_verified
    The second matters more per the platform's moat rule, and previously had
    no persisted, queryable answer across runs/sources.
    """

    source = models.ForeignKey(
        "jobs.Source", on_delete=models.CASCADE, related_name="scraper_runs",
    )
    provider = models.CharField(max_length=30, blank=True)
    strategy_tier = models.CharField(
        max_length=20, blank=True,
        help_text="Which StrategyRouter tier handled this run (STRUCTURED/HTTP/BROWSER/ADAPTIVE/AI/AGENTIC)",
    )

    started_at = models.DateTimeField(db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Funnel counts - mirror RunMetrics.to_dict() exactly, persisted.
    fetched = models.IntegerField(default=0)
    normalized = models.IntegerField(default=0)
    created = models.IntegerField(default=0)
    updated = models.IntegerField(default=0)
    duplicates = models.IntegerField(default=0)
    verified = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)
    publishable = models.IntegerField(default=0)
    indexed = models.IntegerField(default=0)

    # §8 Direct-Apply resolution metrics - the directive's explicit ask.
    direct_apply_candidates = models.IntegerField(
        default=0, help_text="Jobs that had a non-empty apply URL to evaluate",
    )
    direct_apply_verified = models.IntegerField(
        default=0, help_text="Jobs whose apply URL passed the direct/moat gate",
    )

    rejected_total = models.IntegerField(default=0)
    rejected_breakdown = models.JSONField(default=dict, blank=True)
    degraded = models.BooleanField(default=False, db_index=True)
    zero_yield_anomaly = models.BooleanField(default=False, db_index=True)

    objects = ScraperRunQuerySet.as_manager()

    class Meta:
        db_table = "scraper_run"
        ordering = ["-started_at"]
        verbose_name = "Scraper Run"
        verbose_name_plural = "Scraper Runs"
        indexes = [
            models.Index(fields=["source", "-started_at"], name="scraper_run_source_time_idx"),
        ]

    def __str__(self):
        return f"{self.source.slug} @ {self.started_at:%Y-%m-%d %H:%M} ({self.created} created)"

    @property
    def direct_apply_resolution_rate(self) -> float:
        """§8: fraction of direct-apply CANDIDATES that were actually
        VERIFIED direct-apply (not aggregator/intermediary/dead link).
        0.0 when there were no candidates, not a divide-by-zero crash."""
        if not self.direct_apply_candidates:
            return 0.0
        return round(self.direct_apply_verified / self.direct_apply_candidates, 4)

    @classmethod
    def record(cls, source, metrics_dict: dict, *, strategy_tier: str = "", started_at=None, finished_at=None):
        """Persist one RunMetrics.to_dict() output as a ScraperRun row.

        Thin adapter so orchestrator._process_jobs doesn't need to know this
        model's field names - it just passes the dict it already builds.
        """
        from django.utils import timezone
        now = timezone.now()
        return cls.objects.create(
            source=source,
            provider=metrics_dict.get("provider", ""),
            strategy_tier=strategy_tier,
            started_at=started_at or now,
            finished_at=finished_at or now,
            fetched=metrics_dict.get("fetched", 0),
            normalized=metrics_dict.get("normalized", 0),
            created=metrics_dict.get("created", 0),
            updated=metrics_dict.get("updated", 0),
            duplicates=metrics_dict.get("duplicates", 0),
            verified=metrics_dict.get("verified", 0),
            errors=metrics_dict.get("errors", 0),
            publishable=metrics_dict.get("publishable", 0),
            indexed=metrics_dict.get("indexed", 0),
            direct_apply_candidates=metrics_dict.get("direct_apply_candidate", 0),
            direct_apply_verified=metrics_dict.get("direct_apply_verified", 0),
            rejected_total=metrics_dict.get("rejected_total", 0),
            rejected_breakdown=metrics_dict.get("rejected", {}) or {},
            degraded=bool(metrics_dict.get("degraded", False)),
            zero_yield_anomaly=bool(metrics_dict.get("zero_yield_anomaly", False)),
        )
