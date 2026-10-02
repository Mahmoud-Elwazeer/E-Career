"""Tests for the Recruitee connector using a trimmed REAL payload shape.

Fixture mirrors a real company board (veocareers.recruitee.com) captured live
2026-10-02 (full response: 57 real jobs; fixture trims to 2 representative
offers - one onsite, one remote-with-salary).
"""
import json
import os

from apps.scraper.ats import recruitee as rc

_FIXTURE = os.path.join(os.path.dirname(__file__), "tests_fixtures_recruitee.json")


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

    def get(self, url, **kw):
        return _Resp(self.payload)

    class RequestException(Exception):
        pass


def _install():
    with open(_FIXTURE, encoding="utf-8") as fh:
        payload = json.load(fh)
    rc.requests = _FakeRequests(payload)
    return payload


def test_parses_real_shaped_offers():
    payload = _install()
    jobs = rc.fetch_recruitee_jobs("veocareers")
    assert len(jobs) == len(payload["offers"])
    assert jobs[0]["ats_platform"] == "recruitee"
    assert jobs[0]["title"] == "Transport Team Leader"
    assert jobs[0]["ats_job_id"] == "2765452"


def test_apply_url_is_careers_url_not_apply_form():
    _install()
    jobs = rc.fetch_recruitee_jobs("veocareers")
    for j in jobs:
        url = j["direct_apply_url"]
        assert url.startswith("https://veocareers.recruitee.com/o/")
        assert "/c/new" not in url, "must use the job listing page, not the apply-form URL"


def test_remote_flag_maps_to_remote_type():
    _install()
    jobs = rc.fetch_recruitee_jobs("veocareers")
    remote_job = next(j for j in jobs if j["ats_job_id"] == "2765453")
    onsite_job = next(j for j in jobs if j["ats_job_id"] == "2765452")
    assert remote_job["remote_type"] == "remote"
    assert onsite_job["remote_type"] == "onsite"


def test_salary_extracted_when_present():
    _install()
    jobs = rc.fetch_recruitee_jobs("veocareers")
    remote_job = next(j for j in jobs if j["ats_job_id"] == "2765453")
    assert remote_job["salary_min"] == 45000
    assert remote_job["salary_max"] == 60000
    assert remote_job["salary_currency"] == "EUR"


def test_missing_salary_handled_gracefully():
    _install()
    jobs = rc.fetch_recruitee_jobs("veocareers")
    onsite_job = next(j for j in jobs if j["ats_job_id"] == "2765452")
    assert onsite_job["salary_min"] is None
    assert onsite_job["salary_max"] is None


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
