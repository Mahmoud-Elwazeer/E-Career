"""ATS Readiness Engine (Professional Presence directive §3-§6).

Builds a structured, evidence-based ATS readiness report on top of the existing
deterministic ATSScoringService — WITHOUT inventing an opaque score. Every
component is exposed with its evidence and actionable recommendations.

Separation the directive requires (§4):
  - PARSING_COMPATIBILITY: deterministic structural rules (headers, contact,
    formatting, length, keywords) — what actually breaks ATS parsers.
  - JOB_ALIGNMENT: keyword/skill coverage vs a target job (optional).
  - ATS_NOTE: per-provider parsing note when the job's ATS is known — framed as
    KNOWN COMPATIBILITY GUIDANCE, never unverified proprietary ranking claims.

Deterministic; no AI, so it works while Bedrock is blocked.
"""
from __future__ import annotations

from typing import Optional

from apps.career.ats_scoring_service import ats_scoring_service


# Known, publicly-documented parser-friendliness guidance per ATS. These are
# PARSING-COMPATIBILITY hints (not ranking claims). Kept conservative + honest.
ATS_PARSING_NOTES = {
    "greenhouse": "Greenhouse parses standard single-column resumes well; avoid tables/columns and use standard section headers.",
    "lever": "Lever's parser prefers plain text with clear headings; avoid images and multi-column layouts.",
    "ashby": "Ashby handles standard PDFs; keep contact info in the body (not a header/footer image).",
    "workday": "Workday parsing is strict — use simple formatting, standard headers, and avoid tables/graphics.",
    "smartrecruiters": "SmartRecruiters parses standard resumes; ensure skills are in a clear Skills section.",
    "bamboohr": "BambooHR prefers simple, single-column layouts with standard section names.",
    "workable": "Workable parses common formats; keep dates consistent and headers standard.",
    "teamtailor": "Teamtailor handles standard resumes; avoid embedding key text in images.",
    "icims": "iCIMS parsing is strict with formatting — prefer simple single-column layout and standard headers.",
}

# Score bands for the honest overall readiness label.
def _band(score: int) -> str:
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 55:
        return "fair"
    return "needs_work"


class ATSReadinessService:
    """Produces a structured ATS readiness report (no opaque score)."""

    def build_report(
        self,
        cv_text: str,
        *,
        job=None,
        ats_platform: str = "",
    ) -> dict:
        job_description = ""
        detected_ats = (ats_platform or "").lower()
        job_title = ""
        if job is not None:
            job_description = getattr(job, "description", "") or ""
            job_title = getattr(job, "title", "") or ""
            if not detected_ats:
                detected_ats = (getattr(job, "ats_platform", "") or "").lower()

        # Deterministic structural scoring (existing engine).
        ats = ats_scoring_service.score(cv_text, job_description)

        parsing = {
            "overall_score": ats["overall_score"],
            "band": _band(ats["overall_score"]),
            "components": ats["section_scores"],
            "recommendations": ats["recommendations"],
        }

        report = {
            "parsing_compatibility": parsing,
            "job_alignment": None,
            "ats_note": None,
            "summary": "",
        }

        # Per-ATS parsing guidance (compatibility, NOT ranking claims).
        if detected_ats and detected_ats in ATS_PARSING_NOTES:
            report["ats_note"] = {
                "ats_platform": detected_ats,
                "guidance": ATS_PARSING_NOTES[detected_ats],
                "kind": "known_parsing_compatibility",
            }

        # Job alignment: keyword coverage (from the ATS engine) + explicit title match.
        if job is not None and job_description:
            keyword_score = ats["section_scores"].get("keyword_density", 0)
            title_present = bool(job_title) and job_title.lower() in cv_text.lower()
            report["job_alignment"] = {
                "job_title": job_title,
                "keyword_coverage_score": keyword_score,
                "title_mentioned_in_cv": title_present,
                "recommendation": (
                    "Mirror key terms from the job description; your keyword "
                    "coverage is low." if keyword_score < 50 else
                    "Good keyword coverage against this job."
                ),
            }

        # Honest summary.
        band = parsing["band"]
        pieces = [f"ATS parsing readiness: {band} ({parsing['overall_score']}/100)."]
        if report["ats_note"]:
            pieces.append(f"Detected ATS: {detected_ats}.")
        if report["job_alignment"] and report["job_alignment"]["keyword_coverage_score"] < 50:
            pieces.append("Keyword coverage vs the target job needs improvement.")
        report["summary"] = " ".join(pieces)

        return report


ats_readiness_service = ATSReadinessService()
