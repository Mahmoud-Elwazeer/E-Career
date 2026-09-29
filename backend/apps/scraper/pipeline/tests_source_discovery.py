"""Tests for ATS Source Discovery + migration verdict (§8/§9/§10).

Offline: the network fetcher is a stub returning canned (status, payload) per
URL, replaying the real Notion Lever->Ashby migration discovered on 2026-09-29.
"""
from apps.scraper.pipeline.source_discovery import (
    discover_ats, compare_for_migration, ATS_ENDPOINTS,
)


def make_fetcher(responses):
    """responses: dict url -> (status, payload)."""
    def _f(url):
        return responses.get(url, (404, {"ok": False}))
    return _f


def test_discovers_greenhouse_first_healthy():
    url = ATS_ENDPOINTS["greenhouse"].format(slug="stripe")
    f = make_fetcher({url: (200, {"jobs": [{"id": 1}, {"id": 2}]})})
    r = discover_ats("stripe", fetcher=f)
    assert r.healthy is True
    assert r.provider == "greenhouse"
    assert r.job_count == 2
    assert r.endpoint == url


def test_empty_board_not_healthy():
    url = ATS_ENDPOINTS["greenhouse"].format(slug="ghostco")
    f = make_fetcher({url: (200, {"jobs": []})})
    r = discover_ats("ghostco", fetcher=f)
    assert r.healthy is False
    assert r.provider is None
    # evidence still records the 200/empty probe
    assert any(e.get("status") == 200 for e in r.evidence)


def test_notion_lever_migrated_to_ashby():
    lever_url = ATS_ENDPOINTS["lever"].format(slug="notion")
    ashby_url = ATS_ENDPOINTS["ashby"].format(slug="notion")
    f = make_fetcher({
        lever_url: (404, {"ok": False, "error": "Document not found"}),
        ashby_url: (200, {"jobs": [{"id": i} for i in range(128)]}),
    })
    r = discover_ats("notion", fetcher=f)
    assert r.provider == "ashby"
    assert r.job_count == 128
    verdict = compare_for_migration("lever", r)
    assert verdict["verdict"] == "MIGRATED"
    assert verdict["reason"] == "lever -> ashby"
    assert verdict["new_provider"] == "ashby"


def test_same_provider_still_healthy_is_not_migration():
    gh = ATS_ENDPOINTS["greenhouse"].format(slug="airbnb")
    f = make_fetcher({gh: (200, {"jobs": [{"id": 1}] * 156})})
    r = discover_ats("airbnb", fetcher=f)
    verdict = compare_for_migration("greenhouse", r)
    assert verdict["verdict"] == "ACTIVE"


def test_no_provider_anywhere_is_invalid():
    # Everything 404s (e.g. Netflix — no public ATS json).
    f = make_fetcher({})
    r = discover_ats("netflix", fetcher=f)
    assert r.healthy is False
    verdict = compare_for_migration("lever", r)
    assert verdict["verdict"] == "INVALID"
    # evidence records a probe for every known provider
    assert len(r.evidence) == len(ATS_ENDPOINTS)


def test_candidates_restrict_probes():
    ashby_url = ATS_ENDPOINTS["ashby"].format(slug="plaid")
    f = make_fetcher({ashby_url: (200, {"jobs": [{"id": 1}] * 121})})
    r = discover_ats("plaid", fetcher=f, candidates=["ashby"])
    assert r.provider == "ashby"
    assert len(r.evidence) == 1  # only probed ashby


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
