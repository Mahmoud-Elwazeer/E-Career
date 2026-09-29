"""Tests for CV→Profile sync with conflict flagging (Phase B, §20). Offline."""
from types import SimpleNamespace

from apps.profiles.cv_sync import sync_cv_to_profile


PARSED = {
    "skills": {"technical": ["Python", "Django"], "languages": ["English"]},
    "experience": [{"title": "Senior Engineer", "start_date": "2020-01", "end_date": "Present"}],
    "education": ["BSc CS"],
    "personal": {"portfolio": "https://p.example"},
}


def _empty_profile():
    return SimpleNamespace(skills=[], languages=[], experience_years=0,
                           current_role="", education=[], certifications=[],
                           portfolio_url="")


def test_empty_profile_gets_filled():
    p = _empty_profile()
    r = sync_cv_to_profile(p, PARSED)
    assert p.skills == ["Python", "Django"]
    assert p.current_role == "Senior Engineer"
    assert p.experience_years >= 5
    assert "skills" in r.applied and "current_role" in r.applied
    assert r.conflicts == []


def test_matching_values_confirmed_not_conflicted():
    p = SimpleNamespace(skills=["Python", "Django"], languages=["English"],
                        experience_years=6, current_role="Senior Engineer",
                        education=["BSc CS"], certifications=[], portfolio_url="")
    r = sync_cv_to_profile(p, PARSED)
    assert "skills" in r.confirmed
    assert not r.conflicts  # everything agrees


def test_differing_values_flagged_not_overwritten():
    p = SimpleNamespace(skills=["Python", "Django"], languages=["English"],
                        experience_years=5, current_role="Product Manager",
                        education=["BSc CS"], certifications=[], portfolio_url="")
    r = sync_cv_to_profile(p, PARSED)
    # user values preserved
    assert p.current_role == "Product Manager"
    assert p.experience_years == 5
    conflict_fields = {c.field for c in r.conflicts}
    assert "current_role" in conflict_fields
    assert "experience_years" in conflict_fields
    assert r.to_dict()["has_conflicts"] is True


def test_apply_false_does_not_mutate():
    p = _empty_profile()
    r = sync_cv_to_profile(p, PARSED, apply=False)
    assert p.skills == []  # not mutated
    assert "skills" in r.applied  # but reported as fillable


def test_empty_parsed_data_noop():
    p = _empty_profile()
    r = sync_cv_to_profile(p, {})
    assert r.applied == [] and r.conflicts == []
