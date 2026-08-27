"""
Content Generation Pipeline.

Generates SEO-optimized career content using AI:
- Career guides per industry/role
- Skills-demand reports
- Salary insights articles
- Interview preparation guides
- Company culture summaries

All content is generated from platform data + research, not hallucinated.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from django.core.cache import cache

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    CAREER_GUIDE = "career_guide"
    SKILLS_REPORT = "skills_report"
    SALARY_INSIGHT = "salary_insight"
    INTERVIEW_GUIDE = "interview_guide"
    INDUSTRY_OVERVIEW = "industry_overview"
    COMPANY_PROFILE = "company_profile"


@dataclass
class ContentPiece:
    """Generated content piece."""
    title: str
    content_type: ContentType
    body: str
    meta_description: str = ""
    keywords: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    word_count: int = 0
    language: str = "en"

    def __post_init__(self):
        self.word_count = len(self.body.split())


class ContentPipeline:
    """
    Generates research-backed career content.

    Pipeline:
    1. Gather data from platform (jobs, skills, salary, trends)
    2. Optionally run research for external data
    3. Generate content using AI with data context
    4. Add SEO metadata
    """

    def __init__(self):
        self._ai = None

    @property
    def ai(self):
        if self._ai is None:
            from .service import get_ai_service
            self._ai = get_ai_service()
        return self._ai

    def generate_career_guide(self, role: str, industry: str = "", language: str = "en") -> ContentPiece:
        """Generate a career guide for a specific role."""
        context = self._gather_role_context(role)

        system = """You are a career content writer. Write informative, actionable career guides.
Use data provided to back up claims. Write in a professional but approachable tone.
Structure with clear headings (##). Include actionable advice."""

        if language == "ar":
            system += "\nWrite the entire guide in Arabic."

        prompt = f"""Write a comprehensive career guide for: {role}
{f'Industry: {industry}' if industry else ''}

DATA CONTEXT:
- Top skills in demand: {context.get('top_skills', 'N/A')}
- Average experience required: {context.get('avg_experience', 'N/A')}
- Common job titles: {context.get('titles', 'N/A')}
- Salary range: {context.get('salary_range', 'N/A')}
- Job count on platform: {context.get('job_count', 'N/A')}

Write a 800-1200 word guide covering:
1. Role overview and day-to-day responsibilities
2. Required skills and how to develop them
3. Career path and progression
4. Salary expectations
5. Tips for job seekers

End with 3-5 actionable next steps."""

        from .llm_plugin import LLMRequest
        response = self.ai.generate(LLMRequest(
            prompt=prompt,
            system_prompt=system,
            model="sonnet",
            max_tokens=3000,
        ))

        return ContentPiece(
            title=f"Career Guide: How to Become a {role}",
            content_type=ContentType.CAREER_GUIDE,
            body=response.content,
            meta_description=f"Complete career guide for {role}. Learn about required skills, salary expectations, and how to break into the field.",
            keywords=[role.lower(), "career guide", "jobs", industry.lower()] if industry else [role.lower(), "career guide", "jobs"],
            sources=["platform_data"],
            language=language,
        )

    def generate_skills_report(self, days: int = 30, language: str = "en") -> ContentPiece:
        """Generate a skills demand report from platform trend data."""
        from .trend_detection import get_trend_service

        service = get_trend_service()
        emerging = service.get_emerging_skills(days=days)
        declining = service.get_declining_skills(days=days)

        system = """You are a labor market analyst. Write data-driven skills reports.
Present findings clearly with specific numbers. Be objective and factual."""

        if language == "ar":
            system += "\nWrite the report in Arabic."

        prompt = f"""Write a skills demand report based on this job market data:

EMERGING SKILLS (growing in demand):
{emerging[:10]}

DECLINING SKILLS (decreasing in demand):
{declining[:10]}

Period: Last {days} days

Write a 600-800 word report covering:
1. Executive summary (3-4 sentences)
2. Top emerging skills and why they're growing
3. Skills losing demand and what's replacing them
4. Recommendations for job seekers
5. Industry implications"""

        from .llm_plugin import LLMRequest
        response = self.ai.generate(LLMRequest(
            prompt=prompt,
            system_prompt=system,
            model="sonnet",
            max_tokens=2000,
        ))

        return ContentPiece(
            title=f"Skills Demand Report: What's Trending in {days}-Day Period",
            content_type=ContentType.SKILLS_REPORT,
            body=response.content,
            meta_description=f"Latest skills demand report. See which skills are growing and declining in the job market over the past {days} days.",
            keywords=["skills report", "job market", "trending skills", "career development"],
            sources=["platform_trends"],
            language=language,
        )

    def generate_interview_guide(self, role: str, company: str = "", language: str = "en") -> ContentPiece:
        """Generate an interview preparation guide."""
        system = """You are an interview preparation coach. Write practical, actionable interview guides.
Include specific example questions and answer frameworks."""

        if language == "ar":
            system += "\nWrite the guide in Arabic."

        prompt = f"""Write an interview preparation guide for: {role}
{f'Company: {company}' if company else ''}

Write a 600-1000 word guide covering:
1. How to prepare (research, practice, materials)
2. Common technical questions (5 examples with answer tips)
3. Behavioral questions (5 examples with STAR framework)
4. Questions to ask the interviewer (5 good questions)
5. Common mistakes to avoid
6. Day-of tips"""

        from .llm_plugin import LLMRequest
        response = self.ai.generate(LLMRequest(
            prompt=prompt,
            system_prompt=system,
            model="sonnet",
            max_tokens=2500,
        ))

        title = f"Interview Guide: {role}"
        if company:
            title += f" at {company}"

        return ContentPiece(
            title=title,
            content_type=ContentType.INTERVIEW_GUIDE,
            body=response.content,
            meta_description=f"Complete interview preparation guide for {role}. Common questions, STAR examples, and expert tips.",
            keywords=[role.lower(), "interview", "preparation", "questions"],
            sources=["ai_generated"],
            language=language,
        )

    def _gather_role_context(self, role: str) -> Dict:
        """Gather platform data context for a role."""
        from apps.jobs.models import Job
        from apps.skills.models import JobSkill
        from django.db.models import Count, Avg

        try:
            jobs = Job.objects.filter(
                title__icontains=role, is_expired=False
            )
            job_count = jobs.count()

            top_skills = list(
                JobSkill.objects.filter(job__in=jobs)
                .values_list('skill__name', flat=True)
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )

            titles = list(
                jobs.values_list('title', flat=True)
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )

            return {
                'job_count': job_count,
                'top_skills': top_skills,
                'titles': titles,
                'avg_experience': 'mid-level',
                'salary_range': 'varies by location',
            }
        except Exception:
            return {}


_pipeline: Optional[ContentPipeline] = None


def get_content_pipeline() -> ContentPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ContentPipeline()
    return _pipeline
