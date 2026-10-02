"""Tests for the CORRECTED BambooHR connector using trimmed REAL payload shapes.

Fixtures mirror a real company board (cubecare.bamboohr.com) captured live
2026-10-03 (full list: 14 real open roles). The PREVIOUS connector targeted
a dead endpoint ({company}.bamboohr.com/jobs/list/, confirmed live 404) with
a wrong JSON shape - this is a real bug fix, not just a new connector.
"""
import json
import os

from apps.scraper.ats import bamboohr as bh

_LIST_FIXTURE = os.path.join(os.path.dirname(__file__), "tests_fixtures_bamboohr_list.json")
_DETAIL_FIXTURE = os.path.join(os.path.dirname(__file__), "tests_fixtures_bamboohr_detail.json")


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeRequests:
    """Routes /careers/list to the list fixture and /careers/{id}/detail to
    the detail fixture, by inspecting the requested URL - mirrors the real
    two-call shape (list + per-job detail)."""

    def __init__(self, list_payload, detail_payload):
        self.list_payload = list_payload
        self.detail_payload = detail_payload

    def get(self, url, **kw):
        if "/detail" in url:
            return _Resp(self.detail_payload)
        return _Resp(self.list_payload)

    class RequestException(Exception):
        pass


def _install():
    with open(_LIST_FIXTURE, encoding="utf-8") as fh:
        list_payload = json.load(fh)
    with open(_DETAIL_FIXTURE, encoding="utf-8") as fh:
        detail_payload = json.load(fh)
    bh.requests = _FakeRequests(list_payload, detail_payload)
    return list_payload, detail_payload


def test_parses_real_shaped_list_and_skips_missing_id():
    list_payload, _ = _install()
    jobs = bh.fetch_bamboohr_jobs("cubecare")
    # fixture has 3 entries, 1 has no id and must be skipped.
    assert len(list_payload["result"]) == 3
    assert len(jobs) == 2
    assert jobs[0]["ats_platform"] == "bamboohr"
    assert jobs[0]["title"] == "Full Remote - Estimating Coordinator"
    assert jobs[0]["ats_job_id"] == "439"


def test_apply_url_is_employer_subdomain_share_url():
    _install()
    jobs = bh.fetch_bamboohr_jobs("cubecare")
    for j in jobs:
        assert j["direct_apply_url"].startswith("https://cubecare.bamboohr.com/careers/")


def test_detail_fetch_enriches_description_and_canonical_url():
    _install()
    jobs = bh.fetch_bamboohr_jobs("cubecare")
    first = jobs[0]
    assert "Cube Care" in first["description"]
    assert first["direct_apply_url"] == "https://cubecare.bamboohr.com/careers/439"
    assert first["scraped_at"] == "2026-09-02"


def test_remote_location_detected():
    _install()
    jobs = bh.fetch_bamboohr_jobs("cubecare")
    remote_job = next(j for j in jobs if j["ats_job_id"] == "439")
    assert remote_job["remote_type"] == "remote"


def test_onsite_location_detected():
    _install()
    jobs = bh.fetch_bamboohr_jobs("cubecare")
    onsite_job = next(j for j in jobs if j["ats_job_id"] == "451")
    assert onsite_job["remote_type"] == "onsite"
    assert onsite_job["location"] == "Opa Locka"


def test_detail_fetch_failure_degrades_gracefully():
    """If the detail call fails, the job must still be returned with a
    deterministic fallback apply_url - not dropped."""
    list_payload, _ = _install()

    class _FailingDetailRequests(_FakeRequests):
        def get(self, url, **kw):
            if "/detail" in url:
                raise self.RequestException("boom")
            return _Resp(self.list_payload)

    bh.requests = _FailingDetailRequests(list_payload, {})
    jobs = bh.fetch_bamboohr_jobs("cubecare")
    assert len(jobs) == 2
    assert jobs[0]["direct_apply_url"] == "https://cubecare.bamboohr.com/careers/439"
    assert jobs[0]["description"] == ""


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
