"""CV <-> Job Match Report (Professional Presence §31 item B).

Produces ONE explainable report of how well a candidate's CV/profile matches a
specific job, GROUNDED in the deterministic UnifiedMatchingEngine (not a new,
opaque score). It fuses two already-authoritative engines:

  1. UnifiedMatchingEngine  → the fit SCORE + per-factor breakdown
     (skills/experience/location/salary/industry) and matched/missing/gaps.
  2. ATSReadinessService    → whether the CV will PARSE for this job's ATS and
     how well it covers the job's keywords.

Design constraints (recurring directive):
- Do NOT invent a second matching score. The overall fit number IS the matching
  engine's number, so a candidate never sees two different scores for the same
  pairing (the "different score on different pages" bug this platform has hit).
- Everything is evidence-backed and actionable: matched vs missing skills,
  keyword gaps, concrete next steps.
- Deterministic; no AI dependency (works while Bedrock is blocked). An optional
  AI layer may enrich phrasing later without changing the numbers.
"""
from __future__ import annotations

from typing import Optional

from apps.matching.engine import unified_matching_engine
from apps.career.ats_readiness_service import ats_readiness_service


class CVJobMatchService:
    """Builds a CV<->Job match report grounded in the matching engine."""

    def build_report(self, *, profile, job, cv_text: str = "") -> dict:
        # 1) Fit score + breakdown from the ONE authoritative engine.
        match = unified_matching_engine.match(profile, job)

        # 2) ATS parsing + keyword alignment for this specific job (if we have
        #    the CV text). Reuses the readiness engine; no new score.
        ats = None
        if cv_text:
            ats = ats_readiness_service.build_report(cv_text, job=job)

        # 3) Consolidated, actionable next steps — derived from real gaps, not
        #    generic advice.
        action_items = self._action_items(match, ats)

        return {
            "job": {
                "title": getattr(job, "title", ""),
                "company": getattr(getattr(job, "company", None), "name", ""),
                "ats_platform": getattr(job, "ats_platform", ""),
                "direct_apply_url": getattr(job, "direct_apply_url", ""),
            },
            # The fit score IS the matching engine's — single source of truth.
            "fit": {
                "overall_score": round(match.overall_score, 1),
                "eligible": match.eligible,
                "breakdown": match.breakdown,
                "matched_requirements": match.matched_requirements,
                "missing_requirements": match.missing_requirements,
                "strengths": match.strengths,
                "gaps": match.gaps,
                "eligibility_failures": match.eligibility_failures,
                "recommendation": match.recommendation,
            },
            # ATS readiness is a SEPARATE dimension (parse-ability != fit).
            "ats_readiness": (
                {
                    "parsing_band": ats["parsing_compatibility"]["band"],
                    "parsing_score": ats["parsing_compatibility"]["overall_score"],
                    "keyword_alignment": ats.get("job_alignment"),
                    "ats_note": ats.get("ats_note"),
                }
                if ats else None
            ),
            "action_items": action_items,
            "summary": self._summary(match, ats),
        }

    def _action_items(self, match, ats) -> list[dict]:
        items: list[dict] = []
        # Missing skills are the highest-leverage, most concrete gap.
        for skill in match.missing_requirements[:5]:
            items.append({
                "type": "add_skill_evidence",
                "priority": "high",
                "detail": f"Show evidence of '{skill}' (project, bullet, or keyword) — required by this job.",
            })
        # Eligibility blockers come next.
        for fail in match.eligibility_failures:
            items.append({"type": "eligibility", "priority": "high", "detail": fail})
        # ATS parsing fixes.
        if ats:
            band = ats["parsing_compatibility"]["band"]
            if band in ("fair", "needs_work"):
                for rec in ats["parsing_compatibility"]["recommendations"][:3]:
                    items.append({"type": "ats_parsing", "priority": "medium", "detail": rec})
            ja = ats.get("job_alignment")
            if ja and ja.get("keyword_coverage_score", 100) < 50:
                items.append({
                    "type": "keyword_coverage", "priority": "medium",
                    "detail": "Mirror more key terms from the job description in your CV.",
                })
        return items

    def _summary(self, match, ats) -> str:
        pieces = [
            f"Fit {round(match.overall_score)}/100 — {match.recommendation}"
        ]
        if not match.eligible:
            pieces.append("Note: currently ineligible on a hard requirement (see failures).")
        if ats:
            pieces.append(
                f"CV ATS parsing: {ats['parsing_compatibility']['band']} "
                f"({ats['parsing_compatibility']['overall_score']}/100)."
            )
        return " ".join(pieces)


cv_job_match_service = CVJobMatchService()
