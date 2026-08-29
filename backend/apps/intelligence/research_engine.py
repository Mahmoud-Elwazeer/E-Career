"""
Research Engine Service.

Evidence-oriented research architecture that collects sources,
timestamps, confidence scores, and provenance. Supports multiple
research types: company, market, career, technology.

Uses the platform's AI service for synthesis when GPT Researcher
is not available, with web search via configured providers.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from django.utils import timezone

logger = structlog.get_logger()


class ResearchType(str, Enum):
    COMPANY = "company"
    MARKET = "market"
    CAREER = "career"
    TECHNOLOGY = "technology"
    INDUSTRY = "industry"
    COMPETITOR = "competitor"
    SKILL = "skill"


class EvidenceQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


@dataclass
class Evidence:
    """A single piece of evidence from research."""
    content: str
    source_url: str = ""
    source_name: str = ""
    collected_at: datetime = field(default_factory=timezone.now)
    quality: EvidenceQuality = EvidenceQuality.UNVERIFIED
    confidence: float = 0.5
    contradicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "collected_at": str(self.collected_at),
            "quality": self.quality.value,
            "confidence": self.confidence,
            "contradicts": self.contradicts,
        }


@dataclass
class ResearchResult:
    """Complete research output."""
    query: str
    research_type: ResearchType
    summary: str
    evidence: list[Evidence]
    key_findings: list[str]
    confidence_score: float
    completed_at: datetime = field(default_factory=timezone.now)
    methodology: str = ""
    contradictions: list[str] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len(self.evidence)

    @property
    def high_quality_count(self) -> int:
        return sum(1 for e in self.evidence if e.quality == EvidenceQuality.HIGH)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "research_type": self.research_type.value,
            "summary": self.summary,
            "evidence": [e.to_dict() for e in self.evidence],
            "key_findings": self.key_findings,
            "confidence_score": self.confidence_score,
            "source_count": self.source_count,
            "completed_at": str(self.completed_at),
            "methodology": self.methodology,
            "contradictions": self.contradictions,
        }


class ResearchEngine:
    """Platform research engine with evidence collection."""

    def research(
        self,
        query: str,
        research_type: ResearchType = ResearchType.MARKET,
        depth: str = "standard",
        max_sources: int = 10,
    ) -> ResearchResult:
        """Conduct research on a topic.

        Args:
            query: The research question or topic
            research_type: Type of research to conduct
            depth: "quick" (1-2 sources), "standard" (5-10), "deep" (10-20)
            max_sources: Maximum number of sources to collect
        """
        logger.info("research_started", query=query, type=research_type.value, depth=depth)

        if self._gpt_researcher_available():
            return self._research_with_gpt_researcher(query, research_type, depth, max_sources)

        return self._research_with_platform_ai(query, research_type, max_sources)

    def research_company(self, company_name: str) -> ResearchResult:
        """Research a specific company."""
        query = f"Company profile and recent news about {company_name}: industry, size, culture, tech stack, recent developments"
        return self.research(query, ResearchType.COMPANY)

    def research_skill_market(self, skill: str) -> ResearchResult:
        """Research market demand for a skill."""
        query = f"Current job market demand for {skill}: salary ranges, growth trend, top hiring companies, required complementary skills"
        return self.research(query, ResearchType.SKILL)

    def research_career_path(self, current_role: str, target_role: str) -> ResearchResult:
        """Research a career transition path."""
        query = f"Career transition from {current_role} to {target_role}: required skills, typical timeline, recommended steps, potential challenges"
        return self.research(query, ResearchType.CAREER)

    def _gpt_researcher_available(self) -> bool:
        """Check if GPT Researcher is installed."""
        try:
            import gpt_researcher
            return True
        except ImportError:
            return False

    def _research_with_gpt_researcher(
        self, query: str, research_type: ResearchType, depth: str, max_sources: int
    ) -> ResearchResult:
        """Use GPT Researcher for web-based research."""
        try:
            from gpt_researcher import GPTResearcher
            import asyncio

            researcher = GPTResearcher(query=query, report_type="research_report")

            loop = asyncio.new_event_loop()
            try:
                report = loop.run_until_complete(researcher.conduct_research())
                research_report = loop.run_until_complete(researcher.write_report())
            finally:
                loop.close()

            sources = getattr(researcher, 'research_sources', []) or []
            evidence = [
                Evidence(
                    content=s.get("content", "")[:500] if isinstance(s, dict) else str(s)[:500],
                    source_url=s.get("url", "") if isinstance(s, dict) else "",
                    source_name=s.get("title", "") if isinstance(s, dict) else "",
                    quality=EvidenceQuality.MEDIUM,
                    confidence=0.7,
                )
                for s in sources[:max_sources]
            ]

            return ResearchResult(
                query=query,
                research_type=research_type,
                summary=research_report if isinstance(research_report, str) else str(research_report),
                evidence=evidence,
                key_findings=self._extract_key_findings(research_report),
                confidence_score=self._compute_confidence(evidence, "gpt_researcher_web_search"),
                methodology="gpt_researcher_web_search",
            )

        except Exception as e:
            logger.error("gpt_researcher_failed", error=str(e))
            return self._research_with_platform_ai(query, research_type, max_sources)

    def _research_with_platform_ai(
        self, query: str, research_type: ResearchType, max_sources: int
    ) -> ResearchResult:
        """Fallback: use platform AI service with internal data."""
        from apps.intelligence import get_ai_service
        from apps.intelligence.llm_plugin import LLMRequest

        service = get_ai_service()

        platform_context = self._gather_platform_context(query, research_type)

        prompt = f"""Research the following topic using the context provided:

