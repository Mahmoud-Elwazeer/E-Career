"""Tests for the additive job field-provenance builder (Section 14).

Provenance records per-field lineage (value/source/method/confidence) without
destroying the raw payload. These tests are pure/offline.
"""
from apps.scraper.pipeline.normalizer import build_provenance


def test_builds_provenance_for_present_fields():
    job = {
        "title": "Senior Engineer",
        "location": "Cairo",
        "ats_platform": "greenhouse",
        "ats_job_id": "12345",
        "direct_apply_url": "https://boards.greenhouse.io/acme/jobs/12345",
    }
    prov = build_provenance(job, source="greenhouse", method="ats_api", confidence=1.0)
    assert prov["title"]["value"] == "Senior Engineer"
    assert prov["title"]["source"] == "greenhouse"
    assert prov["title"]["method"] == "ats_api"
    assert prov["title"]["confidence"] == 1.0
    assert "ats_job_id" in prov
    assert "direct_apply_url" in prov


def test_skips_missing_and_empty_fields():
    job = {"title": "Dev", "location": "", "salary_min": None}
    prov = build_provenance(job, source="lever")
    assert "title" in prov
    assert "location" not in prov  # empty string skipped
    assert "salary_min" not in prov  # None skipped


def test_confidence_is_rounded_and_bounded():
    job = {"title": "X"}
    prov = build_provenance(job, source="ai", method="ai_extraction", confidence=0.87654)
    assert prov["title"]["method"] == "ai_extraction"
    assert prov["title"]["confidence"] == 0.877


def test_empty_job_yields_empty_provenance():
    assert build_provenance({}, source="s") == {}
