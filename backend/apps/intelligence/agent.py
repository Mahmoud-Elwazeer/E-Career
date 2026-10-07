"""
Pydantic AI Agent Framework for the platform.

Provides typed, tool-calling AI agents backed by AWS Bedrock.
The primary agent is Rashid (career advisor), but the framework
supports any domain-specific agent.

KNOWN DUPLICATION (flagged, not fixed in this pass — see
audit/PLATFORM_ENGINE_ENRICHMENT_MASTER.md for the full writeup): the tools
registered below via `_register_rashid_tools` are the LIVE tool set actually
invoked by Rashid chat (through `apps.rashid.service._invoke_via_agent`).
`apps/rashid/tools.py` defines a SEPARATE `RashidTool`/`RASHID_TOOLS`
registry with its own `search_jobs`/`recommend_jobs` implementations,
reachable only via `POST /api/rashid/tools/execute/` — it is never called
from this agent and has drifted to a different implementation of the same
two tools. This is exactly the "drifting into separate schemas" anti-pattern
AGENTS.md warns about for `career`/`skills`/`rashid`. Reconciling the two
tool registries is out of scope for this pass; this comment exists so the
next person touching either file sees the other one.
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


def format_evidence_trailer(sources: list[str]) -> str:
    """Format a list of source references as a trailing citation line.

    Evaluated against hydra-db/open-glean (Apache-2.0, 1583 stars): its Deep
    Research feature dedupes retrieval results into a numbered citation list
    appended to the synthesized answer. We don't install Open Glean itself
    (REFERENCE_ONLY — it's a UI shell over a proprietary paid Hydra DB
    backend we don't have access to), but the same idea — tell the user
    exactly which record the tool's answer came from — is cheap to add to
    our own deterministic (non-LLM, direct-DB-query) Rashid tools.

    Returns "" when there's nothing concrete to cite, so tools with no data
    don't get a misleading empty trailer.
    """
    if not sources:
        return ""
    return "\n\n_Source: " + "; ".join(sources) + "_"


def format_career_profile(user_id: int, user_name: str) -> str:
    """Build the Career Profile summary text, with a source trailer citing
    the exact CareerProfile/TalentScore rows the answer was built from.

    Extracted from the `get_career_profile` agent tool so it's callable (and
    testable) as a plain function, independent of pydantic-ai/RunContext and
    without needing a live Bedrock call.
    """
    from apps.career.models import CareerProfile, TalentScore

    try:
        profile = CareerProfile.objects.get(user_id=user_id)
    except CareerProfile.DoesNotExist:
        return "No career profile found. Please complete your profile first."

    sources = [f"CareerProfile#{profile.pk}"]
    lines = [f"**Career Profile for {user_name}:**"]

    if profile.cv_parsed_data:
        data = profile.cv_parsed_data
        if data.get("skills"):
            lines.append(f"- Skills: {', '.join(data['skills'][:10])}")
        if data.get("experience"):
            lines.append(f"- Experience entries: {len(data['experience'])}")
        if data.get("education"):
            lines.append(f"- Education entries: {len(data['education'])}")

    try:
        score = TalentScore.objects.filter(user_id=user_id).latest("last_calculated_at")
        # overall_score is stored 0-1; present as a percentage.
        lines.append(f"- Talent Score: {round(score.overall_score * 100)}/100")
        sources.append(f"TalentScore#{score.pk}")
    except TalentScore.DoesNotExist:
        lines.append("- Talent Score: Not yet calculated")

    return "\n".join(lines) + format_evidence_trailer(sources)


def format_salary_insights(job_title: str, location: str = "") -> str:
    """Build the salary insights text, with a source trailer citing the
    exact SalaryData rows the average/range was computed from.

    Extracted from the `get_salary_insights` agent tool for the same reason
    as `format_career_profile` above.
    """
    from apps.salary.models import SalaryData

    # SalaryData links to Job (title lives on Job); it has no job_title of
    # its own. Filter through the job relation.
    qs = SalaryData.objects.filter(job__title__icontains=job_title)
    if location:
        qs = qs.filter(job__location__icontains=location)
    data = list(qs.select_related("job")[:50])
    if not data:
        return f"No salary data available for {job_title}{f' in {location}' if location else ''}."

    # Prefer explicit min/max; fall back to annualized fields when present.
    lows, highs = [], []
    currency = "USD"
    for d in data:
        lo = d.salary_min if d.salary_min is not None else d.annualized_salary_min
        hi = d.salary_max if d.salary_max is not None else getattr(d, "annualized_salary_max", None)
        if lo is not None:
            lows.append(float(lo))
        if hi is not None:
            highs.append(float(hi))
        if getattr(d, "salary_currency", None):
            currency = d.salary_currency

    if not lows and not highs:
        return "Salary data exists but amounts are not available."

    all_vals = lows + highs
    avg = sum(all_vals) / len(all_vals)
    min_sal = min(lows) if lows else min(all_vals)
    max_sal = max(highs) if highs else max(all_vals)

    sources = [f"SalaryData#{d.pk}" for d in data[:5]]
    if len(data) > 5:
        sources.append(f"+{len(data) - 5} more")

    return (
        f"**Salary Insights for {job_title}:**\n"
        f"- Average: {currency} {avg:,.0f}\n"
        f"- Range: {currency} {min_sal:,.0f} - {currency} {max_sal:,.0f}\n"
        f"- Based on {len(data)} data points"
    ) + format_evidence_trailer(sources)


def format_match_score(user_id: int, job_id: str) -> str:
    """Build the match-score breakdown text, with a source trailer citing
    the exact CareerProfile and Job rows the score was computed from.

    Extracted from the `get_match_score` agent tool for the same reason as
    `format_career_profile` above.
    """
    from apps.career.models import CareerProfile
    from apps.jobs.models import Job
    from apps.profiles.services import MatchingService

    try:
        profile = CareerProfile.objects.get(user_id=user_id)
    except CareerProfile.DoesNotExist:
        return "No career profile found. Please complete your profile first."

    try:
        job = Job.objects.get(uuid=job_id)
    except (Job.DoesNotExist, ValueError):
        return f"Job with ID {job_id} not found."

    service = MatchingService()
    result = service.get_match_breakdown(profile, job)

    lines = [f"**Match Score for '{job.title}':** {result.get('overall_score', 0):.0f}/100"]
    breakdown = result.get("breakdown", {})
    for factor, detail in breakdown.items():
        score = detail.get("score", 0) if isinstance(detail, dict) else detail
        reasoning = detail.get("reasoning", "") if isinstance(detail, dict) else ""
        lines.append(f"- {factor.replace('_', ' ').title()}: {score:.0f}/100{f' — {reasoning}' if reasoning else ''}")

    for strength in result.get("strengths", []):
        lines.append(f"- Strength: {strength}")
    for gap in result.get("gaps", []):
        lines.append(f"- Gap: {gap}")
    if result.get("recommendation"):
        lines.append(f"\n**Recommendation:** {result['recommendation']}")

    sources = [f"CareerProfile#{profile.pk}", f"Job#{job.uuid}"]
    return "\n".join(lines) + format_evidence_trailer(sources)


def get_bedrock_model(model_alias: str = "sonnet") -> str:
    """Resolve model alias to Bedrock model string for Pydantic AI."""
    from apps.intelligence.bedrock_plugin import MODEL_ALIASES
    if model_alias.startswith("bedrock:"):
        return model_alias
    model_id = MODEL_ALIASES.get(model_alias, MODEL_ALIASES.get("sonnet"))
    return f"bedrock:{model_id}"


def _build_rashid_model():
    """Build the Bedrock model for Rashid.

    Prefer an explicit BedrockProvider backed by the SAME boto3 client the app
    configures (region + credentials from settings). Without this, pydantic-ai
    builds its own client with no region and fails at construction with
    'You must provide a region_name'. Falls back to the plain model string if
    the explicit-provider API is unavailable in the installed pydantic-ai.
    """
    from apps.intelligence.bedrock_plugin import MODEL_ALIASES

    alias = getattr(settings, "RASHID_MODEL", "sonnet")
    model_id = MODEL_ALIASES.get(alias, MODEL_ALIASES.get("sonnet"))

    try:
        from pydantic_ai.models.bedrock import BedrockConverseModel
        from pydantic_ai.providers.bedrock import BedrockProvider
        from apps.intelligence.bedrock_client import get_runtime_client

        # Shared factory → same region + credential chain as BedrockLLMPlugin.
        provider = BedrockProvider(bedrock_client=get_runtime_client())
        return BedrockConverseModel(model_id, provider=provider)
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("rashid_model_explicit_provider_failed", error=str(exc))
        return get_bedrock_model(alias)


def create_rashid_agent() -> Agent[PlatformDeps, str]:
    """Create the Rashid AI career advisor agent."""
    model = _build_rashid_model()

    rashid = Agent(
        model,
        deps_type=PlatformDeps,
        instructions=_rashid_system_prompt,
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
        from apps.search.plugins.base import SearchQuery

        filters: dict[str, Any] = {}
        if location:
            filters["location"] = location
        if remote:
            filters["work_arrangement"] = "remote"

        service = SearchService()
        try:
            response = service.search_jobs(
                SearchQuery(q=query, filters=filters, page=1, per_page=limit)
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("rashid_search_jobs_failed", error=str(exc))
            return "Job search is temporarily unavailable. Please try again shortly."

        hits = getattr(response, "hits", []) or []
        if not hits:
            return "No jobs found matching your criteria."

        lines = []
        for hit in hits[:limit]:
            data = getattr(hit, "data", {}) or {}
            lines.append(
                f"- **{data.get('title', 'Untitled')}** at "
                f"{data.get('company_name', 'Unknown')} "
                f"({data.get('location', 'N/A')}) - ID: {data.get('id') or hit.id}"
            )
        return "\n".join(lines)

    @agent.tool
    async def analyze_skill_gap(
        ctx: RunContext[PlatformDeps],
        job_id: str = "",
        target_role: str = "",
    ) -> str:
        """Analyze the user's skill gap against their target roles."""
        if not ctx.deps.user_id:
            return "User not authenticated. Cannot analyze skills."

        from django.contrib.auth import get_user_model
        from apps.career.skill_gap_analysis import SkillGapAnalyzer

        User = get_user_model()
        try:
            user = User.objects.get(id=ctx.deps.user_id)
        except User.DoesNotExist:
            return "User not found."

        try:
            result = SkillGapAnalyzer(user).analyze()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("rashid_skill_gap_failed", error=str(exc))
            return (
                "Could not perform skill gap analysis. Please add target roles "
                "and skills to your career profile first."
            )

        missing = result.get("missing_skills", []) or []
        if not missing and not result.get("gaps_by_role"):
            return (
                "No skill gaps found, or your profile has no target roles yet. "
                "Add target roles to your career profile for a detailed analysis."
            )

        lines = [
            f"**Skill Gap Analysis** (severity: {result.get('gap_severity', 'unknown')}, "
            f"overall gap score: {result.get('overall_gap_score', 0)}):",
        ]
        for skill in missing[:15]:
            lines.append(f"- Missing: {skill}")
        recs = result.get("recommendations", []) or []
        if recs:
            lines.append("\n**Recommendations:**")
            for rec in recs[:5]:
                if isinstance(rec, dict):
                    lines.append(f"- {rec.get('skill', rec.get('title', ''))}: {rec.get('reason', rec.get('resource', ''))}".rstrip(": "))
                else:
                    lines.append(f"- {rec}")
        return "\n".join(lines)

    @agent.tool
    async def get_career_profile(ctx: RunContext[PlatformDeps]) -> str:
        """Get the user's career profile summary including skills, experience, and talent score."""
        if not ctx.deps.user_id:
            return "User not authenticated."
        return format_career_profile(ctx.deps.user_id, ctx.deps.user_name)

    @agent.tool
    async def get_recommendations(ctx: RunContext[PlatformDeps], limit: int = 5) -> str:
        """Get personalized job recommendations for the user."""
        if not ctx.deps.user_id:
            return "User not authenticated."

        if not ctx.deps.user_id:
            return "User not authenticated."

        from django.contrib.auth import get_user_model
        from apps.search.recommendation_engine import RecommendationEngine

        User = get_user_model()
        try:
            user = User.objects.get(id=ctx.deps.user_id)
        except User.DoesNotExist:
            return "User not found."

        try:
            engine = RecommendationEngine(user)
            jobs = engine.get_recommendations(n_recommendations=limit)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("rashid_recommendations_failed", error=str(exc))
            return "Recommendations are temporarily unavailable. Please try again shortly."

        if not jobs:
            return "No recommendations available yet. Complete your profile and add skills to get personalized recommendations."

        lines = ["**Recommended Jobs:**"]
        for job in jobs[:limit]:
            lines.append(
                f"- **{job.get('job_title')}** at {job.get('company_name')} "
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
            operation="interview_prep",
        ))
        return response.content

    @agent.tool
    async def get_salary_insights(
        ctx: RunContext[PlatformDeps],
        job_title: str,
        location: str = "",
    ) -> str:
        """Get salary insights for a specific role and location."""
        return format_salary_insights(job_title, location)

    @agent.tool
    async def get_match_score(
        ctx: RunContext[PlatformDeps],
        job_id: str,
    ) -> str:
        """Get a detailed match score breakdown between the user's profile and a specific job."""
        if not ctx.deps.user_id:
            return "User not authenticated."
        return format_match_score(ctx.deps.user_id, job_id)

    @agent.tool
    async def tailor_resume(
        ctx: RunContext[PlatformDeps],
        job_id: str,
    ) -> str:
        """Tailor the user's resume for a specific job, returning before/after ATS scores and suggestions."""
        if not ctx.deps.user_id:
            return "User not authenticated."

        from django.contrib.auth import get_user_model
        from apps.jobs.models import Job

        User = get_user_model()
        try:
            user = User.objects.get(id=ctx.deps.user_id)
        except User.DoesNotExist:
            return "User not found."

        try:
            job = Job.objects.get(uuid=job_id)
        except (Job.DoesNotExist, ValueError):
            return f"Job with ID {job_id} not found."

        from apps.career.cv_tailor_service import CVTailorService
        service = CVTailorService()
        result = service.tailor_for_job(user, job)

        lines = [
            f"**Resume Tailoring for '{job.title}':**",
            f"- Original ATS Score: {result['original_score']:.0f}/100",
            f"- Tailored ATS Score: {result['tailored_score']:.0f}/100",
            f"- Improvement: +{result['score_delta']:.0f} points",
            f"- Skill Match: {result['skill_match_ratio']:.0%}",
        ]
        if result.get("missing_skills"):
            lines.append(f"- Missing Skills: {', '.join(result['missing_skills'][:8])}")
        if result.get("suggestions"):
            lines.append("\n**Suggestions:**")
            for s in result["suggestions"][:5]:
                lines.append(f"  {s}")
        return "\n".join(lines)

    @agent.tool
    async def find_referral_contacts(
        ctx: RunContext[PlatformDeps],
        company_id: str,
    ) -> str:
        """Find insider connections at a company — E-Career users and public GitHub contributors."""
        if not ctx.deps.user_id:
            return "User not authenticated."

        from django.contrib.auth import get_user_model
        from apps.employers.connections_service import ConnectionsService

        User = get_user_model()
        try:
            user = User.objects.get(id=ctx.deps.user_id)
        except User.DoesNotExist:
            return "User not found."

        service = ConnectionsService()
        try:
            result = service.find_connections(int(company_id), requesting_user=user)
        except Exception as e:
            return f"Could not find connections: {e}"

        company_name = result["company"]["name"]
        ecareer = result.get("ecareer_connections", [])
        github = result.get("github_contributors", [])

        if not ecareer and not github:
            return f"No insider connections found at {company_name}."

        lines = [f"**Connections at {company_name}:** ({result['total_connections']} found)"]
        for c in ecareer[:5]:
            role = f" — {c['current_role']}" if c.get("current_role") else ""
            lines.append(f"- {c['name']}{role} ({c['connection_type'].replace('_', ' ')})")
        for g in github[:5]:
            lines.append(f"- GitHub: @{g['username']} ({g['profile_url']})")
        return "\n".join(lines)


_rashid_agent: Agent[PlatformDeps, str] | None = None


def get_rashid_agent() -> Agent[PlatformDeps, str]:
    """Get or create the singleton Rashid agent."""
    global _rashid_agent
    if _rashid_agent is None:
        _rashid_agent = create_rashid_agent()
    return _rashid_agent