TOPIC: {query}
TYPE: {research_type.value}

PLATFORM DATA CONTEXT:
{platform_context}

Provide:
1. A comprehensive summary (3-5 paragraphs)
2. Key findings (bullet points)
3. Confidence assessment (what we know vs. what's uncertain)
4. Any contradictions in the data

Format your response as structured text with clear sections."""

        response = service.generate(LLMRequest(
            prompt=prompt,
            system_prompt="You are a research analyst. Provide evidence-based analysis. Clearly distinguish facts from inferences. Never fabricate sources.",
            model="sonnet",
            max_tokens=2000,
        ))

        evidence = [
            Evidence(
                content=platform_context[:500],
                source_name="Platform internal data",
                quality=EvidenceQuality.HIGH,
                confidence=0.9,
            )
        ] if platform_context else []

        return ResearchResult(
            query=query,
            research_type=research_type,
            summary=response.content,
            evidence=evidence,
            key_findings=self._extract_key_findings(response.content),
            confidence_score=self._compute_confidence(evidence, "platform_ai_internal_data"),
            methodology="platform_ai_internal_data",
        )

    def _semantic_job_search(self, query: str) -> str:
        """Use VectorService for semantic job search when available."""
        try:
            from apps.vectors.service import vector_service
            result = vector_service.semantic_search(
                collection="jobs", query_text=query, limit=10, score_threshold=0.5,
            )
            if result and result.results:
                lines = []
                for r in result.results:
                    meta = r.metadata or {}
                    lines.append(f"- {meta.get('title', 'Unknown')} at {meta.get('company', 'Unknown')} (score: {r.score:.2f})")
                return f"Semantically related jobs ({len(lines)}):\n" + "\n".join(lines)
        except Exception as e:
            logger.debug("vector_search_unavailable", error=str(e))
        return ""

    def _gather_platform_context(self, query: str, research_type: ResearchType) -> str:
        """Gather relevant platform data as context for research.

        Uses VectorService.semantic_search when available, falls back to ORM.
        """
        context_parts = []

        try:
            if research_type in (ResearchType.SKILL, ResearchType.MARKET, ResearchType.CAREER):
                vector_context = self._semantic_job_search(query)
                if vector_context:
                    context_parts.append(vector_context)
                else:
                    from apps.jobs.models import Job
                    first_word = query.split()[0] if query else ""
                    relevant_jobs = Job.objects.filter(
                        status='active',
                        description__icontains=first_word,
                    ).values("title", "company__name", "location")[:10]
                    if relevant_jobs:
                        context_parts.append(
                            f"Related active jobs ({relevant_jobs.count()}):\n" +
                            "\n".join(f"- {j['title']} at {j['company__name']}" for j in relevant_jobs[:10])
                        )

            if research_type == ResearchType.COMPANY:
                from apps.jobs.models import Company
                companies = Company.objects.filter(name__icontains=query.split()[0])[:3]
                for company in companies:
                    context_parts.append(
                        f"Company: {company.name}\n"
                        f"Industry: {company.industry or 'Unknown'}\n"
                        f"Description: {(company.description or '')[:300]}"
                    )

        except Exception as e:
            logger.warning("context_gathering_failed", error=str(e))

        return "\n\n".join(context_parts)

    @staticmethod
    def _compute_confidence(evidence: list[Evidence], methodology: str) -> float:
        """Compute confidence based on evidence quality and quantity."""
        if not evidence:
            return 0.15
        quality_weights = {
            EvidenceQuality.HIGH: 1.0,
            EvidenceQuality.MEDIUM: 0.6,
            EvidenceQuality.LOW: 0.3,
            EvidenceQuality.UNVERIFIED: 0.1,
        }
        quality_avg = sum(quality_weights.get(e.quality, 0.1) for e in evidence) / len(evidence)
        source_factor = min(len(evidence) / 5, 1.0)
        methodology_bonus = {"gpt_researcher_web_search": 0.15}.get(methodology, 0.0)
        score = quality_avg * 0.5 + source_factor * 0.35 + methodology_bonus
        return round(max(0.1, min(0.95, score)), 2)

    def _extract_key_findings(self, text: str) -> list[str]:
        """Extract key findings from research text."""
        if not text:
            return []

        findings = []
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("- ", "* ", "• ")) and len(line) > 20:
                findings.append(line.lstrip("-*• ").strip())
            elif line.startswith(("1.", "2.", "3.", "4.", "5.")):
                findings.append(line[2:].strip())

        return findings[:10]


_engine: ResearchEngine | None = None


def get_research_engine() -> ResearchEngine:
    global _engine
    if _engine is None:
        _engine = ResearchEngine()
    return _engine
