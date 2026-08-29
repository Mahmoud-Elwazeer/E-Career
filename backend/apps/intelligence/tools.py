"""
MCP Tool Registry for platform services.

Exposes platform capabilities as discoverable tools that can be
called by Rashid or any future AI agent. Each tool wraps an
existing platform service — no business logic duplication.
"""
from __future__ import annotations

import structlog
from typing import Any

logger = structlog.get_logger()


class ToolRegistry:
    """Registry of platform tools available to AI agents."""

    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}

    def register(self, name: str, description: str, handler: callable, parameters: dict | None = None):
        """Register a platform tool."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "handler": handler,
            "parameters": parameters or {},
        }

    def list_tools(self) -> list[dict[str, str]]:
        """List all registered tools with descriptions."""
        return [
            {"name": t["name"], "description": t["description"]}
            for t in self._tools.values()
        ]

    def call_tool(self, name: str, **kwargs) -> Any:
        """Execute a registered tool by name."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found. Available: {list(self._tools.keys())}")
        try:
            return tool["handler"](**kwargs)
        except Exception as e:
            logger.error("tool_execution_failed", tool=name, error=str(e))
            raise

    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Get tool metadata by name."""
        return self._tools.get(name)


_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the singleton tool registry with all platform tools registered."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_all_tools(_registry)
    return _registry


def _register_all_tools(registry: ToolRegistry) -> None:
    """Register all platform services as tools."""

    registry.register(
        name="search_jobs",
        description="Search job listings by keyword, location, company, remote status, employment type",
        handler=_tool_search_jobs,
        parameters={
            "query": {"type": "string", "required": True},
            "location": {"type": "string", "required": False},
            "remote": {"type": "boolean", "required": False},
            "employment_type": {"type": "string", "required": False},
            "limit": {"type": "integer", "required": False, "default": 10},
        },
    )

    registry.register(
        name="get_job_detail",
        description="Get full details of a specific job by ID",
        handler=_tool_get_job_detail,
        parameters={
            "job_id": {"type": "string", "required": True},
        },
    )

    registry.register(
        name="get_user_skills",
        description="Get the user's current skills from their career profile",
        handler=_tool_get_user_skills,
        parameters={
            "user_id": {"type": "integer", "required": True},
        },
    )

    registry.register(
        name="get_skill_demand",
        description="Get demand metrics for a specific skill",
        handler=_tool_get_skill_demand,
        parameters={
            "skill_name": {"type": "string", "required": True},
        },
    )

    registry.register(
        name="get_career_paths",
        description="Get possible career paths from a given role",
        handler=_tool_get_career_paths,
        parameters={
            "current_role": {"type": "string", "required": True},
        },
    )

    registry.register(
        name="analyze_cv",
        description="Analyze a user's CV and return structured data",
        handler=_tool_analyze_cv,
        parameters={
            "user_id": {"type": "integer", "required": True},
        },
    )

    registry.register(
        name="get_company_info",
        description="Get information about a company",
        handler=_tool_get_company_info,
        parameters={
            "company_id": {"type": "string", "required": False},
            "company_name": {"type": "string", "required": False},
        },
    )

    registry.register(
        name="get_recommendations",
        description="Get personalized job recommendations for a user",
        handler=_tool_get_recommendations,
        parameters={
            "user_id": {"type": "integer", "required": True},
            "limit": {"type": "integer", "required": False, "default": 5},
        },
    )

    registry.register(
        name="get_application_status",
        description="Get status of user's job applications",
        handler=_tool_get_application_status,
        parameters={
            "user_id": {"type": "integer", "required": True},
        },
    )

    registry.register(
        name="get_market_trends",
        description="Get current job market trends for a skill or industry",
        handler=_tool_get_market_trends,
        parameters={
            "topic": {"type": "string", "required": True},
        },
    )


def _tool_search_jobs(query: str, location: str = "", remote: bool = False,
                      employment_type: str = "", limit: int = 10) -> dict:
    from apps.search.service import SearchService
    service = SearchService()
    filters = {}
    if location:
        filters["location"] = location
    if remote:
        filters["remote"] = True
    if employment_type:
        filters["employment_type"] = employment_type
    results = service.search_jobs(query=query, filters=filters, limit=limit)
    return {"jobs": results, "total": len(results)}


def _tool_get_job_detail(job_id: str) -> dict:
    from apps.jobs.models import Job
    try:
        job = Job.objects.select_related("company").get(id=job_id, status='active')
        return {
            "id": str(job.id),
            "title": job.title,
            "company": job.company.name if job.company else "Unknown",
            "location": job.location or "",
            "description": job.description[:2000] if job.description else "",
            "employment_type": job.employment_type or "",
            "experience_level": job.experience_level or "",
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "apply_url": job.apply_url or "",
            "posted_at": str(job.created_at) if job.created_at else "",
            "tags": list(job.tags.values_list("name", flat=True)),
        }
    except Job.DoesNotExist:
        return {"error": f"Job {job_id} not found or inactive"}


def _tool_get_user_skills(user_id: int) -> dict:
    from apps.career.models import CareerProfile, CareerUserSkill

    skills = CareerUserSkill.objects.filter(user_id=user_id).select_related("skill")
    if skills.exists():
        return {
            "skills": [
                {"name": s.skill.name, "level": s.proficiency_level, "verified": s.is_verified}
                for s in skills
            ]
        }

    try:
        profile = CareerProfile.objects.get(user_id=user_id)
        if profile.cv_parsed_data and profile.cv_parsed_data.get("skills"):
            return {"skills": [{"name": s, "level": "unknown", "verified": False}
                             for s in profile.cv_parsed_data["skills"]]}
    except CareerProfile.DoesNotExist:
        pass

    return {"skills": [], "message": "No skills found. Please upload your CV or add skills manually."}


def _tool_get_skill_demand(skill_name: str) -> dict:
    from apps.jobs.models import Job
    from django.db.models import Count

    active_jobs_with_skill = Job.objects.filter(
        is_active=True,
        tags__name__icontains=skill_name
    ).count()

    total_active = Job.objects.filter(status='active').count()
    percentage = (active_jobs_with_skill / total_active * 100) if total_active > 0 else 0

    return {
        "skill": skill_name,
        "job_count": active_jobs_with_skill,
        "percentage_of_jobs": round(percentage, 1),
        "demand_level": "high" if percentage > 10 else "medium" if percentage > 3 else "low",
    }


def _tool_get_career_paths(current_role: str) -> dict:
    from apps.skills.models import CareerPath

    paths = CareerPath.objects.filter(
        from_occupation__title__icontains=current_role
    ).select_related("to_occupation")[:5]

    if not paths:
        return {"paths": [], "message": f"No career paths found from '{current_role}'."}

    return {
        "paths": [
            {
                "target_role": p.to_occupation.title,
                "transition_difficulty": p.difficulty_level or "unknown",
                "typical_duration": p.typical_duration or "varies",
            }
            for p in paths
        ]
    }


def _tool_analyze_cv(user_id: int) -> dict:
    from apps.career.models import CareerProfile

    try:
        profile = CareerProfile.objects.get(user_id=user_id)
    except CareerProfile.DoesNotExist:
        return {"error": "No CV uploaded. Please upload your CV first."}

    if not profile.cv_parsed_data:
        return {"error": "CV not yet parsed. Please re-upload your CV."}

    data = profile.cv_parsed_data
    return {
        "parsed": True,
        "skills_count": len(data.get("skills", [])),
        "experience_count": len(data.get("experience", [])),
        "education_count": len(data.get("education", [])),
        "skills": data.get("skills", [])[:15],
        "has_contact_info": bool(data.get("email") or data.get("phone")),
        "completeness": _calculate_cv_completeness(data),
    }


def _tool_get_company_info(company_id: str = "", company_name: str = "") -> dict:
    from apps.jobs.models import Company, Job

    try:
        if company_id:
            company = Company.objects.get(id=company_id)
        elif company_name:
            company = Company.objects.filter(name__icontains=company_name).first()
            if not company:
                return {"error": f"Company '{company_name}' not found."}
        else:
            return {"error": "Please provide company_id or company_name."}
    except Company.DoesNotExist:
        return {"error": "Company not found."}

    active_jobs = Job.objects.filter(company=company, status='active').count()
    return {
        "id": str(company.id),
        "name": company.name,
        "industry": company.industry or "Unknown",
        "size": company.size or "Unknown",
        "location": company.headquarters or "",
        "website": company.website or "",
        "active_jobs": active_jobs,
        "description": (company.description or "")[:500],
    }


def _tool_get_recommendations(user_id: int, limit: int = 5) -> dict:
    from apps.search.recommendation_engine import RecommendationEngine

    engine = RecommendationEngine()
    jobs = engine.get_recommendations(user_id=user_id, limit=limit)
    return {"recommendations": jobs[:limit], "count": len(jobs)}


def _tool_get_application_status(user_id: int) -> dict:
    from apps.employers.models import JobApplication

    apps = JobApplication.objects.filter(
        user_id=user_id
    ).select_related("job_posting").order_by("-applied_at")[:10]

    if not apps:
        return {"applications": [], "message": "No applications found."}

    return {
        "applications": [
            {
                "job_title": a.job_posting.title if a.job_posting else "Unknown",
                "company": a.job_posting.company_name if a.job_posting else "Unknown",
                "status": a.status,
                "applied_at": str(a.applied_at),
            }
            for a in apps
        ],
        "total": apps.count() if hasattr(apps, 'count') else len(apps),
    }


def _tool_get_market_trends(topic: str) -> dict:
    from apps.jobs.models import Job
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_60_days = now - timedelta(days=60)

    recent_count = Job.objects.filter(
        status='active',
        created_at__gte=last_30_days,
        tags__name__icontains=topic
    ).count()

    previous_count = Job.objects.filter(
        is_active=True,
        created_at__gte=last_60_days,
        created_at__lt=last_30_days,
        tags__name__icontains=topic
    ).count()

    if previous_count > 0:
        growth = ((recent_count - previous_count) / previous_count) * 100
    else:
        growth = 100 if recent_count > 0 else 0

    return {
        "topic": topic,
        "jobs_last_30_days": recent_count,
        "jobs_previous_30_days": previous_count,
        "growth_percentage": round(growth, 1),
        "trend": "growing" if growth > 10 else "stable" if growth > -10 else "declining",
    }


def _calculate_cv_completeness(data: dict) -> int:
    """Calculate CV completeness percentage."""
    score = 0
    total = 5
    if data.get("skills"):
        score += 1
    if data.get("experience"):
        score += 1
    if data.get("education"):
        score += 1
    if data.get("email") or data.get("phone"):
        score += 1
    if data.get("name"):
        score += 1
    return int((score / total) * 100)
