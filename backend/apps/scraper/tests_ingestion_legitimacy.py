"""Regression tests for the ingestion legitimacy gate + run metrics.

Guards the real bug behind "Greenhouse fetched 154 / created 0": structured-ATS
jobs (company in company_slug, short list-endpoint description) must NOT be
rejected by the legitimacy gate, while real scams still are. Pure/offline.
"""
from apps.scraper.pipeline.legitimacy import calculate_legitimacy_score
from apps.scraper.pipeline.run_metrics import RunMetrics, LOW_LEGITIMACY


def _greenhouse_job():
    return {
        "title": "Senior Backend Engineer",
        "company_slug": "airbnb",           # employer lives in company_slug
        "description": "Short listing blurb.",  # <100 chars, from list endpoint
        "direct_apply_url": "https://boards.greenhouse.io/airbnb/jobs/123",
        "ats_platform": "greenhouse",
        "ats_job_id": "123",
    }


def test_greenhouse_job_not_rejected_by_legitimacy():
    score, flags = calculate_legitimacy_score(_greenhouse_job())
    assert score >= 0.4, (score, flags)
    assert "Missing or invalid company name" not in flags
    assert "Description too short" not in flags  # structured ATS exempt


def test_company_read_from_company_slug():
    job = {"title": "Dev", "company_slug": "acme", "description": "x" * 200}
    _, flags = calculate_legitimacy_score(job)
    assert "Missing or invalid company name" not in flags


def test_scam_still_rejected():
    scam = {
        "title": "Earn $5000 per week work from home",
        "company_slug": "",
        "description": "Send processing fee via western union.",
    }
    score, _ = calculate_legitimacy_score(scam)
    assert score < 0.4


def test_non_ats_short_description_still_penalized():
    plain = {"title": "Engineer", "company_slug": "acme", "description": "short"}
    _, flags = calculate_legitimacy_score(plain)
    assert "Description too short" in flags  # source trust != content quality


def test_run_metrics_zero_yield_anomaly():
    m = RunMetrics(source="airbnb-greenhouse", fetched=154)
    for _ in range(154):
        m.reject(LOW_LEGITIMACY, "x")
    d = m.to_dict()
    assert d["fetched"] == 154 and d["created"] == 0
    assert d["rejected"]["LOW_LEGITIMACY"] == 154
    assert m.is_zero_yield_anomaly is True


def test_run_metrics_healthy_run_not_anomaly():
    m = RunMetrics(source="x", fetched=10)
    m.created = 8
    assert m.is_zero_yield_anomaly is False
