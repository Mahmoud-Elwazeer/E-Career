"""Tests for Phase A normalization + layered dedup upgrades. Pure/offline."""
from apps.scraper.pipeline.normalizer import (
    normalize_seniority,
    normalize_country_city,
)
from apps.scraper.pipeline.deduplicator import (
    normalize_title_for_dedup,
    content_fingerprint,
    dedup_verdict,
)


# ── seniority ────────────────────────────────────────────────────────────────
def test_seniority_from_raw_level_high_confidence():
    s, c = normalize_seniority("Software Engineer", raw_level="senior")
    assert s == "senior"
    assert c >= 0.9


def test_seniority_inferred_from_title():
    s, c = normalize_seniority("Lead Backend Engineer")
    assert s == "senior"
    assert 0 < c < 0.9


def test_seniority_executive():
    s, _ = normalize_seniority("Chief Technology Officer")
    assert s == "executive"


def test_seniority_unknown():
    s, c = normalize_seniority("Backend Engineer")
    assert s is None and c == 0.0


# ── location ─────────────────────────────────────────────────────────────────
def test_country_city_known_country():
    country, city, conf = normalize_country_city("Cairo, Egypt")
    assert country == "Egypt"
    assert city == "Cairo"
    assert conf >= 0.8


def test_country_city_unknown_country_assumes_last():
    country, city, conf = normalize_country_city("Springfield, Freedonia")
    assert city == "Springfield"
    assert country == "Freedonia"
    assert conf == 0.5


def test_country_city_empty():
    assert normalize_country_city("") == ("", "", 0.0)


# ── dedup ────────────────────────────────────────────────────────────────────
def test_title_normalization_strips_noise():
    a = normalize_title_for_dedup("Senior Backend Engineer (Remote)")
    b = normalize_title_for_dedup("Backend Engineer")
    assert a == b == "backend engineer"


def test_content_fingerprint_stable_and_matches_across_seniority():
    j1 = {"company": "Acme", "title": "Senior Backend Engineer", "location": "Cairo"}
    j2 = {"company": "acme", "title": "Backend Engineer", "location": "cairo"}
    assert content_fingerprint(j1) == content_fingerprint(j2)


def test_dedup_verdict_l1_from_ats_id():
    v = dedup_verdict({"ats_platform": "Greenhouse", "ats_job_id": "123",
                       "company": "Acme", "title": "Dev", "location": "Cairo"})
    assert v["l1_canonical_key"] == "greenhouse:123"
    assert v["l2_normalized_key"] == "acme|dev|cairo"
    assert len(v["l3_content_hash"]) == 64


def test_dedup_verdict_l1_falls_back_to_url():
    v = dedup_verdict({"direct_apply_url": "https://Boards.Greenhouse.io/acme/jobs/9",
                       "company": "Acme", "title": "Dev", "location": "Cairo"})
    assert v["l1_canonical_key"] == "https://boards.greenhouse.io/acme/jobs/9"
