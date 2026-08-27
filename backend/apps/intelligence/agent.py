"""
Pydantic AI Agent Framework for the platform.

Provides typed, tool-calling AI agents backed by AWS Bedrock.
The primary agent is Rashid (career advisor), but the framework
supports any domain-specific agent.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

logger = structlog.get_logger()


@dataclass
class PlatformDeps:
    """Dependencies injected into every agent run."""
    user_id: int | None = None
    user_email: str = ""
    user_name: str = ""
    language: str = "en"
    session_id: str = ""


class AgentResponse(BaseModel):
    """Structured response from any platform agent."""
    content: str
    tool_calls: list[dict[str, Any]] = []
    sources: list[str] = []
    confidence: float = 1.0


def get_bedrock_model(model_alias: str = "sonnet") -> str:
    """Resolve model alias to Bedrock model string for Pydantic AI."""
    aliases = {
        "haiku": f"bedrock:anthropic.claude-3-haiku-20240307-v1:0",
        "sonnet": f"bedrock:anthropic.claude-sonnet-4-20250514-v1:0",
    }
    if model_alias in aliases:
        return aliases[model_alias]
    if model_alias.startswith("bedrock:"):
        return model_alias
    return aliases["sonnet"]


def create_rashid_agent() -> Agent[PlatformDeps, str]:
    """Create the Rashid AI career advisor agent."""
    model = get_bedrock_model(
        getattr(settings, "RASHID_MODEL", "sonnet")
    )

    rashid = Agent(
        model,
        deps_type=PlatformDeps,
        system_prompt=_rashid_system_prompt,
        retries=2,
    )

    _register_rashid_tools(rashid)
    return rashid


def _rashid_system_prompt(ctx: RunContext[PlatformDeps]) -> str:
    """Dynamic system prompt based on user context."""
    lang = ctx.deps.language
    name = ctx.deps.user_name or "there"

    if lang == "ar":
        return f"""أنت راشد، مستشار مهني ذكي في منصة يوسام للتوظيف.
تتحدث بالعربية بأسلوب مصري ودود ومحترف.
اسم المستخدم: {name}

مهمتك:
- مساعدة المستخدمين في البحث عن وظائف مناسبة
- تحليل السير الذاتية وتقديم نصائح لتحسينها
- التحضير للمقابلات
- تحليل فجوات المهارات
- تقديم نصائح مهنية مخصصة

استخدم الأدوات المتاحة للوصول إلى بيانات المنصة الفعلية.
لا تختلق معلومات - إذا لم تجد بيانات، أخبر المستخدم بصراحة."""
    else:
        return f"""You are Rashid, an intelligent career advisor on the USAM jobs platform.
You speak in a friendly, professional tone.
User's name: {name}

Your mission:
- Help users find suitable jobs
- Analyze CVs and provide improvement suggestions
- Prepare for interviews
- Identify skill gaps
- Provide personalized career advice

