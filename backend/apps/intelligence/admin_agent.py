"""
Admin AI Copilot Agent.

Separate pydantic-ai agent with admin-scoped tools.
Privilege-separated from the user-facing Rashid agent.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

logger = structlog.get_logger()


@dataclass
class AdminDeps:
    admin_id: int | None = None
    admin_email: str = ""


def create_admin_agent() -> Agent[AdminDeps, str]:
    from .agent import get_bedrock_model

    model = get_bedrock_model("haiku")

    agent = Agent(
        model,
        deps_type=AdminDeps,
        system_prompt=_admin_system_prompt,
        retries=2,
    )

    _register_admin_tools(agent)
    return agent


def _admin_system_prompt(ctx: RunContext[AdminDeps]) -> str:
    return f"""You are the E-Career Admin Copilot, an AI assistant for platform administrators.
Admin: {ctx.deps.admin_email}

You help administrators understand platform health, scraping status, AI costs,
talent pool statistics, and verification anomalies. Use the available tools to
fetch real data — never fabricate numbers.

For any action that would change platform state (pausing a source, overriding
a verification), describe what you WOULD do and ask the admin to confirm via
the admin dashboard UI. Do not execute destructive actions directly."""


def _register_admin_tools(agent: Agent[AdminDeps, str]) -> None:

    @agent.tool
    async def get_system_health(ctx: RunContext[AdminDeps]) -> str:
        """Check platform health: database, Redis, Celery workers, email accounts."""
        from django.db import connection
        from django.core.cache import cache

        checks = []

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks.append("Database: healthy")
        except Exception as e:
            checks.append(f"Database: error — {e}")

        try:
            cache.set("admin_copilot_health", "ok", 10)
            val = cache.get("admin_copilot_health")
            checks.append("Redis: healthy" if val == "ok" else "Redis: error")
        except Exception:
            checks.append("Redis: error")

        try:
            from celery import current_app
            stats = current_app.control.inspect().stats()
            if stats:
                checks.append(f"Celery: {len(stats)} worker(s) active")
            else:
                checks.append("Celery: no workers detected")
        except Exception:
            checks.append("Celery: error (could not inspect)")

        return "\n".join(checks)

    @agent.tool
    async def get_scraper_health(ctx: RunContext[AdminDeps]) -> str:
        """Get scraping status: sources, job counts, stale sources."""
        from apps.jobs.models import Job, Source
        from django.utils import timezone as tz
        from datetime import timedelta

        sources = Source.objects.all()
        total = sources.count()
        active = sources.filter(is_active=True).count()

        total_jobs = Job.objects.count()
        active_jobs = Job.objects.filter(status="active").count()

        now = tz.now()
        stale = []
        for src in sources.filter(is_active=True):
            last_job = Job.objects.filter(source=src).order_by("-created_at").first()
            if last_job and (now - last_job.created_at) > timedelta(days=2):
                stale.append(src.name)
            elif not last_job:
                stale.append(f"{src.name} (no jobs)")

        lines = [
            f"**Sources:** {active}/{total} active",
            f"**Jobs:** {active_jobs:,} active / {total_jobs:,} total",
        ]
        if stale:
            lines.append(f"**Stale sources ({len(stale)}):** {', '.join(stale[:5])}")
        else:
            lines.append("**All active sources are fresh.**")
        return "\n".join(lines)

    @agent.tool
    async def get_ai_cost_breakdown(
        ctx: RunContext[AdminDeps],
        period: str = "today",
    ) -> str:
        """Get AI cost summary. period: 'today', 'week', or 'month'."""
        from apps.events.models import EventLog
        from django.utils import timezone as tz
        from datetime import timedelta

        now = tz.now()
        if period == "week":
            since = now - timedelta(days=7)
        elif period == "month":
            since = now - timedelta(days=30)
        else:
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)

        events = EventLog.objects.filter(
            event_type="ai_model_called", created_at__gte=since
        )
        total_cost = 0
        by_op = {}
        for ev in events:
            if ev.data:
                cost = float(ev.data.get("cost_usd", 0))
                total_cost += cost
                op = ev.data.get("operation", "unknown")
                by_op[op] = by_op.get(op, 0) + cost

        lines = [
            f"**Period:** {period} (since {since.strftime('%Y-%m-%d %H:%M')})",
            f"**Total cost:** ${total_cost:.4f}",
            f"**Total calls:** {events.count()}",
            "",
            "**By feature:**",
        ]
        for op, cost in sorted(by_op.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {op}: ${cost:.4f}")

        return "\n".join(lines)

    @agent.tool
    async def find_verification_anomalies(ctx: RunContext[AdminDeps]) -> str:
        """Find recent verification anomalies: admin overrides, low trust scores, failures."""
        from apps.verification.models import VerificationResult
        from django.utils import timezone as tz
        from datetime import timedelta

        week_ago = tz.now() - timedelta(days=7)

        overrides = VerificationResult.objects.filter(
            admin_override=True, updated_at__gte=week_ago
        ).count()

        low_trust = VerificationResult.objects.filter(
            trust_score__lt=0.3, created_at__gte=week_ago
        ).count()

        failed = VerificationResult.objects.filter(
            status="failed", created_at__gte=week_ago
        ).count()

        total_week = VerificationResult.objects.filter(
            created_at__gte=week_ago
        ).count()

        lines = [
            f"**Verification anomalies (last 7 days):**",
            f"- Total verifications: {total_week}",
            f"- Admin overrides: {overrides}",
            f"- Low trust score (<0.3): {low_trust}",
            f"- Failed verifications: {failed}",
        ]

        if overrides == 0 and low_trust == 0 and failed == 0:
            lines.append("\nNo anomalies detected — verification pipeline looks healthy.")

        return "\n".join(lines)

    @agent.tool
    async def get_talent_pool_stats(ctx: RunContext[AdminDeps]) -> str:
        """Get talent pool statistics: pool counts, candidate totals."""
        try:
            from apps.employers.models import TalentPool, TalentPoolCandidate
        except ImportError:
            return "Talent pool models not available."

        pools = TalentPool.objects.count()
        active_pools = TalentPool.objects.filter(is_active=True).count()
        total_candidates = TalentPoolCandidate.objects.count()

        return (
            f"**Talent Pools:** {active_pools} active / {pools} total\n"
            f"**Total candidates across all pools:** {total_candidates}"
        )


_admin_agent: Agent[AdminDeps, str] | None = None


def get_admin_agent() -> Agent[AdminDeps, str]:
    global _admin_agent
    if _admin_agent is None:
        _admin_agent = create_admin_agent()
    return _admin_agent
