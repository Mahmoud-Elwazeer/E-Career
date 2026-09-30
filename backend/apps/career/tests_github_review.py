"""Tests for GitHub Profile Review (§31). Offline via injected fetcher."""
from datetime import datetime, timezone, timedelta
from apps.career.github_review_service import github_review_service as S


NOW = datetime(2026, 9, 29, tzinfo=timezone.utc)


def _recent(days): return (NOW - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def make_fetcher(repos, ok=True):
    def _f(username):
        if not ok:
            raise RuntimeError("api down")
        return {"profile": {"login": username}, "repos": repos}
    return _f


STRONG_REPOS = [
    {"name": "payflow", "fork": False, "language": "Python",
     "description": "Payment service", "pushed_at": _recent(10), "stargazers_count": 42, "has_readme": True},
    {"name": "infra", "fork": False, "language": "Go",
     "description": "IaC modules", "pushed_at": _recent(40), "stargazers_count": 5, "has_readme": True},
    {"name": "forked-thing", "fork": True, "language": "JavaScript", "pushed_at": _recent(5)},
]


def test_strong_profile_scores_well():
    r = S.review("jane", fetcher=make_fetcher(STRONG_REPOS), now=NOW)
    assert r["ok"] is True
    assert r["stats"]["original_repos"] == 2   # fork excluded
    assert r["band"] in ("good", "excellent")


def test_language_coverage_evidence_based():
    r = S.review("jane", fetcher=make_fetcher(STRONG_REPOS),
                 target_languages=["Python", "Go", "Rust"], now=NOW)
    lc = r["language_coverage"]
    assert "python" in lc["present"] and "go" in lc["present"]
    assert "rust" in lc["missing"]   # no repo uses Rust -> not fabricated
    assert lc["coverage_percent"] < 100


def test_no_original_repos_fails():
    only_forks = [{"name": "f", "fork": True, "language": "Python", "pushed_at": _recent(1)}]
    r = S.review("jane", fetcher=make_fetcher(only_forks), now=NOW)
    fields = {c["field"]: c["status"] for c in r["checks"]}
    assert fields["original_work"] == "fail"


def test_stale_activity_warns():
    stale = [{"name": "old", "fork": False, "language": "Python",
              "description": "x", "pushed_at": _recent(500), "has_readme": True}]
    r = S.review("jane", fetcher=make_fetcher(stale), now=NOW)
    fields = {c["field"]: c["status"] for c in r["checks"]}
    assert fields["activity"] == "warn"


def test_fetch_failure_handled():
    r = S.review("jane", fetcher=make_fetcher([], ok=False), now=NOW)
    assert r["ok"] is False
    assert "api down" in r["error"]


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
