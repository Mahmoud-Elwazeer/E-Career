"""
Marketing Intelligence Service.

Provides competitor analysis, market positioning insights, and content
recommendations based on platform data and external research.

Capabilities:
- Competitor job posting analysis
- Market gap identification
- Content opportunity scoring
- Platform growth metrics
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import timedelta

from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 60 * 60 * 12


@dataclass
class MarketInsight:
    """A single market insight."""
    category: str
    title: str
    description: str
    data: Dict = field(default_factory=dict)
    confidence: float = 0.8
    actionable: bool = True


@dataclass
class CompetitorProfile:
    """Competitor analysis profile."""
    name: str
    job_count: int = 0
    top_skills: List[str] = field(default_factory=list)
    avg_salary: Optional[float] = None
    growth_rate: float = 0.0
    market_position: str = "unknown"


class MarketingIntelligenceService:
    """
    Analyzes market positioning and competitive landscape.
    """

    def get_platform_metrics(self) -> Dict:
        """Get current platform health and growth metrics."""
        cache_key = "marketing:platform_metrics"
        cached = cache.get(cache_key)
        if cached:
            return cached

        from apps.jobs.models import Job, Company
        from apps.accounts.models import User

        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        metrics = {
            "total_jobs": Job.objects.filter(is_expired=False).count(),
            "jobs_added_7d": Job.objects.filter(created_at__gte=week_ago).count(),
            "jobs_added_30d": Job.objects.filter(created_at__gte=month_ago).count(),
            "total_companies": Company.objects.count(),
            "new_companies_30d": Company.objects.filter(created_at__gte=month_ago).count(),
            "total_users": User.objects.filter(is_active=True).count(),
            "new_users_7d": User.objects.filter(date_joined__gte=week_ago).count(),
            "new_users_30d": User.objects.filter(date_joined__gte=month_ago).count(),
        }

        total_prev_month = Job.objects.filter(
            created_at__gte=month_ago - timedelta(days=30),
            created_at__lt=month_ago,
        ).count()
        if total_prev_month > 0:
            metrics["job_growth_rate"] = round(
                (metrics["jobs_added_30d"] - total_prev_month) / total_prev_month * 100, 1
            )
        else:
            metrics["job_growth_rate"] = 0

        cache.set(cache_key, metrics, CACHE_TIMEOUT)
        return metrics

    def get_market_gaps(self) -> List[MarketInsight]:
        """
        Identify market gaps — roles/skills with high demand but low supply on platform.
        """
        from apps.jobs.models import Job
        from apps.skills.models import JobSkill, Skill

        insights = []

        high_demand_skills = (
            JobSkill.objects.filter(job__is_expired=False)
            .values('skill__name')
            .annotate(job_count=Count('job', distinct=True))
            .order_by('-job_count')[:20]
        )

        for item in high_demand_skills:
            skill_name = item['skill__name']
            job_count = item['job_count']

            from apps.career.models import CareerProfile
            user_count = CareerProfile.objects.filter(
                skills__name__iexact=skill_name
            ).count() if hasattr(CareerProfile, 'skills') else 0

            if job_count > 10 and user_count < job_count * 0.3:
                insights.append(MarketInsight(
                    category="skill_gap",
                    title=f"High demand, low supply: {skill_name}",
                    description=f"{job_count} jobs require {skill_name} but only {user_count} users have it.",
                    data={"skill": skill_name, "jobs": job_count, "users": user_count},
                    confidence=0.85,
                ))

        return insights[:10]

    def get_content_opportunities(self) -> List[MarketInsight]:
        """
        Identify content opportunities based on search patterns and gaps.
        """
        from apps.jobs.models import Job

        now = timezone.now()
        month_ago = now - timedelta(days=30)

        top_roles = (
            Job.objects.filter(is_expired=False, created_at__gte=month_ago)
            .values('title')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        opportunities = []
        for item in top_roles:
            role = item['title']
            count = item['count']
            opportunities.append(MarketInsight(
                category="content_opportunity",
                title=f"Career guide opportunity: {role}",
                description=f"{count} active jobs for {role}. Generate career guide + interview prep.",
                data={"role": role, "job_count": count},
                confidence=0.75,
            ))

        return opportunities

    def get_industry_breakdown(self) -> Dict:
        """Get job distribution by industry/category."""
        from apps.jobs.models import Job

        breakdown = (
            Job.objects.filter(is_expired=False)
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count')[:15]
        )

        return {
            "industries": [
                {"name": item['category'] or "Other", "count": item['count']}
                for item in breakdown
            ],
        }

    def get_location_insights(self) -> Dict:
        """Get job distribution and trends by location."""
        from apps.jobs.models import Job

        location_data = (
            Job.objects.filter(is_expired=False)
            .values('location')
            .annotate(count=Count('id'))
            .order_by('-count')[:20]
        )

        remote_count = Job.objects.filter(
            is_expired=False, remote_type='remote'
        ).count()
        total = Job.objects.filter(is_expired=False).count()

        return {
            "top_locations": [
                {"location": item['location'] or "Not specified", "count": item['count']}
                for item in location_data
            ],
            "remote_percentage": round(remote_count / max(total, 1) * 100, 1),
            "total_jobs": total,
        }


_marketing_service: Optional[MarketingIntelligenceService] = None


def get_marketing_intelligence() -> MarketingIntelligenceService:
    global _marketing_service
    if _marketing_service is None:
        _marketing_service = MarketingIntelligenceService()
    return _marketing_service
