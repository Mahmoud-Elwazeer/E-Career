"""Portfolio Evidence Builder (Professional Presence §31).

Assembles a candidate's VERIFIABLE portfolio evidence (projects, repos, live
links, publications) and assesses how well it substantiates the skills a target
role needs. The point of the platform's moat is evidence over claims — this
turns a flat skills list into "which skills are actually backed by a shippable
artifact".

Deterministic, no AI, no external calls (link liveness checks are optional and
injected). Never fabricates evidence: a skill is only "backed" if a real
artifact references it.
"""
from __future__ import annotations

import re
from typing import Callable, Iterable, Optional


_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]{1,}", (text or "").lower()))


class PortfolioEvidenceService:
    """Builds a portfolio-evidence report grounded in real artifacts."""

    def build(
        self,
        *,
        projects: Optional[list[dict]] = None,
        target_skills: Optional[Iterable[str]] = None,
        link_checker: Optional[Callable[[str], bool]] = None,
    ) -> dict:
        """projects: [{name, description, url, tech:[...], role, highlights:[...]}]
        target_skills: skills the role needs (to compute evidence coverage).
        link_checker: optional fn(url)->bool for liveness (injected; offline-safe).
        """
        projects = projects or []
        target_skills = [s.lower().strip() for s in (target_skills or []) if s]

        assessed: list[dict] = []
        evidence_by_skill: dict[str, list[str]] = {s: [] for s in target_skills}

        for p in projects:
            name = p.get("name") or p.get("title") or "Untitled project"
            url = (p.get("url") or "").strip()
            tech = [t.lower().strip() for t in (p.get("tech") or []) if t]
            blob = _tokens(" ".join([
                name, p.get("description", ""), " ".join(tech),
                " ".join(p.get("highlights") or []),
            ]))

            has_link = bool(url) and bool(_URL_RE.match(url))
            link_live = None
            if has_link and link_checker is not None:
                try:
                    link_live = bool(link_checker(url))
                except Exception:
                    link_live = None

            # Strength: verifiable link + concrete description + tech + highlights.
            strength = 0
            reasons = []
            if has_link:
                strength += 40; reasons.append("has_link")
            if len((p.get("description") or "")) >= 60:
                strength += 20; reasons.append("described")
            if tech:
                strength += 20; reasons.append("tech_listed")
            if p.get("highlights"):
                strength += 20; reasons.append("has_highlights")

            # Which target skills this project backs.
            backs = sorted({s for s in target_skills if s in blob or s in tech})
            for s in backs:
                evidence_by_skill[s].append(name)

            assessed.append({
                "name": name,
                "url": url,
                "has_verifiable_link": has_link,
                "link_live": link_live,
                "strength": strength,
                "strength_reasons": reasons,
                "backs_skills": backs,
            })

        backed = [s for s, evs in evidence_by_skill.items() if evs]
        unbacked = [s for s in target_skills if s not in backed]
        coverage = round(100 * len(backed) / len(target_skills)) if target_skills else 0

        return {
            "projects": assessed,
            "project_count": len(assessed),
            "strong_project_count": sum(1 for a in assessed if a["strength"] >= 60),
            "skill_evidence_coverage_percent": coverage,
            "skills_backed_by_evidence": backed,
            "skills_missing_evidence": unbacked,
            "evidence_by_skill": {s: evs for s, evs in evidence_by_skill.items() if evs},
            "action_items": self._actions(assessed, unbacked),
            "summary": self._summary(assessed, coverage, unbacked),
        }

    def _actions(self, assessed, unbacked) -> list[dict]:
        items = []
        for skill in unbacked[:5]:
            items.append({
                "type": "add_evidence", "priority": "high",
                "detail": f"Add a project/repo demonstrating '{skill}' — it's required but unproven.",
            })
        for a in assessed:
            if not a["has_verifiable_link"]:
                items.append({
                    "type": "add_link", "priority": "medium",
                    "detail": f"Add a live link (repo/demo) for '{a['name']}' so it's verifiable.",
                })
            elif a["strength"] < 60:
                items.append({
                    "type": "strengthen_project", "priority": "low",
                    "detail": f"Strengthen '{a['name']}': add description, tech stack, and impact highlights.",
                })
        return items

    def _summary(self, assessed, coverage, unbacked) -> str:
        parts = [f"{len(assessed)} project(s); skill-evidence coverage {coverage}%."]
        if unbacked:
            parts.append(f"Unproven target skills: {', '.join(unbacked[:5])}.")
        return " ".join(parts)


portfolio_evidence_service = PortfolioEvidenceService()
