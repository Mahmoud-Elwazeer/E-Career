"""LinkedIn Profile Guidance (Professional Presence §31).

Produces deterministic, evidence-based guidance to strengthen a candidate's
LinkedIn profile for a target role/industry. No AI dependency (works while
Bedrock is blocked); no scraping of LinkedIn (ToS-safe) — it analyzes data the
candidate already gave us (profile + optional target job) and returns concrete,
checkable recommendations.

Grounding (recurring directive: expose evidence, not an opaque score):
- Each check reports pass/fail + WHY + a concrete fix.
- The optional target-role keyword check reuses the same keyword logic style as
  the ATS engine so guidance is consistent across the platform.

This is guidance, NOT automation: we never post or edit anything on the user's
behalf.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional


# LinkedIn's documented, stable limits (used for length guidance).
HEADLINE_MAX = 220
ABOUT_RECOMMENDED_MIN = 200      # chars — a too-short About underperforms
ABOUT_MAX = 2600
SKILLS_RECOMMENDED_MIN = 5
SKILLS_MAX = 50


def _words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]{1,}", (text or "").lower())


class LinkedInGuidanceService:
    """Deterministic LinkedIn profile checks + recommendations."""

    def analyze(
        self,
        *,
        headline: str = "",
        about: str = "",
        skills: Optional[Iterable[str]] = None,
        experience_count: int = 0,
        has_photo: bool = False,
        target_role: str = "",
        target_keywords: Optional[Iterable[str]] = None,
    ) -> dict:
        skills = [s for s in (skills or []) if s]
        checks: list[dict] = []

        # 1) Headline
        h = (headline or "").strip()
        if not h:
            checks.append(self._fail("headline", "Headline is empty.",
                                     "Add a headline: role + specialty + value (e.g. "
                                     "'Backend Engineer | Python, Django | Scaling APIs')."))
        elif len(h) < 30:
            checks.append(self._warn("headline", f"Headline is short ({len(h)} chars).",
                                     "Expand to include specialty and value, not just a job title."))
        elif len(h) > HEADLINE_MAX:
            checks.append(self._fail("headline", f"Headline exceeds {HEADLINE_MAX} chars.",
                                     "Trim to the most important role + skills."))
        else:
            checks.append(self._pass("headline", "Headline length is in a good range."))

        # 2) About / summary
        a = (about or "").strip()
        if not a:
            checks.append(self._fail("about", "About section is empty.",
                                     "Write 2-4 short paragraphs: who you are, key skills, "
                                     "notable results, and what you're looking for."))
        elif len(a) < ABOUT_RECOMMENDED_MIN:
            checks.append(self._warn("about", f"About is short ({len(a)} chars).",
                                     "Aim for a fuller summary with concrete achievements and metrics."))
        elif len(a) > ABOUT_MAX:
            checks.append(self._fail("about", f"About exceeds {ABOUT_MAX} chars.",
                                     "Tighten to the strongest content."))
        else:
            checks.append(self._pass("about", "About length is in a good range."))

        # 3) Skills
        if len(skills) < SKILLS_RECOMMENDED_MIN:
            checks.append(self._warn("skills", f"Only {len(skills)} skills listed.",
                                     f"Add at least {SKILLS_RECOMMENDED_MIN} relevant skills so you "
                                     "surface in more recruiter searches."))
        elif len(skills) > SKILLS_MAX:
            checks.append(self._warn("skills", f"{len(skills)} skills — over LinkedIn's {SKILLS_MAX} cap.",
                                     "Keep the most relevant skills; prune the rest."))
        else:
            checks.append(self._pass("skills", f"{len(skills)} skills listed."))

        # 4) Photo + experience presence (basic completeness)
        if not has_photo:
            checks.append(self._warn("photo", "No profile photo.",
                                     "Add a clear, professional headshot — profiles with photos get "
                                     "far more engagement."))
        if experience_count <= 0:
            checks.append(self._warn("experience", "No experience entries.",
                                     "Add roles with 2-4 achievement bullets each (impact + metrics)."))

        # 5) Target-role keyword alignment (optional, evidence-based)
        keyword_alignment = None
        if target_role or target_keywords:
            kws = {k.lower() for k in (target_keywords or []) if k}
            if target_role:
                kws |= set(_words(target_role))
            profile_blob = set(_words(f"{headline} {about} {' '.join(skills)}"))
            present = sorted(kws & profile_blob)
            missing = sorted(kws - profile_blob)
            coverage = round(100 * len(present) / len(kws)) if kws else 0
            keyword_alignment = {
                "target_role": target_role,
                "coverage_percent": coverage,
                "present_keywords": present,
                "missing_keywords": missing[:15],
                "recommendation": (
                    "Weave the missing keywords naturally into your headline/about/skills."
                    if missing else "Strong keyword alignment with the target role."
                ),
            }

        score = self._completeness(checks)
        return {
            "completeness_score": score,
            "band": self._band(score),
            "checks": checks,
            "keyword_alignment": keyword_alignment,
            "summary": self._summary(score, checks, keyword_alignment),
        }

    # helpers ----------------------------------------------------------------
    def _pass(self, field, msg): return {"field": field, "status": "pass", "detail": msg}
    def _warn(self, field, msg, fix): return {"field": field, "status": "warn", "detail": msg, "fix": fix}
    def _fail(self, field, msg, fix): return {"field": field, "status": "fail", "detail": msg, "fix": fix}

    def _completeness(self, checks) -> int:
        if not checks:
            return 0
        weight = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
        got = sum(weight[c["status"]] for c in checks)
        return round(100 * got / len(checks))

    def _band(self, score: int) -> str:
        if score >= 85: return "excellent"
        if score >= 70: return "good"
        if score >= 50: return "fair"
        return "needs_work"

    def _summary(self, score, checks, kw) -> str:
        fails = [c["field"] for c in checks if c["status"] == "fail"]
        parts = [f"LinkedIn completeness: {self._band(score)} ({score}/100)."]
        if fails:
            parts.append("Fix first: " + ", ".join(fails) + ".")
        if kw and kw["missing_keywords"]:
            parts.append(f"Add target-role keywords: {', '.join(kw['missing_keywords'][:5])}.")
        return " ".join(parts)


linkedin_guidance_service = LinkedInGuidanceService()
