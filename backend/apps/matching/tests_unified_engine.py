"""Tests for the unified matching engine (Phase D). Pure/offline via fakes."""
from types import SimpleNamespace

from apps.matching.engine import (
    UnifiedMatchingEngine,
    EligibilityEngine,
    RankingEngine,
    WEIGHTS,
)


class _Tag:
    def __init__(self, name):
        self.name = name


class _Tags:
    def __init__(self, names):
        self._t = [_Tag(n) for n in names]

    def all(self):
        return self._t


def _job(**kw):
    base = dict(
        location="Cairo, Egypt",
        location_type="onsite",
        experience_level="mid",
        salary_min=1000,
        salary_max=2000,
        company=SimpleNamespace(industry="Software"),
    )
    base.update(kw)
    job = SimpleNamespace(**base)
    job.tags = _Tags(kw.pop("skills", ["python", "django", "sql"]) if "skills" in kw else ["python", "django", "sql"])
    return job


def _profile(**kw):
    base = dict(
        skills=["Python", "Django"],
        desired_locations=["Cairo"],
        experience_years=4,
        min_salary=1000,
        preferred_industries=["Software"],
        open_to_remote=False,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_weights_sum_to_100():
    assert sum(WEIGHTS.values()) == 100


def test_deterministic_same_inputs_same_score():
    eng = UnifiedMatchingEngine()
    p, j = _profile(), _job()
    s1 = eng.score(p, j)
    s2 = eng.score(p, j)
    assert s1 == s2  # determinism is the whole point of convergence


def test_partial_skill_match_scales_score():
    eng = UnifiedMatchingEngine()
    # profile has 2 of 3 job skills → skills factor ~ 66% of 40
    r = eng.match(_profile(), _job())
    assert r.breakdown["skills"]["score"] == 67  # round(2/3*100)
    assert "python" in r.breakdown["skills"]["matched"]
    assert "sql" in r.breakdown["skills"]["missing"]


def test_full_match_high_score():
    eng = UnifiedMatchingEngine()
    p = _profile(skills=["Python", "Django", "SQL"])
    r = eng.match(p, _job())
    assert r.overall_score >= 80
    assert r.eligible is True
    assert r.recommendation


def test_eligibility_salary_floor_fails():
    # candidate wants 5000; job max 2000 → below 80% tolerance → ineligible
    eligible, failures = EligibilityEngine.check(
        _profile(min_salary=5000), _job(salary_min=1500, salary_max=2000)
    )
    assert eligible is False
    assert failures


def test_explanation_lists_matched_and_missing():
    eng = UnifiedMatchingEngine()
    r = eng.match(_profile(), _job())
    assert any("Matching skills" in s for s in r.strengths)
    assert any("Missing skills" in g for g in r.gaps)


def test_ranking_and_match_agree():
    eng = UnifiedMatchingEngine()
    p, j = _profile(), _job()
    ranking_only, _ = RankingEngine.score(p, j)
    assert abs(ranking_only - eng.match(p, j).overall_score) < 0.001
