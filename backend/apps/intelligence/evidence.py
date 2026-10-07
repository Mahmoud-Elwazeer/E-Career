"""
Canonical evidence/citation model for Rashid (and future AI features).

Evaluated against hydra-db/open-glean's Deep Research citation pattern
(Apache-2.0, REFERENCE_ONLY — see audit/PLATFORM_ENGINE_ENRICHMENT_MASTER.md)
and against this engagement's earlier ad hoc `_Source: Model#id_` text
trailers (apps/intelligence/agent.py). Both approaches had the same gap:
no shared, structured shape — any new tool that wanted to cite its data
would invent its own format.

This module is the ONE place that defines what "evidence" means on this
platform. A tool that returns factual information should build a
`ToolResult` with one `EvidenceSource` per record it actually read.
Confidence is only ever set when the underlying computation produces a
real score — never invented to make output "look" more rigorous.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

# Keep in sync with the domains actually readable by Rashid tools. Add a new
# literal here (not a free-form string elsewhere) when a tool starts citing
# a new kind of record, so the whole set stays discoverable in one place.
SourceType = Literal[
    "candidate_profile",
    "career_identity",
    "cv",
    "skills",
    "assessment",
    "talent_score",
    "job",
    "job_requirement",
    "company",
    "application",
    "interview",
    "salary_dataset",
    "knowledge_document",
    "external_research",
]


@dataclass(frozen=True)
class EvidenceSource:
    """One concrete record a tool's answer is grounded in.

    Only `source_type` + `source_id` are required — everything else is
    filled in when it's meaningfully available, never guessed.
    """

    source_type: SourceType
    source_id: str
    label: str = ""
    field: str = ""
    timestamp: Optional[datetime] = None
    confidence: Optional[float] = None
    url: Optional[str] = None
    # Visibility/permission metadata: which user this record is scoped to,
    # so a caller can double-check a citation was never built from another
    # user's data before it reaches a response. Empty means "not user-scoped"
    # (e.g. a public Job record).
    owner_user_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "type": self.source_type,
            "id": self.source_id,
            "label": self.label,
            "field": self.field,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "confidence": self.confidence,
            "url": self.url,
        }

    def as_citation(self) -> str:
        """Human-readable form, e.g. 'CareerProfile#12'. Used for the plain-text
        trailer appended to LLM-facing tool output (the chat UI renders text,
        not structured JSON, today).

        A blank `source_id` (used for a summary note like "+2 more" rather
        than a specific record) renders as just the label, with no bare '#'.
        """
        label = self.label or self.source_type
        if not self.source_id:
            return label
        return f"{label}#{self.source_id}"


def format_evidence_trailer(sources: list[str]) -> str:
    """Format a list of plain citation strings as a trailing citation line.

    Kept as a standalone function (not just a `ToolResult` method) for
    backwards compatibility with call sites that already have a list of
    citation strings rather than `EvidenceSource` objects.

    Returns "" when there's nothing concrete to cite, so tools with no data
    don't get a misleading empty trailer.
    """
    if not sources:
        return ""
    return "\n\n_Source: " + "; ".join(sources) + "_"


@dataclass
class ToolResult:
    """What a canonical tool function returns.

    `text` is what the LLM/chat UI sees (unchanged contract from before this
    refactor — pydantic-ai tool functions must keep returning plain text for
    the agent to reason over). `sources` is the structured citation list for
    callers that CAN render structured evidence (REST endpoints, a future
    "Based on your CV" UI) instead of just a text trailer.
    """

    text: str
    sources: list[EvidenceSource] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"result": self.text, "sources": [s.to_dict() for s in self.sources]}

    def with_trailer(self) -> str:
        """Text + a human-readable citation trailer, for callers that only
        render plain text (the current LLM tool-output contract)."""
        if not self.sources:
            return self.text
        citations = "; ".join(s.as_citation() for s in self.sources)
        return f"{self.text}\n\n_Source: {citations}_"
