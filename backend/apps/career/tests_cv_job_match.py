"""Tests for the CV<->Job Match Report (§31 item B).

Verifies the report is GROUNDED in the UnifiedMatchingEngine (same fit score,
not a second opaque number), fuses ATS readiness as a separate dimension, and
produces concrete action items from real gaps. Uses fakes; no DB.
"""
from apps.career.cv_job_match_service import cv_job_match_service
from apps.matching.engine import unified_matching_engine


class _Tag:
    def __init__(self, name): self.name = name
class _TagMgr:
    def __init__(self, names): self._t = [_Tag(n) for n in names]
    def all(self): return self._t
class _Company:
    def __init__(self, name="Acme", industry="technology"):
        self.name = name; self.industry = industry
class _Job:
    def __init__(self):
        self.title = "Senior Backend Engineer"
        self.description = ("We need a Senior Backend Engineer with Python, Django and "
                            "PostgreSQL experience. Responsibilities include building APIs. " * 5)
        self.location = "Remote, United States"
        self.location_type = "remote"
        self.experience_level = "senior"
        self.tags = _TagMgr(["python", "django", "postgresql", "kubernetes"])
        self.salary_min = 120000; self.salary_max = 160000
        self.company = _Company()
        self.ats_platform = "greenhouse"
        self.direct_apply_url = "https://boards.greenhouse.io/acme/jobs/1"
class _Profile:
    def __init__(self):
        self.skills = ["Python", "Django", "PostgreSQL"]
        self.experience_years = 8
        self.min_salary = 120000
        self.open_to_remote = True
        self.desired_locations = []
        self.preferred_industries = ["technology"]


CV_TEXT = """
John Doe
Email: john@example.com | Phone: 555-1234
Experience
Senior Backend Engineer at FooCorp (2018-2024)
- Built Python and Django services backed by PostgreSQL
Skills
Python, Django, PostgreSQL, REST APIs
Education
BSc Computer Science
"""


def test_fit_score_equals_matching_engine():
    prof, job = _Profile(), _Job()
    report = cv_job_match_service.build_report(profile=prof, job=job, cv_text=CV_TEXT)
    engine_score = round(unified_matching_engine.match(prof, job).overall_score, 1)
    # The report's fit score MUST be the matching engine's number, not a new one.
    assert report["fit"]["overall_score"] == engine_score


def test_report_has_ats_readiness_dimension_when_cv_given():
    report = cv_job_match_service.build_report(profile=_Profile(), job=_Job(), cv_text=CV_TEXT)
    assert report["ats_readiness"] is not None
    assert "parsing_band" in report["ats_readiness"]
    # greenhouse note should be attached
    note = report["ats_readiness"]["ats_note"]
    assert note and note["ats_platform"] == "greenhouse"


def test_missing_skill_becomes_action_item():
    report = cv_job_match_service.build_report(profile=_Profile(), job=_Job(), cv_text=CV_TEXT)
    # job requires kubernetes; profile lacks it -> should appear as an add_skill action
    details = " ".join(a["detail"].lower() for a in report["action_items"])
    assert "kubernetes" in details


def test_no_cv_text_still_produces_fit_without_ats():
    report = cv_job_match_service.build_report(profile=_Profile(), job=_Job())
    assert report["ats_readiness"] is None
    assert report["fit"]["overall_score"] >= 0


def test_job_metadata_carried_through():
    report = cv_job_match_service.build_report(profile=_Profile(), job=_Job(), cv_text=CV_TEXT)
    assert report["job"]["company"] == "Acme"
    assert report["job"]["ats_platform"] == "greenhouse"
    assert report["job"]["direct_apply_url"].startswith("https://boards.greenhouse.io/")


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
