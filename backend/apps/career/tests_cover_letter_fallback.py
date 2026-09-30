"""Tests for the grounded (AI-unavailable) cover-letter fallback (§31).

Verifies that when the AI path is down, the letter is deterministic and
references the candidate's ACTUAL matched skills (via the matching engine),
never fabricating. Uses fakes; no DB/AI.
"""
from apps.career.cover_letter_service import cover_letter_service as S


class _Tag:
    def __init__(self, n): self.name = n
class _TagMgr:
    def __init__(self, names): self._t = [_Tag(n) for n in names]
    def all(self): return self._t
class _Company:
    def __init__(self): self.name = "Acme"; self.industry = "technology"
class _Job:
    title = "Senior Backend Engineer"
    description = "Python and Django role."
    def __init__(self):
        self.company = _Company()
        self.tags = _TagMgr(["python", "django", "kubernetes"])
        self.location = "Remote"; self.location_type = "remote"
        self.experience_level = "senior"; self.salary_min = 120000; self.salary_max = 160000
class _Profile:
    skills = ["Python", "Django", "PostgreSQL"]
    experience_years = 8; min_salary = 120000; open_to_remote = True
    desired_locations = []; preferred_industries = ["technology"]
class _User:
    def __init__(self):
        self.career_profile = _Profile()
    def get_full_name(self): return "Jane Dev"


def test_join_human():
    assert S._join_human(["a"]) == "a"
    assert S._join_human(["a", "b"]) == "a and b"
    assert S._join_human(["a", "b", "c"]) == "a, b, and c"


def test_grounded_fallback_references_matched_skills():
    letter = S._grounded_fallback(_User(), _Job())
    low = letter.lower()
    # matched skills python+django should appear; unmatched kubernetes must NOT
    assert "python" in low
    assert "django" in low
    assert "kubernetes" not in low  # candidate doesn't have it -> not fabricated
    assert "Jane Dev" in letter
    assert "Senior Backend Engineer" in letter
    assert "Acme" in letter


def test_grounded_fallback_without_profile_is_generic_but_valid():
    class U:
        def get_full_name(self): return "No Profile"
    letter = S._grounded_fallback(U(), _Job())
    assert "No Profile" in letter
    assert "core requirements" in letter.lower()  # generic sentence, no fabricated skills


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
