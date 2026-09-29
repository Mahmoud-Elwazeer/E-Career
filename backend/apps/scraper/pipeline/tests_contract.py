"""Tests for the normalized job contract (§5) and ingestion states (§7).

Pure-Python (no Django DB) so they run under pytest OR the standalone importlib
harness used for this repo when pytest collection hangs.
"""
from apps.scraper.pipeline.contract import (
    NormalizedJob, IngestionState, _humanize_slug,
)


class _FakeSource:
    def __init__(self, id, name, slug, type="scraper"):
        self.id = id
        self.name = name
        self.slug = slug
        self.type = type


def test_greenhouse_shape_maps_to_contract():
    # Shape emitted by base.normalize_job for a greenhouse job.
    d = {
        "title": "Senior Backend Engineer",
        "company_slug": "airbnb",
        "direct_apply_url": "https://careers.airbnb.com/positions/123",
        "description": "x" * 400,
        "location": "San Francisco, CA",
        "ats_platform": "greenhouse",
        "ats_job_id": "123",
        "raw_data": {"id": 123},
        "salary_currency": "USD",
    }
    src = _FakeSource("s1", "Airbnb", "airbnb-greenhouse")
    nj = NormalizedJob.from_connector_dict(d, source=src)
    assert nj.title == "Senior Backend Engineer"
    assert nj.direct_apply_url.endswith("/positions/123")
    assert nj.ats_provider == "greenhouse"
    assert nj.ats_job_id == "123"
    # company_slug present on the dict wins as slug; name resolves to explicit
    # source name (real employer), never the raw board slug.
    assert nj.company_name == "Airbnb"
    assert nj.is_valid


def test_apply_url_key_variants_both_honored():
    # icims/teamtailor style: only apply_url present.
    d = {"title": "SRE", "apply_url": "https://careers-acme.icims.com/jobs/9",
         "company_name": "Acme", "ats_platform": "icims", "id": "9"}
    nj = NormalizedJob.from_connector_dict(d)
    assert nj.direct_apply_url.endswith("/jobs/9")
    assert nj.canonical_job_url.endswith("/jobs/9")


def test_company_name_falls_back_to_humanized_slug():
    # No explicit name and no source: must NOT surface a raw slug as the name.
    d = {"title": "Data Analyst", "company_slug": "modern-health-lever",
         "direct_apply_url": "https://jobs.lever.co/modern-health/1", "id": "1"}
    nj = NormalizedJob.from_connector_dict(d)
    assert nj.company_name == "Modern Health"
    assert nj.company_slug == "modern-health-lever"


def test_validate_flags_missing_required():
    nj = NormalizedJob.from_connector_dict({"description": "no title/url/company"})
    problems = nj.validate()
    assert "missing_title" in problems
    assert "missing_direct_apply_url" in problems
    assert "missing_company_name" in problems
    assert not nj.is_valid


def test_humanize_slug_strips_ats_suffix():
    assert _humanize_slug("airbnb-greenhouse") == "Airbnb"
    assert _humanize_slug("modern_health") == "Modern Health"
    assert _humanize_slug("spotify-lever") == "Spotify"


def test_ingestion_state_to_quality_state_mapping():
    assert IngestionState.TO_QUALITY_STATE[IngestionState.VERIFIED] == "direct_verified"
    assert IngestionState.TO_QUALITY_STATE[IngestionState.PUBLISHED] == "active"
    assert IngestionState.DUPLICATE in IngestionState.TERMINAL_FAILURES


def test_seniority_reads_experience_level_alias():
    d = {"title": "X", "apply_url": "https://x.co/1", "company_name": "X",
         "experience_level": "senior", "id": "1"}
    nj = NormalizedJob.from_connector_dict(d)
    assert nj.seniority == "senior"


if __name__ == "__main__":
    # Standalone harness (pytest collection intermittently hangs in this repo).
    import sys, types
    fns = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