Use available tools to access actual platform data.
Never fabricate information - if no data is found, tell the user honestly."""


def _register_rashid_tools(agent: Agent[PlatformDeps, str]) -> None:
    """Register platform tools on the Rashid agent."""

    @agent.tool
    async def search_jobs(
        ctx: RunContext[PlatformDeps],
        query: str,
        location: str = "",
        remote: bool = False,
        limit: int = 5,
    ) -> str:
        """Search for jobs matching the query. Returns job titles, companies, and links."""
        from apps.search.service import SearchService

        service = SearchService()
        results = service.search_jobs(
            query=query,
            filters={"location": location, "remote": remote} if location or remote else {},
            limit=limit,
        )
        if not results:
            return "No jobs found matching your criteria."

        lines = []
        for job in results[:limit]:
            lines.append(
                f"- **{job.get('title', 'Untitled')}** at {job.get('company_name', 'Unknown')} "
                f"({job.get('location', 'N/A')}) - ID: {job.get('id')}"
            )
        return "\n".join(lines)

    @agent.tool
    async def analyze_skill_gap(
        ctx: RunContext[PlatformDeps],
        job_id: str = "",
        target_role: str = "",
    ) -> str:
        """Analyze the user's skill gap for a specific job or target role."""
        if not ctx.deps.user_id:
            return "User not authenticated. Cannot analyze skills."

        from apps.career.skill_gap_analysis import SkillGapService

        service = SkillGapService()
        if job_id:
            result = service.analyze_for_job(ctx.deps.user_id, job_id)
        elif target_role:
            result = service.analyze_for_role(ctx.deps.user_id, target_role)
        else:
            return "Please specify a job ID or target role for skill gap analysis."

        if not result:
            return "Could not perform skill gap analysis. Please update your profile with your skills."

        lines = ["**Skill Gap Analysis:**"]
        for skill in result.get("missing_skills", []):
            lines.append(f"- Missing: {skill['name']} (importance: {skill.get('importance', 'medium')})")
        for skill in result.get("matching_skills", []):
            lines.append(f"- Match: {skill['name']} ✓")
        if result.get("score"):
            lines.append(f"\n**Match Score:** {result['score']}%")
        return "\n".join(lines)

    @agent.tool
    async def get_career_profile(ctx: RunContext[PlatformDeps]) -> str:
        """Get the user's career profile summary including skills, experience, and talent score."""
        if not ctx.deps.user_id:
            return "User not authenticated."

        from apps.career.models import CareerProfile, TalentScore

        try:
            profile = CareerProfile.objects.get(user_id=ctx.deps.user_id)
        except CareerProfile.DoesNotExist:
            return "No career profile found. Please complete your profile first."

        lines = [f"**Career Profile for {ctx.deps.user_name}:**"]

        if profile.cv_parsed_data:
            data = profile.cv_parsed_data
            if data.get("skills"):
                lines.append(f"- Skills: {', '.join(data['skills'][:10])}")
            if data.get("experience"):
                lines.append(f"- Experience entries: {len(data['experience'])}")
            if data.get("education"):
                lines.append(f"- Education entries: {len(data['education'])}")

        try:
            score = TalentScore.objects.filter(user_id=ctx.deps.user_id).latest("calculated_at")
            lines.append(f"- Talent Score: {score.overall_score}/100")
        except TalentScore.DoesNotExist:
            lines.append("- Talent Score: Not yet calculated")

        return "\n".join(lines)

    @agent.tool
    async def get_recommendations(ctx: RunContext[PlatformDeps], limit: int = 5) -> str:
        """Get personalized job recommendations for the user."""
        if not ctx.deps.user_id:
            return "User not authenticated."

        from apps.search.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()
        jobs = engine.get_recommendations(user_id=ctx.deps.user_id, limit=limit)

        if not jobs:
            return "No recommendations available yet. Complete your profile and add skills to get personalized recommendations."

        lines = ["**Recommended Jobs:**"]
        for job in jobs[:limit]:
            lines.append(
                f"- **{job.get('title')}** at {job.get('company_name')} "
                f"(match: {job.get('score', 0):.0%})"
            )
        return "\n".join(lines)

    @agent.tool
    async def prepare_interview(
        ctx: RunContext[PlatformDeps],
        job_title: str,
        company: str = "",
        focus: str = "general",
    ) -> str:
        """Generate interview preparation material for a specific role."""
        from apps.intelligence import get_ai_service
        from .llm_plugin import LLMRequest

        service = get_ai_service()
        prompt = f"""Generate 5 interview questions for a {job_title} position{f' at {company}' if company else ''}.
Focus area: {focus}
For each question provide:
1. The question
2. What the interviewer is looking for
3. A brief tip for answering well

Format as a clear numbered list."""

        response = service.generate(LLMRequest(
            prompt=prompt,
            system_prompt="You are an expert interview coach.",
            model="haiku",
            max_tokens=1500,
            user_id=ctx.deps.user_id,
        ))
        return response.content

    @agent.tool
    async def get_salary_insights(
        ctx: RunContext[PlatformDeps],
        job_title: str,
        location: str = "",
    ) -> str:
        """Get salary insights for a specific role and location."""
        from apps.salary.models import SalaryData

        filters = {"job_title__icontains": job_title}
        if location:
            filters["location__icontains"] = location

        data = SalaryData.objects.filter(**filters)[:10]
        if not data:
            return f"No salary data available for {job_title}{f' in {location}' if location else ''}."

        salaries = [d.salary_amount for d in data if d.salary_amount]
        if not salaries:
            return "Salary data exists but amounts are not available."

        avg = sum(salaries) / len(salaries)
        min_sal = min(salaries)
        max_sal = max(salaries)
        return (
            f"**Salary Insights for {job_title}:**\n"
            f"- Average: ${avg:,.0f}\n"
            f"- Range: ${min_sal:,.0f} - ${max_sal:,.0f}\n"
            f"- Based on {len(salaries)} data points"
        )


_rashid_agent: Agent[PlatformDeps, str] | None = None


def get_rashid_agent() -> Agent[PlatformDeps, str]:
    """Get or create the singleton Rashid agent."""
    global _rashid_agent
    if _rashid_agent is None:
        _rashid_agent = create_rashid_agent()
    return _rashid_agent
