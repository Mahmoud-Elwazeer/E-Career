"""GitHub Profile Review (Professional Presence §31).

Reviews a candidate's PUBLIC GitHub profile signals against a target role and
returns evidence-based, actionable feedback. Deterministic, no AI. The GitHub
data fetcher is INJECTED so this is unit-testable offline and never hard-depends
on network availability; a live fetcher (public GitHub REST API, no auth needed
for public data) can be supplied in the view/service layer.

We assess REAL, checkable signals only:
- repo count, non-fork original work, languages used
- READMEs / descriptions present (documentation signal)
- recent activity (staleness)
- coverage of the target role's key languages/skills

No fabrication: a language/skill is "demonstrated" only if a real repo uses it.
"""
from __future__ import annotations

from typing import Callable, Iterable, Optional
from datetime import datetime, timezone


# fetcher(username) -> {"profile": {...}, "repos": [ {...}, ... ]} using public
# GitHub REST shapes (repos have: name, fork, language, description, pushed_at,
# stargazers_count, has_readme(optional)).
GitHubFetcher = Callable[[str], dict]


class GitHubReviewService:
    def review(
        self,
        username: str,
        *,
        fetcher: GitHubFetcher,
        target_languages: Optional[Iterable[str]] = None,
        now: Optional[datetime] = None,
    ) -> dict:
        now = now or datetime.now(timezone.utc)
        target_languages = [l.lower().strip() for l in (target_languages or []) if l]

        try:
            data = fetcher(username)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"{type(e).__name__}: {e}", "username": username}

        repos = data.get("repos", []) or []
        originals = [r for r in repos if not r.get("fork")]
        languages = sorted({(r.get("language") or "").lower() for r in originals if r.get("language")})
        documented = [r for r in originals if (r.get("description") or "").strip() or r.get("has_readme")]
        stars = sum(int(r.get("stargazers_count") or 0) for r in originals)

        most_recent = self._most_recent_push(originals)
        stale_days = None
        if most_recent:
            stale_days = (now - most_recent).days

        checks: list[dict] = []
        if len(originals) == 0:
            checks.append(self._fail("original_work", "No original (non-fork) repositories.",
                                     "Publish at least 1-2 original projects that show your work."))
        else:
            checks.append(self._pass("original_work", f"{len(originals)} original repo(s)."))

        if originals and len(documented) / len(originals) < 0.5:
            checks.append(self._warn("documentation", "Most repos lack a description/README.",
                                     "Add a short README + description to each key repo."))
        elif originals:
            checks.append(self._pass("documentation", "Most repos are documented."))

        if stale_days is not None and stale_days > 365:
            checks.append(self._warn("activity", f"No pushes in ~{stale_days} days.",
                                     "Recent commits signal you're active; push some work."))
        elif stale_days is not None:
            checks.append(self._pass("activity", f"Active (last push ~{stale_days} days ago)."))

        # Target-language coverage (evidence-based).
        lang_coverage = None
        if target_languages:
            present = sorted(set(target_languages) & set(languages))
            missing = sorted(set(target_languages) - set(languages))
            cov = round(100 * len(present) / len(target_languages))
            lang_coverage = {
                "present": present, "missing": missing, "coverage_percent": cov,
                "recommendation": (
                    f"No public repos demonstrate: {', '.join(missing)}. Add a project using them."
                    if missing else "Your repos demonstrate the target languages."
                ),
            }

        score = self._score(checks, lang_coverage)
        return {
            "ok": True,
            "username": username,
            "stats": {
                "original_repos": len(originals),
                "languages": languages,
                "documented_repos": len(documented),
                "total_stars": stars,
                "days_since_last_push": stale_days,
            },
            "checks": checks,
            "language_coverage": lang_coverage,
            "score": score,
            "band": self._band(score),
            "action_items": [c["fix"] for c in checks if c.get("fix")]
                            + ([lang_coverage["recommendation"]] if lang_coverage and lang_coverage["missing"] else []),
        }

    def _most_recent_push(self, repos) -> Optional[datetime]:
        best = None
        for r in repos:
            ts = r.get("pushed_at")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            if best is None or dt > best:
                best = dt
        return best

    def _pass(self, f, m): return {"field": f, "status": "pass", "detail": m}
    def _warn(self, f, m, fix): return {"field": f, "status": "warn", "detail": m, "fix": fix}
    def _fail(self, f, m, fix): return {"field": f, "status": "fail", "detail": m, "fix": fix}

    def _score(self, checks, lang_cov) -> int:
        w = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
        base = (sum(w[c["status"]] for c in checks) / len(checks)) if checks else 0
        if lang_cov is not None:
            base = 0.7 * base + 0.3 * (lang_cov["coverage_percent"] / 100)
        return round(100 * base)

    def _band(self, s) -> str:
        if s >= 85: return "excellent"
        if s >= 70: return "good"
        if s >= 50: return "fair"
        return "needs_work"


github_review_service = GitHubReviewService()
