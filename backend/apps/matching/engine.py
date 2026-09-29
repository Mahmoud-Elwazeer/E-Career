"""Unified matching engine (Phase D — convergence).

ONE authoritative, deterministic matching computation with a clean separation:

  EligibilityEngine  → hard pass/fail gates (work model, min salary floor, etc.)
  RankingEngine      → weighted relevance score 0-100 (skills/exp/location/salary/industry)
  ExplanationEngine  → matched/missing requirements + human-readable reasoning

Goals:
- Deterministic and stable: the same (profile, job) yields the same score
  everywhere, fixing the "different score on different pages" fragmentation.
- No AI dependency in the core path (so it works while Bedrock is blocked).
  An optional AI layer can enrich the explanation later, but the SCORE is
  deterministic and reproducible.
- Reuses the proven weighting from profiles.MatchingService._basic_match_score
  (skills 40 / location 20 / experience 15 / salary 15 / industry 10).

Profile/job attributes are read defensively via getattr so this works for both
UserProfile and CareerProfile-style objects (as the existing code does).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Weight budget (must sum to 100) — preserved from the existing deterministic path.
WEIGHTS = {
    "skills": 40,
    "location": 20,
    "experience": 15,
    "salary": 15,
    "industry": 10,
}

_EXP_RANGES = {
    "entry": (0, 2), "junior": (1, 3), "mid": (3, 6),
    "senior": (6, 10), "lead": (8, None), "executive": (10, None),
    "director": (8, None), "c_level": (10, None), "student": (0, 1),
}


@dataclass
class MatchResult:
    overall_score: float
    eligible: bool
    breakdown: dict[str, dict] = field(default_factory=dict)
    matched_requirements: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    eligibility_failures: list[str] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.7

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 1),
            "eligible": self.eligible,
            "breakdown": self.breakdown,
            "matched_requirements": self.matched_requirements,
            "missing_requirements": self.missing_requirements,
            "strengths": self.strengths,
            "gaps": self.gaps,
            "eligibility_failures": self.eligibility_failures,
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 3),
        }


def _profile_skills(profile) -> set[str]:
    skills = getattr(profile, "skills", None) or []
    out = {str(s).lower().strip() for s in skills if s}
    return out


def _job_skills(job) -> set[str]:
    tags = job.tags.all() if hasattr(job, "tags") else []
    out = {t.name.lower().strip() for t in tags if getattr(t, "name", None)}
    return out


class EligibilityEngine:
    """Hard gates. Returns (eligible, failures)."""

    @staticmethod
    def check(profile, job) -> tuple[bool, list[str]]:
        failures: list[str] = []

        # Work-model gate: if the candidate is onsite-only and job is a different
        # fixed city with no remote, that's a soft signal — we do NOT hard-fail on
        # location by default (too noisy). Hard gates are intentionally minimal.

        # Salary floor: if the candidate has a hard minimum and the job's MAX is
        # below it, they are ineligible on comp.
        min_sal = getattr(profile, "min_salary", None)
        job_max = getattr(job, "salary_max", None)
        job_min = getattr(job, "salary_min", None)
        if min_sal and (job_min or job_max):
            best = job_max or job_min
            if best and float(best) < float(min_sal) * 0.8:  # 20% tolerance band
                failures.append(
                    f"Salary below candidate minimum ({min_sal})"
                )

        return (len(failures) == 0, failures)


class RankingEngine:
    """Deterministic weighted relevance 0-100 with per-factor breakdown."""

    @staticmethod
    def score(profile, job) -> tuple[float, dict]:
        breakdown: dict[str, dict] = {}
        total = 0.0

        # Skills (40)
        pskills, jskills = _profile_skills(profile), _job_skills(job)
        if jskills:
            matched = pskills & jskills
            ratio = len(matched) / len(jskills)
            pts = ratio * WEIGHTS["skills"]
            total += pts
            breakdown["skills"] = {
                "score": round(ratio * 100),
                "weight": WEIGHTS["skills"],
                "matched": sorted(matched),
                "missing": sorted(jskills - pskills),
                "reasoning": f"{len(matched)}/{len(jskills)} required skills matched",
            }
        else:
            breakdown["skills"] = {"score": 0, "weight": WEIGHTS["skills"],
                                    "matched": [], "missing": [],
                                    "reasoning": "No required skills listed on job"}

        # Location (20)
        loc_score = 0
        desired = getattr(profile, "desired_locations", None) or []
        job_loc = (getattr(job, "location", "") or "").lower()
        if getattr(profile, "open_to_remote", False) and getattr(job, "location_type", "") == "remote":
            loc_score = 100
        elif desired and job_loc:
            if any(d and d.lower() in job_loc for d in desired):
                loc_score = 100
        total += (loc_score / 100) * WEIGHTS["location"]
        breakdown["location"] = {"score": loc_score, "weight": WEIGHTS["location"],
                                  "reasoning": "Location/remote preference alignment"}

        # Experience (15)
        exp_score = 0
        yrs = getattr(profile, "experience_years", None)
        level = getattr(job, "experience_level", "")
        if yrs is not None and level in _EXP_RANGES:
            lo, hi = _EXP_RANGES[level]
            if hi is None:
                exp_score = 100 if yrs >= lo else int((yrs / max(lo, 1)) * 100)
            elif lo <= yrs <= hi:
                exp_score = 100
            elif yrs > hi:
                exp_score = 80
            else:
                exp_score = int((yrs / max(lo, 1)) * 100)
        total += (exp_score / 100) * WEIGHTS["experience"]
        breakdown["experience"] = {"score": exp_score, "weight": WEIGHTS["experience"],
                                    "reasoning": f"{yrs} yrs vs {level or 'unspecified'} level"}

        # Salary (15)
        sal_score = 0
        min_sal = getattr(profile, "min_salary", None)
        job_min = getattr(job, "salary_min", None)
        job_max = getattr(job, "salary_max", None)
        if min_sal and (job_min or job_max):
            if job_min and float(job_min) >= float(min_sal):
                sal_score = 100
            elif job_max and float(job_max) >= float(min_sal):
                sal_score = 75
            else:
                sal_score = 30
        total += (sal_score / 100) * WEIGHTS["salary"]
        breakdown["salary"] = {"score": sal_score, "weight": WEIGHTS["salary"],
                                "reasoning": "Compensation alignment"}

        # Industry (10)
        ind_score = 0
        pref_inds = getattr(profile, "preferred_industries", None) or []
        job_ind = getattr(getattr(job, "company", None), "industry", "") or ""
        if pref_inds and job_ind and job_ind in pref_inds:
            ind_score = 100
        total += (ind_score / 100) * WEIGHTS["industry"]
        breakdown["industry"] = {"score": ind_score, "weight": WEIGHTS["industry"],
                                  "reasoning": "Industry preference alignment"}

        return min(total, 100.0), breakdown


class ExplanationEngine:
    """Turns a ranking breakdown into matched/missing/strength/gap lists."""

    @staticmethod
    def explain(breakdown: dict, overall: float) -> dict:
        matched, missing, strengths, gaps = [], [], [], []
        sk = breakdown.get("skills", {})
        matched = sk.get("matched", [])
        missing = sk.get("missing", [])
        if matched:
            strengths.append(f"Matching skills: {', '.join(matched[:5])}")
        if missing:
            gaps.append(f"Missing skills: {', '.join(missing[:5])}")
        for factor in ("location", "experience", "salary", "industry"):
            b = breakdown.get(factor, {})
            if b.get("score", 0) >= 80:
                strengths.append(f"Strong {factor} fit")
            elif b.get("score", 0) <= 30:
                gaps.append(f"Weak {factor} fit")

        if overall >= 85:
            rec = "Excellent match — strongly consider applying."
        elif overall >= 70:
            rec = "Strong match — you meet most key requirements."
        elif overall >= 55:
            rec = "Good match — worth applying if interested."
        else:
            rec = "Partial match — some gaps to address first."
        return {"matched": matched, "missing": missing,
                "strengths": strengths, "gaps": gaps, "recommendation": rec}


class UnifiedMatchingEngine:
    """The single authoritative entrypoint."""

    def match(self, profile, job) -> MatchResult:
        eligible, failures = EligibilityEngine.check(profile, job)
        overall, breakdown = RankingEngine.score(profile, job)
        ex = ExplanationEngine.explain(breakdown, overall)
        return MatchResult(
            overall_score=overall,
            eligible=eligible,
            breakdown=breakdown,
            matched_requirements=ex["matched"],
            missing_requirements=ex["missing"],
            strengths=ex["strengths"],
            gaps=ex["gaps"],
            eligibility_failures=failures,
            recommendation=ex["recommendation"],
            confidence=0.7,  # deterministic core; AI enrichment could raise this
        )

    def score(self, profile, job) -> float:
        return self.match(profile, job).overall_score


# Module-level singleton for convenient reuse.
unified_matching_engine = UnifiedMatchingEngine()
