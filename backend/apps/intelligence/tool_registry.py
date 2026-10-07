"""
Canonical Rashid tool registry.

Fixes the documented duplicate-tool-registry finding (see
audit/PLATFORM_ENGINE_ENRICHMENT_MASTER.md, Open Glean section): this
platform previously had TWO independent definitions of the same
capabilities —

  (A) `apps/intelligence/agent.py::_register_rashid_tools` — the LIVE path,
      wired into real chat via pydantic-ai `@agent.tool` decorators.
  (B) `apps/rashid/tools.py::RASHID_TOOLS` — a separate `RashidTool` class
      registry, reachable only via `POST /api/rashid/tools/execute/`, never
      called from (A), with its OWN (different, in places buggy —
      `search_jobs` filtered on `status="active"` instead of the
      authoritative `quality_state`; `recommend_jobs` called
      `get_recommendation_engine` instead of `RecommendationEngine`
      directly, a working but inconsistent entrypoint) implementation of
      `search_jobs`/`recommend_jobs`.

This module is now the ONE place where a tool's name, schema, permission
rule, and underlying service call are defined. Both the pydantic-ai agent
(`agent.py`) and the REST tool-execute endpoint (`rashid/views.py`) call
into `TOOL_REGISTRY` here rather than each defining their own version.

Design:
  - `ToolDefinition` captures name/description/the callable/whether auth is
    required/whether the tool performs a consequential (non-idempotent)
    action.
  - Each tool function takes a plain `ToolContext` (not a pydantic-ai
    `RunContext`, not a raw Django request) so it has exactly ONE calling
    convention regardless of which transport invokes it.
  - Tool functions return a `ToolResult` (see `apps.intelligence.evidence`)
    so factual tools can carry structured evidence instead of inventing a
    one-off text format each time.
  - Permission enforcement is centralized in `TOOL_REGISTRY.execute()`,
    not re-implemented per tool: an `requires_auth=True` tool is rejected
    before the tool body ever runs if `ctx.user_id` is falsy.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from apps.intelligence.evidence import EvidenceSource, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ToolContext:
    """Everything a tool function needs, independent of transport.

    Built once per call from whichever caller invoked the tool (the
    pydantic-ai `RunContext.deps` for live chat, or `request.user` for the
    REST tools/execute endpoint) — the tool body itself never touches
    Django `request` or pydantic-ai `RunContext` directly.
    """

    user_id: Optional[int] = None
    user_email: str = ""
    user_name: str = ""
    language: str = "en"
    # Free-form extra args a specific tool needs (job_id, query, etc.) —
    # validated by the tool function itself, not by this dataclass.
    args: dict[str, Any] = field(default_factory=dict)

    def require_auth(self) -> Optional[str]:
        """Returns an error string if unauthenticated, else None."""
        if not self.user_id:
            return "User not authenticated."
        return None


ToolFunc = Callable[[ToolContext], ToolResult]


@dataclass
class ToolDefinition:
    name: str
    description: str
    func: ToolFunc
    requires_auth: bool = True
    # Consequential tools (e.g. a future "submit application" tool) should
    # set this True so callers can require explicit confirmation before
    # calling execute() — none of the current tools mutate data, but this
    # flag exists so the registry can express that distinction when one
    # does, rather than bolting it on as a special case later.
    is_consequential: bool = False


class ToolRegistry:
    """Holds every canonical tool definition and enforces auth centrally."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._tools:
            raise ValueError(f"Duplicate tool name registered: {definition.name!r}")
        self._tools[definition.name] = definition

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def all(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def execute(self, name: str, ctx: ToolContext) -> ToolResult:
        """Run a tool by name with centralized auth enforcement.

        Every caller (pydantic-ai tool wrapper, REST endpoint) should go
        through this method rather than calling `tool.func` directly, so
        the `requires_auth` check can never be silently skipped by a new
        call site.
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult(text=f"Tool '{name}' not found.")

        if tool.requires_auth:
            auth_error = ctx.require_auth()
            if auth_error:
                return ToolResult(text=auth_error)

        try:
            return tool.func(ctx)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("tool_execution_failed", tool=name, error=str(exc))
            return ToolResult(text=f"Could not complete '{name}' right now. Please try again shortly.")


TOOL_REGISTRY = ToolRegistry()


def tool(name: str, description: str, requires_auth: bool = True, is_consequential: bool = False):
    """Decorator to register a plain `ToolContext -> ToolResult` function."""

    def decorator(func: ToolFunc) -> ToolFunc:
        TOOL_REGISTRY.register(
            ToolDefinition(
                name=name,
                description=description,
                func=func,
                requires_auth=requires_auth,
                is_consequential=is_consequential,
            )
        )
        return func

    return decorator


# ─────────────────────────────────────────────────────────────────────────
# Canonical tool implementations
#
# Each one calls the SAME real service classes the old agent.py tools
# called (SearchService, SkillGapAnalyzer, RecommendationEngine,
# MatchingService, CVTailorService, ConnectionsService) — no business logic
# lives here, this module is purely registration + request/response
# shaping, matching the directive's required shape:
#   Rashid Agent -> canonical Tool Registry -> authorized service
#   -> domain engine -> evidence/result -> AI response.
# ─────────────────────────────────────────────────────────────────────────


@tool("search_jobs", "Search for jobs matching a query. Returns job titles, companies, and links.", requires_auth=False)
def _search_jobs(ctx: ToolContext) -> ToolResult:
    from apps.search.service import SearchService
    from apps.search.plugins.base import SearchQuery

    query = ctx.args.get("query", "")
    location = ctx.args.get("location", "")
    remote = ctx.args.get("remote", False)
    limit = ctx.args.get("limit", 5)

    filters: dict[str, Any] = {}
    if location:
        filters["location"] = location
    if remote:
        filters["work_arrangement"] = "remote"

    service = SearchService()
    try:
        response = service.search_jobs(SearchQuery(q=query, filters=filters, page=1, per_page=limit))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("tool_search_jobs_failed", error=str(exc))
        return ToolResult(text="Job search is temporarily unavailable. Please try again shortly.")

    hits = getattr(response, "hits", []) or []
    if not hits:
        return ToolResult(text="No jobs found matching your criteria.")

    lines = []
    sources = []
    for hit in hits[:limit]:
        data = getattr(hit, "data", {}) or {}
        job_id = data.get("id") or hit.id
        lines.append(
            f"- **{data.get('title', 'Untitled')}** at "
            f"{data.get('company_name', 'Unknown')} "
            f"({data.get('location', 'N/A')}) - ID: {job_id}"
        )
        sources.append(EvidenceSource(source_type="job", source_id=str(job_id), label=data.get("title", "Job")))
    return ToolResult(text="\n".join(lines), sources=sources)


@tool("analyze_skill_gap", "Analyze the user's skill gap against their target roles.")
def _analyze_skill_gap(ctx: ToolContext) -> ToolResult:
    from django.contrib.auth import get_user_model
    from apps.career.skill_gap_analysis import SkillGapAnalyzer

    User = get_user_model()
    try:
        user = User.objects.get(id=ctx.user_id)
    except User.DoesNotExist:
        return ToolResult(text="User not found.")

    try:
        result = SkillGapAnalyzer(user).analyze()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("tool_skill_gap_failed", error=str(exc))
        return ToolResult(text="Could not perform skill gap analysis. Please add target roles and skills to your career profile first.")

    missing = result.get("missing_skills", []) or []
    if not missing and not result.get("gaps_by_role"):
        return ToolResult(text="No skill gaps found, or your profile has no target roles yet. Add target roles to your career profile for a detailed analysis.")

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
    return ToolResult(text="\n".join(lines))


@tool("get_career_profile", "Get the user's career profile summary including skills, experience, and talent score.")
def _get_career_profile(ctx: ToolContext) -> ToolResult:
    from apps.career.models import CareerProfile, TalentScore

    try:
        profile = CareerProfile.objects.get(user_id=ctx.user_id)
    except CareerProfile.DoesNotExist:
        return ToolResult(text="No career profile found. Please complete your profile first.")

    sources = [EvidenceSource(source_type="career_identity", source_id=str(profile.pk), label="CareerProfile", owner_user_id=ctx.user_id)]
    lines = [f"**Career Profile for {ctx.user_name}:**"]

    if profile.cv_parsed_data:
        data = profile.cv_parsed_data
        if data.get("skills"):
            lines.append(f"- Skills: {', '.join(data['skills'][:10])}")
        if data.get("experience"):
            lines.append(f"- Experience entries: {len(data['experience'])}")
        if data.get("education"):
            lines.append(f"- Education entries: {len(data['education'])}")

    try:
        score = TalentScore.objects.filter(user_id=ctx.user_id).latest("last_calculated_at")
        lines.append(f"- Talent Score: {round(score.overall_score * 100)}/100")
        sources.append(EvidenceSource(source_type="talent_score", source_id=str(score.pk), label="TalentScore", confidence=score.ai_confidence, owner_user_id=ctx.user_id))
    except TalentScore.DoesNotExist:
        lines.append("- Talent Score: Not yet calculated")

    return ToolResult(text="\n".join(lines), sources=sources)


@tool("get_recommendations", "Get personalized job recommendations for the user.")
def _get_recommendations(ctx: ToolContext) -> ToolResult:
    from django.contrib.auth import get_user_model
    from apps.search.recommendation_engine import RecommendationEngine

    limit = ctx.args.get("limit", 5)
    User = get_user_model()
    try:
        user = User.objects.get(id=ctx.user_id)
    except User.DoesNotExist:
        return ToolResult(text="User not found.")

    try:
        engine = RecommendationEngine(user)
        jobs = engine.get_recommendations(n_recommendations=limit)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("tool_recommendations_failed", error=str(exc))
        return ToolResult(text="Recommendations are temporarily unavailable. Please try again shortly.")

    if not jobs:
        return ToolResult(text="No recommendations available yet. Complete your profile and add skills to get personalized recommendations.")

    lines = ["**Recommended Jobs:**"]
    sources = []
    for j in jobs[:limit]:
        lines.append(f"- **{j.get('job_title')}** at {j.get('company_name')} (match: {j.get('score', 0):.0%})")
        if j.get("job_id"):
            sources.append(EvidenceSource(source_type="job", source_id=str(j["job_id"]), label=j.get("job_title", "Job"), confidence=j.get("score")))
    return ToolResult(text="\n".join(lines), sources=sources)


@tool("prepare_interview", "Generate interview preparation material for a specific role.")
def _prepare_interview(ctx: ToolContext) -> ToolResult:
    from apps.intelligence import get_ai_service
    from apps.intelligence.llm_plugin import LLMRequest

    job_title = ctx.args.get("job_title", "")
    company = ctx.args.get("company", "")
    focus = ctx.args.get("focus", "general")

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
        user_id=ctx.user_id,
        operation="interview_prep",
    ))
    return ToolResult(text=response.content)


@tool("get_salary_insights", "Get salary insights for a specific role and location.", requires_auth=False)
def _get_salary_insights(ctx: ToolContext) -> ToolResult:
    from apps.salary.models import SalaryData

    job_title = ctx.args.get("job_title", "")
    location = ctx.args.get("location", "")

    qs = SalaryData.objects.filter(job__title__icontains=job_title)
    if location:
        qs = qs.filter(job__location__icontains=location)
    data = list(qs.select_related("job")[:50])
    if not data:
        return ToolResult(text=f"No salary data available for {job_title}{f' in {location}' if location else ''}.")

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
        return ToolResult(text="Salary data exists but amounts are not available.")

    all_vals = lows + highs
    avg = sum(all_vals) / len(all_vals)
    min_sal = min(lows) if lows else min(all_vals)
    max_sal = max(highs) if highs else max(all_vals)

    sources = [EvidenceSource(source_type="salary_dataset", source_id=str(d.pk), label="SalaryData") for d in data[:5]]
    if len(data) > 5:
        sources.append(EvidenceSource(source_type="salary_dataset", source_id="", label=f"+{len(data) - 5} more"))

    text = (
        f"**Salary Insights for {job_title}:**\n"
        f"- Average: {currency} {avg:,.0f}\n"
        f"- Range: {currency} {min_sal:,.0f} - {currency} {max_sal:,.0f}\n"
        f"- Based on {len(data)} data points"
    )
    return ToolResult(text=text, sources=sources)


@tool("get_match_score", "Get a detailed match score breakdown between the user's profile and a specific job.")
def _get_match_score(ctx: ToolContext) -> ToolResult:
    from apps.career.models import CareerProfile
    from apps.jobs.models import Job
    from apps.profiles.services import MatchingService

    job_id = ctx.args.get("job_id", "")

    try:
        profile = CareerProfile.objects.get(user_id=ctx.user_id)
    except CareerProfile.DoesNotExist:
        return ToolResult(text="No career profile found. Please complete your profile first.")

    try:
        job = Job.objects.get(uuid=job_id)
    except (Job.DoesNotExist, ValueError):
        return ToolResult(text=f"Job with ID {job_id} not found.")

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

    sources = [
        EvidenceSource(source_type="career_identity", source_id=str(profile.pk), label="CareerProfile", owner_user_id=ctx.user_id),
        EvidenceSource(source_type="job", source_id=str(job.uuid), label=job.title),
    ]
    return ToolResult(text="\n".join(lines), sources=sources)


@tool("tailor_resume", "Tailor the user's resume for a specific job, returning before/after ATS scores and suggestions.")
def _tailor_resume(ctx: ToolContext) -> ToolResult:
    from django.contrib.auth import get_user_model
    from apps.jobs.models import Job
    from apps.career.cv_tailor_service import CVTailorService

    job_id = ctx.args.get("job_id", "")
    User = get_user_model()
    try:
        user = User.objects.get(id=ctx.user_id)
    except User.DoesNotExist:
        return ToolResult(text="User not found.")

    try:
        job = Job.objects.get(uuid=job_id)
    except (Job.DoesNotExist, ValueError):
        return ToolResult(text=f"Job with ID {job_id} not found.")

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

    sources = [EvidenceSource(source_type="job", source_id=str(job.uuid), label=job.title)]
    return ToolResult(text="\n".join(lines), sources=sources)


@tool("find_referral_contacts", "Find insider connections at a company — E-Career users and public GitHub contributors.")
def _find_referral_contacts(ctx: ToolContext) -> ToolResult:
    from django.contrib.auth import get_user_model
    from apps.employers.connections_service import ConnectionsService

    company_id = ctx.args.get("company_id", "")
    User = get_user_model()
    try:
        user = User.objects.get(id=ctx.user_id)
    except User.DoesNotExist:
        return ToolResult(text="User not found.")

    service = ConnectionsService()
    try:
        result = service.find_connections(int(company_id), requesting_user=user)
    except Exception as e:
        return ToolResult(text=f"Could not find connections: {e}")

    company_name = result["company"]["name"]
    ecareer = result.get("ecareer_connections", [])
    github = result.get("github_contributors", [])

    if not ecareer and not github:
        return ToolResult(text=f"No insider connections found at {company_name}.")

    lines = [f"**Connections at {company_name}:** ({result['total_connections']} found)"]
    for c in ecareer[:5]:
        role = f" — {c['current_role']}" if c.get("current_role") else ""
        lines.append(f"- {c['name']}{role} ({c['connection_type'].replace('_', ' ')})")
    for g in github[:5]:
        lines.append(f"- GitHub: @{g['username']} ({g['profile_url']})")

    sources = [EvidenceSource(source_type="company", source_id=str(result["company"]["id"]), label=company_name)]
    return ToolResult(text="\n".join(lines), sources=sources)


# ─────────────────────────────────────────────────────────────────────────
# Tools migrated from the now-retired apps/rashid/tools.py RASHID_TOOLS
# registry. Ported onto the real CareerProfile model (apps.career.models)
# instead of the previous `apps.profiles.models.UserProfile` import, which
# resolves to CareerProfile via a backwards-compat alias but exposes
# different field names than the old tools assumed — the old
# InterviewPrepTool/LinkedInOptimizerTool referenced `profile.experience`,
# `profile.current_position`, and `profile.years_of_experience`, none of
# which exist on CareerProfile (the real fields are `cv_parsed_data`,
# `current_role`, and `experience_years`) and would have raised
# AttributeError on first real use. Fixed here, not reproduced.
# ─────────────────────────────────────────────────────────────────────────


def _get_career_profile_or_none(user_id: Optional[int]):
    from apps.career.models import CareerProfile

    try:
        return CareerProfile.objects.get(user_id=user_id)
    except CareerProfile.DoesNotExist:
        return None


def _read_cv_text(profile) -> str:
    """CV text source of truth is `cv_parsed_data` (structured extraction),
    with a best-effort raw-file read fallback for older profiles whose CV
    hasn't been parsed yet."""
    if profile.cv_parsed_data and profile.cv_parsed_data.get("text"):
        return profile.cv_parsed_data["text"][:5000]
    if profile.cv_file:
        try:
            with profile.cv_file.open("rb") as f:
                return f.read().decode("utf-8", errors="ignore")[:5000]
        except Exception:
            return ""
    return ""


@tool("cv_review", "Review the user's CV and provide improvement suggestions.")
def _cv_review(ctx: ToolContext) -> ToolResult:
    from apps.intelligence.career_ai import career_ai_service as bedrock_service

    profile = _get_career_profile_or_none(ctx.user_id)
    if profile is None:
        return ToolResult(text="No career profile found. Please complete your profile first.")

    cv_text = _read_cv_text(profile)
    if not cv_text:
        return ToolResult(text="No CV found. Please upload your CV first.")

    system_prompt = (
        "You are an expert CV reviewer. Provide: 1) an overall score out of 10, "
        "2) 3-5 strengths, 3) 3-5 areas to improve, 4) specific actionable "
        "suggestions, 5) examples of stronger phrasing. Be honest but encouraging."
    )
    prompt = f"Review this CV:\n\n{cv_text}\n\nProvide a thorough analysis and practical suggestions."

    try:
        response = bedrock_service.invoke_model(prompt=prompt, system_prompt=system_prompt, max_tokens=2000, temperature=0.5)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("tool_cv_review_failed", error=str(exc))
        return ToolResult(text="Could not review the CV right now. Please try again shortly.")

    sources = [EvidenceSource(source_type="cv", source_id=str(profile.pk), label="CV", owner_user_id=ctx.user_id)]
    return ToolResult(text=response, sources=sources)


@tool("cover_letter", "Generate a cover letter tailored to a specific job.")
def _cover_letter(ctx: ToolContext) -> ToolResult:
    from apps.intelligence.career_ai import career_ai_service as bedrock_service
    from apps.jobs.models import Job

    profile = _get_career_profile_or_none(ctx.user_id)
    if profile is None:
        return ToolResult(text="No career profile found. Please complete your profile first.")

    cv_text = _read_cv_text(profile)
    if not cv_text:
        return ToolResult(text="No CV found. Please upload your CV first.")

    job_id = ctx.args.get("job_id", "")
    job_title = ctx.args.get("job_title", "the role")
    company_name = ctx.args.get("company_name", "the company")
    job_description = ""
    sources = [EvidenceSource(source_type="cv", source_id=str(profile.pk), label="CV", owner_user_id=ctx.user_id)]

    if job_id:
        try:
            job = Job.objects.get(uuid=job_id)
            job_title = job.title
            company_name = job.company.name if job.company_id else company_name
            job_description = f"\nJob: {job.title} at {company_name}\nDescription: {(job.description or '')[:500]}"
            sources.append(EvidenceSource(source_type="job", source_id=str(job.uuid), label=job.title))
        except (Job.DoesNotExist, ValueError):
            pass

    system_prompt = (
        "You are an expert at writing cover letters. Write one that is "
        "professional yet personal, highlights relevant skills, shows genuine "
        "interest in the company, and stays concise (250-350 words)."
    )
    prompt = f"Write a cover letter for:\nRole: {job_title}\nCompany: {company_name}{job_description}\n\nApplicant background:\n{cv_text[:1500]}"

    try:
        response = bedrock_service.invoke_model(prompt=prompt, system_prompt=system_prompt, max_tokens=1500, temperature=0.7)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("tool_cover_letter_failed", error=str(exc))
        return ToolResult(text="Could not write the cover letter right now. Please try again shortly.")

    return ToolResult(text=response, sources=sources)


@tool("linkedin_optimizer", "Give tips to improve the user's LinkedIn profile.")
def _linkedin_optimizer(ctx: ToolContext) -> ToolResult:
    from apps.intelligence.career_ai import career_ai_service as bedrock_service

    profile = _get_career_profile_or_none(ctx.user_id)
    current_position = profile.current_role if profile and profile.current_role else "job seeker"
    skills = ", ".join(profile.skills[:10]) if profile and profile.skills else "not specified"
    years = profile.experience_years if profile else 0

    system_prompt = (
        "You are a LinkedIn profile optimization expert. Give specific advice for: "
        "1) headline, 2) About section, 3) how to phrase experience achievements, "
        "4) which skills to add, 5) profile photo/banner, 6) networking tips."
    )
    prompt = (
        f"Help optimize a LinkedIn profile:\nCurrent/target role: {current_position}\n"
        f"Skills: {skills}\nYears of experience: {years}\n\n"
        "Provide a suggested headline, an About section draft, and concrete tips."
    )

    try:
        response = bedrock_service.invoke_model(prompt=prompt, system_prompt=system_prompt, max_tokens=2000, temperature=0.7)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("tool_linkedin_optimizer_failed", error=str(exc))
        return ToolResult(text="Could not generate LinkedIn suggestions right now. Please try again shortly.")

    sources = []
    if profile:
        sources.append(EvidenceSource(source_type="career_identity", source_id=str(profile.pk), label="CareerProfile", owner_user_id=ctx.user_id))
    return ToolResult(text=response, sources=sources)


_FALLBACK_COURSE_CATALOG = """\
- Python Fundamentals: programming from scratch
- Django Web Development: building production-ready applications
- Data Analysis with Excel: fundamentals to advanced
- Digital Marketing: effective strategies for business
- Professional Project Management: PMP preparation
- UI/UX Design: from concept to execution
- Machine Learning Introduction: a practical primer
- Cybersecurity Fundamentals: protecting data and systems
- Mobile App Development: React Native and Flutter
- Digital Product Management
- Big Data Analysis: tools and techniques
- AWS Cloud Computing: Solutions Architect certification
- Business English: professional communication skills
- Leadership and Management Skills"""


def _fetch_course_catalog() -> str:
    """Fetch courses from edu.usamif.com, falling back to a curated static
    catalog when the integration endpoint isn't reachable."""
    try:
        import requests as http_requests

        resp = http_requests.get(
            "https://edu.usamif.com/api/v1/courses/",
            timeout=8,
            headers={"Accept": "application/json"},
        )
        if resp.status_code == 200:
            data = resp.json()
            courses = data if isinstance(data, list) else data.get("results", data.get("courses", []))
            if courses:
                lines = []
                for c in courses[:20]:
                    name = c.get("title") or c.get("name", "")
                    desc = (c.get("description", "") or "")[:80]
                    lines.append(f"- {name}: {desc}")
                return "\n".join(lines)
    except Exception:
        pass
    return _FALLBACK_COURSE_CATALOG


@tool("course_advisor", "Recommend courses to close the user's skill gaps.")
def _course_advisor(ctx: ToolContext) -> ToolResult:
    from apps.intelligence.career_ai import career_ai_service as bedrock_service

    profile = _get_career_profile_or_none(ctx.user_id)
    skill_gap = ctx.args.get("skill_gap", [])
    target_role = ctx.args.get("target_role", "")

    current_skills = ", ".join(profile.skills) if profile and profile.skills else "none listed"
    target_skills = ", ".join(skill_gap) if skill_gap else "not specified"
    current_role = (profile.current_role if profile else "") or ""

    courses = _fetch_course_catalog()

    system_prompt = (
        "You are a training advisor. IMPORTANT: only recommend courses from the "
        "provided list — never invent course names. Give 3-5 best-fit courses, "
        "the reason for each, a priority order, and a suggested learning path."
    )
    prompt = (
        f"Help choose training courses:\nCurrent skills: {current_skills}\n"
        f"Target skills: {target_skills}\nTarget role: {target_role or current_role or 'not specified'}\n\n"
        f"Available courses:\n{courses}\n\nRecommend the best courses from this list to reach the goal."
    )

    try:
        response = bedrock_service.invoke_model(prompt=prompt, system_prompt=system_prompt, max_tokens=1500, temperature=0.5)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("tool_course_advisor_failed", error=str(exc))
        return ToolResult(text="Could not generate course recommendations right now. Please try again shortly.")

    return ToolResult(text=response)
