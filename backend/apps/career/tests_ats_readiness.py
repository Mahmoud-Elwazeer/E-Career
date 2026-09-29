"""Tests for the ATS Readiness Engine (Professional Presence §3-§6). Offline."""
from types import SimpleNamespace

from apps.career.ats_readiness_service import ats_readiness_service, ATS_PARSING_NOTES


GOOD_CV = """John Doe
john@example.com | +1 555 123 4567 | Cairo, Egypt

Professional Summary
Senior backend engineer who developed and led scalable services.

Experience
Senior Backend Engineer - Acme (2020-Present)
- Built and optimized Python/Django APIs, managed a team, improved latency.

Education
BSc Computer Science

Skills
Python, Django, PostgreSQL, REST APIs, Docker
"""


def test_report_exposes_components_not_just_a_score():
    rep = ats_readiness_service.build_report(GOOD_CV)
    pc = rep["parsing_compatibility"]
    assert "components" in pc and pc["components"]  # evidence, not opaque
    assert "recommendations" in pc
    assert pc["band"] in {"excellent", "good", "fair", "needs_work"}


def test_per_ats_note_is_parsing_compatibility_not_ranking():
    job = SimpleNamespace(description="Python Django role", title="Backend Engineer",
                          ats_platform="greenhouse")
    rep = ats_readiness_service.build_report(GOOD_CV, job=job)
    assert rep["ats_note"]["ats_platform"] == "greenhouse"
    assert rep["ats_note"]["kind"] == "known_parsing_compatibility"
    assert rep["ats_note"]["guidance"] == ATS_PARSING_NOTES["greenhouse"]


def test_job_alignment_reports_keyword_coverage():
    job = SimpleNamespace(
        description="We need a Python Django backend engineer with PostgreSQL and Docker.",
        title="Backend Engineer", ats_platform="")
    rep = ats_readiness_service.build_report(GOOD_CV, job=job)
    ja = rep["job_alignment"]
    assert ja is not None
    assert ja["keyword_coverage_score"] >= 50
    assert ja["title_mentioned_in_cv"] is True


def test_empty_cv_needs_work():
    rep = ats_readiness_service.build_report("")
    assert rep["parsing_compatibility"]["band"] == "needs_work"


def test_unknown_ats_has_no_note():
    job = SimpleNamespace(description="x", title="Dev", ats_platform="obscure_ats")
    rep = ats_readiness_service.build_report(GOOD_CV, job=job)
    assert rep["ats_note"] is None


def test_no_job_means_no_alignment_block():
    rep = ats_readiness_service.build_report(GOOD_CV)
    assert rep["job_alignment"] is None
