"""Tests for §6 source-aware assessment: SOURCE TRUST vs CONTENT QUALITY.

Pure-Python; runs under pytest or the standalone harness.
"""
from apps.scraper.pipeline.legitimacy import (
    calculate_source_trust, assess_job, calculate_legitimacy_score,
)


_GOOD_ATS_JOB = {
    "title": "Senior Backend Engineer",
    "company_name": "Airbnb",
    "description": "x" * 400,
    "ats_platform": "greenhouse",
    "ats_job_id": "12345",
    "direct_apply_url": "https://careers.airbnb.com/positions/12345",
    "canonical_job_url": "https://careers.airbnb.com/positions/12345",
}

_SCAM_JOB = {
    "title": "Work from home earn $5000 per week",
    "company_name": "X",
    "description": "wire transfer required. pay a registration fee to start. send money via moneygram.",
}


def test_structured_ats_has_high_source_trust():
    trust, evidence = calculate_source_trust(_GOOD_ATS_JOB)
    assert trust >= 0.8
    assert "known_ats_provider:greenhouse" in evidence
    assert "has_ats_job_id" in evidence


def test_unstructured_scam_has_low_source_trust():
    trust, evidence = calculate_source_trust(_SCAM_JOB)
    assert trust < 0.3
    assert "known_ats_provider" not in " ".join(evidence)


def test_assess_good_ats_job_publishable():
    a = assess_job(_GOOD_ATS_JOB)
    assert a["publishable"] is True
    assert a["is_structured_ats"] is True
    assert a["content_quality"] >= 0.4
    assert a["source_trust"] >= 0.8
    assert a["block_reasons"] == []


def test_assess_scam_job_blocked_despite_reporting_both_dims():
    a = assess_job(_SCAM_JOB)
    assert a["publishable"] is False
    assert a["content_quality"] < 0.4
    assert any("content_quality_below_threshold" in r for r in a["block_reasons"])


def test_trust_does_not_buy_publication():
    # A trusted provider wrapper around scam CONTENT must still be blocked:
    # trust and content are independent; content gates publication.
    trusted_scam = dict(_SCAM_JOB, ats_platform="greenhouse", ats_job_id="9")
    a = assess_job(trusted_scam)
    assert a["source_trust"] >= 0.7          # high trust
    assert a["publishable"] is False         # still blocked on content
    assert a["content_quality"] < 0.4


def test_short_ats_description_not_penalized_but_scam_still_is():
    short_ats = {
        "title": "Engineer", "company_name": "Stripe", "description": "Apply now.",
        "ats_platform": "greenhouse", "ats_job_id": "7",
        "direct_apply_url": "https://stripe.com/jobs/7",
    }
    a = assess_job(short_ats)
    # structured ATS exemption keeps a short list-endpoint description publishable
    assert a["is_structured_ats"] is True
    assert a["publishable"] is True


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
