"""Tests for the SmartRecruiters connector (§11) using a REAL Bosch payload.

Captured live 2026-09-29 from the public Posting API. Verifies the apply URL is
the candidate-facing careers page, NOT the API `ref` (a prior latent bug).
"""
import json
import os

from apps.scraper.ats import smartrecruiters as sr

_FIXTURE = os.path.join(os.path.dirname(__file__), "tests_fixtures_smartrecruiters.json")


class _Resp:
    def __init__(self, payload):
        self._payload = payload
    def raise_for_status(self):
        pass
    def json(self):
        return self._payload


class _FakeRequests:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
    def get(self, url, **kw):
        self.calls += 1
        if self.calls == 1:
            return _Resp(self.payload)
        return _Resp({"totalFound": self.payload.get("totalFound"), "content": []})
    class RequestException(Exception):
        pass


def _install():
    with open(_FIXTURE, encoding="utf-8") as fh:
        payload = json.load(fh)
    sr.requests = _FakeRequests(payload)
    return payload


def test_parses_bosch_postings():
    payload = _install()
    jobs = sr.fetch_smartrecruiters_jobs("BoschGroup")
    assert len(jobs) == len(payload["content"])
    assert jobs[0]["ats_platform"] == "smartrecruiters"
    assert jobs[0]["title"]
    assert jobs[0]["ats_job_id"]


def test_apply_url_is_careers_page_not_api_ref():
    _install()
    jobs = sr.fetch_smartrecruiters_jobs("BoschGroup")
    for j in jobs:
        url = j["direct_apply_url"].lower()
        assert "api.smartrecruiters.com" not in url, "must not use API ref as apply url"
        assert "jobs.smartrecruiters.com/boschgroup/" in url


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
