"""Matching-flow tests for newly-ingested jobs (§16).

Proves an ingested Job (as produced by the orchestrator) flows into the
UnifiedMatchingEngine and yields a deterministic, explainable score — WITHOUT a
DB, using lightweight fakes shaped like the real Job/Profile/Company/Tag.
"""
from apps.matching.engine import UnifiedMatchingEngine, WEIGHTS


class _Tag:
    def __init__(self, name): self.name = name


class _TagMgr:
    def __init__(self, names): self._t = [_Tag(n) for n in names]
    def all(self): return self._t


class _Company:
    def __init__(self, industry="technology"): self.industry = industry


class _Job:
    """Shaped like an ingested Job (fields the orchestrator populates)."""
    def __init__(self, *, title, location, location_type, experience_level,
                 skills, salary_min=None, salary_max=None, industry="technology"):
        self.title = title
        self.location = location
        self.location_type = location_type
        self.experience_level = experience_level
        self.tags = _TagMgr(skills)
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.company = _Company(industry)


class _Profile:
    def __init__(self, *, skills, experience_years=None, min_salary=None,
                 open_to_remote=False, desired_locations=None, preferred_industries=None):
        self.skills = skills
        self.experience_years = experience_years
        self.min_salary = min_salary
        self.open_to_remote = open_to_remote
        self.desired_locations = desired_locations or []
        self.preferred_industries = preferred_industries or []


ENG = UnifiedMatchingEngine()


def test_weights_sum_to_100():
    assert sum(WEIGHTS.values()) == 100


def test_strong_candidate_scores_high_and_eligible():
    job = _Job(title="Senior Backend Engineer", location="Remote, United States",
               location_type="remote", experience_level="senior",
               skills=["python", "django", "postgres"], salary_min=120000, salary_max=160000)
    prof = _Profile(skills=["Python", "Django", "PostgreSQL", "AWS"],
                    experience_years=8, min_salary=120000, open_to_remote=True,
                    preferred_industries=["technology"])
    r = ENG.match(prof, job)
    assert r.eligible is True
    assert r.overall_score >= 70, r.to_dict()
    assert "python" in [s.lower() for s in r.matched_requirements]


def test_deterministic_same_inputs_same_score():
    job = _Job(title="Data Scientist", location="Cairo", location_type="onsite",
               experience_level="mid", skills=["python", "ml"], salary_min=30000)
    prof = _Profile(skills=["python"], experience_years=4)
    a = ENG.match(prof, job).overall_score
    b = ENG.match(prof, job).overall_score
    assert a == b


def test_salary_floor_makes_ineligible():
    job = _Job(title="Junior Dev", location="Remote", location_type="remote",
               experience_level="entry", skills=["python"],
               salary_min=20000, salary_max=25000)
    prof = _Profile(skills=["python"], experience_years=1, min_salary=100000)
    r = ENG.match(prof, job)
    # job max (25k) far below 80% of candidate min (100k) -> ineligible on comp
    assert r.eligible is False
    assert any("Salary below" in f for f in r.eligibility_failures)


def test_missing_skills_surface_as_gaps():
    job = _Job(title="ML Engineer", location="Remote", location_type="remote",
               experience_level="mid", skills=["python", "tensorflow", "kubernetes"])
    prof = _Profile(skills=["python"], experience_years=4, open_to_remote=True)
    r = ENG.match(prof, job)
    missing = [m.lower() for m in r.missing_requirements]
    assert "tensorflow" in missing and "kubernetes" in missing


def test_job_with_no_skills_does_not_crash():
    job = _Job(title="Generalist", location="Remote", location_type="remote",
               experience_level="mid", skills=[])
    prof = _Profile(skills=["python"], experience_years=4)
    r = ENG.match(prof, job)  # must not raise
    assert 0 <= r.overall_score <= 100


if __name__ == "__main__":
    import sys
    fns = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
