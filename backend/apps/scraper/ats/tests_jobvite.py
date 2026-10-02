"""Tests for the Jobvite connector's DISCOVERY_UNSUPPORTED stub.

Jobvite's official API requires per-employer credentials (confirmed via
Jobvite's own Help Center docs - header-based auth, no public/anonymous
mode) and its only unauthenticated surface is an unversioned, server-
rendered HTML careers page - not a reliable, moat-safe source to scrape.
These tests lock in the honest "unsupported, not guessing" behavior rather
than asserting any real extraction (there is none to test yet).
"""
from apps.scraper.ats import jobvite as jv


def test_unsupported_by_default():
    assert jv.SUPPORTED is False


def test_fetch_returns_empty_for_unknown_tenant():
    jobs = jv.fetch_jobvite_jobs("some-random-company")
    assert jobs == []


def test_empty_tenant_registry_by_default():
    assert jv.JOBVITE_TENANTS == {}


def test_platform_name_is_jobvite():
    scraper = jv.JobviteScraper("acme")
    assert scraper.get_platform_name() == "jobvite"


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
