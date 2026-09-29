"""Talent Qualification contract (Phase B, §11/§18).

Produces an EVIDENCE-BASED qualification verdict, not a single opaque AI score.
It consumes the existing deterministic dimension scores from ScoringEngine
(skill/experience/education/portfolio/interview/...) and packages them into a
clear contract the platform + employers can trust:

  qualification_state : qualified | partially_qualified | not_qualified | insufficient_evidence
  evidence            : which dimensions have real backing + their confidence
  missing_evidence    : which dimensions are empty/weak and what would fill them
  job_family_relevance: optional relevance to a target job family (0-1)
  confidence          : aggregate confidence of the verdict
  updated_at          : timestamp

Deterministic — no AI dependency, so it works while Bedrock is blocked. AI can
later enrich the narrative, but the STATE is reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# Dimensions that count as real "evidence" and the minimum score/confidence
# for that dimension to be considered backed by evidence (not just a default).
EVIDENCE_DIMENSIONS = {
    "skill_score": "Skills (from CV/profile/assessments)",
    "experience_score": "Work experience history",
    "education_score": "Education records",
    "portfolio_score": "Portfolio / projects",
    "interview_score": "Interview performance",
}

MIN_EVIDENCE_CONFIDENCE = 0.35
QUALIFIED_THRESHOLD = 0.65
PARTIAL_THRESHOLD = 0.45


@dataclass
class QualificationResult:
    qualification_state: str
    overall: float
    confidence: float
    evidence: list[dict] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    job_family_relevance: Optional[float] = None
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "qualification_state": self.qualification_state,
            "overall": round(self.overall, 3),
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "missing_evidence": self.missing_evidence,
            "job_family_relevance": (
                round(self.job_family_relevance, 3)
                if self.job_family_relevance is not None else None
            ),
            "explanation": self.explanation,
        }


class QualificationService:
    """Builds a qualification verdict from deterministic dimension scores."""

    def qualify(self, profile, *, target_job_family: str = "") -> QualificationResult:
        scores = self._dimension_scores(profile)

        evidence: list[dict] = []
        missing: list[str] = []
        backed = 0

        for dim, label in EVIDENCE_DIMENSIONS.items():
            res = scores.get(dim)
            value = getattr(res, "value", 0.0) if res is not None else 0.0
            conf = getattr(res, "confidence", 0.0) if res is not None else 0.0
            if value > 0 and conf >= MIN_EVIDENCE_CONFIDENCE:
                backed += 1
                evidence.append({
                    "dimension": dim,
                    "label": label,
                    "value": round(value, 3),
                    "confidence": round(conf, 3),
                })
            else:
                missing.append(label)

        overall, agg_conf = self._composite(scores)

        # Not enough dimensions have real backing → don't pretend to qualify.
        if backed < 2:
            state = "insufficient_evidence"
        elif overall >= QUALIFIED_THRESHOLD:
            state = "qualified"
        elif overall >= PARTIAL_THRESHOLD:
            state = "partially_qualified"
        else:
            state = "not_qualified"

        relevance = self._job_family_relevance(profile, target_job_family) if target_job_family else None

        explanation = (
            f"{state.replace('_', ' ').title()} — {backed}/{len(EVIDENCE_DIMENSIONS)} "
            f"evidence dimensions backed; overall {overall:.0%} "
            f"(confidence {agg_conf:.0%})."
        )
        if missing:
            explanation += f" To strengthen: {', '.join(missing[:3])}."

        return QualificationResult(
            qualification_state=state,
            overall=overall,
            confidence=agg_conf,
            evidence=evidence,
            missing_evidence=missing,
            job_family_relevance=relevance,
            explanation=explanation,
        )

    def _dimension_scores(self, profile) -> dict:
        """Get deterministic dimension scores from the existing ScoringEngine."""
        try:
            from apps.career.scoring_engine import ScoringEngine
            engine = ScoringEngine(profile=profile)
            return engine.calculate_all_scores()
        except Exception:
            return {}

    def _composite(self, scores: dict) -> tuple[float, float]:
        weights = {
            "skill_score": 0.30, "experience_score": 0.25, "education_score": 0.10,
            "portfolio_score": 0.15, "interview_score": 0.20,
        }
        total = 0.0
        conf = 0.0
        wsum = 0.0
        for dim, w in weights.items():
            res = scores.get(dim)
            if res is None:
                continue
            total += getattr(res, "value", 0.0) * w
            conf += getattr(res, "confidence", 0.0) * w
            wsum += w
        if wsum == 0:
            return 0.0, 0.0
        return round(total / wsum, 3), round(conf / wsum, 3)

    def _job_family_relevance(self, profile, family: str) -> float:
        """Cheap deterministic relevance: overlap of profile skills with the
        target family keyword(s). Real ESCO/O*NET mapping can enrich later."""
        skills = {str(s).lower() for s in (getattr(profile, "skills", None) or []) if s}
        fam = family.lower()
        if not skills:
            return 0.0
        hits = sum(1 for s in skills if s in fam or fam in s)
        return round(min(1.0, hits / max(len(skills), 1) + (0.3 if hits else 0.0)), 3)


qualification_service = QualificationService()
