"""
Pydantic AI Agent Framework for the platform.

Provides typed, tool-calling AI agents backed by AWS Bedrock.
The primary agent is Rashid (career advisor), but the framework
supports any domain-specific agent.

Tool definitions live in `apps.intelligence.tool_registry` (the canonical
registry) — this module just wires each registered tool onto the
pydantic-ai `Agent` as a thin `@agent.tool` wrapper. See that module's
docstring for the history: this used to be two independent, drifting
implementations (`agent.py`'s own tool bodies, plus a separate
`apps/rashid/tools.py` `RASHID_TOOLS` registry reachable only via REST).
Both now call through the same `TOOL_REGISTRY`.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from apps.intelligence.tool_registry import TOOL_REGISTRY, ToolContext

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


def _ctx_from_deps(deps: PlatformDeps, **args: Any) -> ToolContext:
    return ToolContext(
        user_id=deps.user_id,
        user_email=deps.user_email,
        user_name=deps.user_name,
        language=deps.language,
        args=args,
    )


# ─────────────────────────────────────────────────────────────────────────
# Back-compat helpers.
#
# These three names (`format_career_profile`, `format_salary_insights`,
# `format_match_score`) existed before the canonical registry — they're
# kept as plain-function wrappers over `TOOL_REGISTRY.execute()` so any
# existing caller/test continues to work unchanged, including the citation
# trailer behavior from the Open Glean evidence-adaptation pass.
# `format_evidence_trailer` is kept as a direct re-export of the trailer
# formatter now owned by `apps.intelligence.evidence`.
# ─────────────────────────────────────────────────────────────────────────

from apps.intelligence.evidence import format_evidence_trailer  # noqa: E402,F401


def format_career_profile(user_id: int, user_name: str) -> str:
    ctx = ToolContext(user_id=user_id, user_name=user_name)
    return TOOL_REGISTRY.execute("get_career_profile", ctx).with_trailer()


def format_salary_insights(job_title: str, location: str = "") -> str:
    ctx = ToolContext(args={"job_title": job_title, "location": location})
    return TOOL_REGISTRY.execute("get_salary_insights", ctx).with_trailer()


def format_match_score(user_id: int, job_id: str) -> str:
    ctx = ToolContext(user_id=user_id, args={"job_id": job_id})
    return TOOL_REGISTRY.execute("get_match_score", ctx).with_trailer()


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
    """Register platform tools on the Rashid agent.

    Every wrapper here does the SAME thing: build a `ToolContext` from the
    pydantic-ai `RunContext.deps` + the tool's typed arguments, then call
    `TOOL_REGISTRY.execute(name, ctx)` and return `.with_trailer()` (plain
    text, since that's the contract pydantic-ai tools must return). The
    actual business logic lives once, in `apps.intelligence.tool_registry`.

    Typed parameters are kept on each wrapper (not collapsed into a single
    `**kwargs`-style tool) because pydantic-ai introspects the function
    signature to build the tool schema the LLM sees — this is the one place
    the "many tool definitions" shape is actually required by the framework,
    not duplicated business logic.
    """

    @agent.tool
    async def search_jobs(
        ctx: RunContext[PlatformDeps],
        query: str,
        location: str = "",
        remote: bool = False,
        limit: int = 5,
    ) -> str:
        """Search for jobs matching the query. Returns job titles, companies, and links."""
        tool_ctx = _ctx_from_deps(ctx.deps, query=query, location=location, remote=remote, limit=limit)
        return TOOL_REGISTRY.execute("search_jobs", tool_ctx).with_trailer()

    @agent.tool
    async def analyze_skill_gap(
        ctx: RunContext[PlatformDeps],
        job_id: str = "",
        target_role: str = "",
    ) -> str:
        """Analyze the user's skill gap against their target roles."""
        tool_ctx = _ctx_from_deps(ctx.deps, job_id=job_id, target_role=target_role)
        return TOOL_REGISTRY.execute("analyze_skill_gap", tool_ctx).with_trailer()

    @agent.tool
    async def get_career_profile(ctx: RunContext[PlatformDeps]) -> str:
        """Get the user's career profile summary including skills, experience, and talent score."""
        tool_ctx = _ctx_from_deps(ctx.deps)
        return TOOL_REGISTRY.execute("get_career_profile", tool_ctx).with_trailer()

    @agent.tool
    async def get_recommendations(ctx: RunContext[PlatformDeps], limit: int = 5) -> str:
        """Get personalized job recommendations for the user."""
        tool_ctx = _ctx_from_deps(ctx.deps, limit=limit)
        return TOOL_REGISTRY.execute("get_recommendations", tool_ctx).with_trailer()

    @agent.tool
    async def prepare_interview(
        ctx: RunContext[PlatformDeps],
        job_title: str,
        company: str = "",
        focus: str = "general",
    ) -> str:
        """Generate interview preparation material for a specific role."""
        tool_ctx = _ctx_from_deps(ctx.deps, job_title=job_title, company=company, focus=focus)
        return TOOL_REGISTRY.execute("prepare_interview", tool_ctx).with_trailer()

    @agent.tool
    async def get_salary_insights(
        ctx: RunContext[PlatformDeps],
        job_title: str,
        location: str = "",
    ) -> str:
        """Get salary insights for a specific role and location."""
        tool_ctx = _ctx_from_deps(ctx.deps, job_title=job_title, location=location)
        return TOOL_REGISTRY.execute("get_salary_insights", tool_ctx).with_trailer()

    @agent.tool
    async def get_match_score(
        ctx: RunContext[PlatformDeps],
        job_id: str,
    ) -> str:
        """Get a detailed match score breakdown between the user's profile and a specific job."""
        tool_ctx = _ctx_from_deps(ctx.deps, job_id=job_id)
        return TOOL_REGISTRY.execute("get_match_score", tool_ctx).with_trailer()

    @agent.tool
    async def tailor_resume(
        ctx: RunContext[PlatformDeps],
        job_id: str,
    ) -> str:
        """Tailor the user's resume for a specific job, returning before/after ATS scores and suggestions."""
        tool_ctx = _ctx_from_deps(ctx.deps, job_id=job_id)
        return TOOL_REGISTRY.execute("tailor_resume", tool_ctx).with_trailer()

    @agent.tool
    async def find_referral_contacts(
        ctx: RunContext[PlatformDeps],
        company_id: str,
    ) -> str:
        """Find insider connections at a company — E-Career users and public GitHub contributors."""
        tool_ctx = _ctx_from_deps(ctx.deps, company_id=company_id)
        return TOOL_REGISTRY.execute("find_referral_contacts", tool_ctx).with_trailer()

    @agent.tool
    async def cv_review(ctx: RunContext[PlatformDeps]) -> str:
        """Review the user's CV and provide improvement suggestions."""
        tool_ctx = _ctx_from_deps(ctx.deps)
        return TOOL_REGISTRY.execute("cv_review", tool_ctx).with_trailer()

    @agent.tool
    async def cover_letter(
        ctx: RunContext[PlatformDeps],
        job_id: str = "",
        job_title: str = "",
        company_name: str = "",
    ) -> str:
        """Generate a cover letter tailored to a specific job."""
        tool_ctx = _ctx_from_deps(ctx.deps, job_id=job_id, job_title=job_title, company_name=company_name)
        return TOOL_REGISTRY.execute("cover_letter", tool_ctx).with_trailer()

    @agent.tool
    async def linkedin_optimizer(ctx: RunContext[PlatformDeps]) -> str:
        """Give tips to improve the user's LinkedIn profile."""
        tool_ctx = _ctx_from_deps(ctx.deps)
        return TOOL_REGISTRY.execute("linkedin_optimizer", tool_ctx).with_trailer()

    @agent.tool
    async def course_advisor(
        ctx: RunContext[PlatformDeps],
        target_role: str = "",
    ) -> str:
        """Recommend courses to close the user's skill gaps."""
        tool_ctx = _ctx_from_deps(ctx.deps, target_role=target_role)
        return TOOL_REGISTRY.execute("course_advisor", tool_ctx).with_trailer()


_rashid_agent: Agent[PlatformDeps, str] | None = None


def get_rashid_agent() -> Agent[PlatformDeps, str]:
    """Get or create the singleton Rashid agent."""
    global _rashid_agent
    if _rashid_agent is None:
        _rashid_agent = create_rashid_agent()
    return _rashid_agent
