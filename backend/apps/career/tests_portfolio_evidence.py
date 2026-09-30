"""Tests for Portfolio Evidence Builder (§31). Pure Python; no DB/network."""
from apps.career.portfolio_evidence_service import portfolio_evidence_service as S


_PROJECTS = [
    {"name": "PayFlow", "url": "https://github.com/me/payflow",
     "description": "A payment processing service handling high throughput with idempotency.",
     "tech": ["Python", "Django", "PostgreSQL"], "highlights": ["Processed 1M tx/day"]},
    {"name": "Sketch", "description": "small toy", "tech": ["JavaScript"]},  # no link, weak
]


def test_backed_and_unbacked_skills():
    r = S.build(projects=_PROJECTS,
                target_skills=["Python", "Django", "Kubernetes"])
    assert "python" in r["skills_backed_by_evidence"]
    assert "django" in r["skills_backed_by_evidence"]
    assert "kubernetes" in r["skills_missing_evidence"]
    assert 0 < r["skill_evidence_coverage_percent"] < 100


def test_strong_vs_weak_project_strength():
    r = S.build(projects=_PROJECTS, target_skills=["Python"])
    by_name = {p["name"]: p for p in r["projects"]}
    assert by_name["PayFlow"]["strength"] >= 60      # link+desc+tech+highlights
    assert by_name["Sketch"]["strength"] < 60         # no link, thin
    assert by_name["PayFlow"]["has_verifiable_link"] is True
    assert by_name["Sketch"]["has_verifiable_link"] is False


def test_missing_skill_becomes_action():
    r = S.build(projects=_PROJECTS, target_skills=["Kubernetes"])
    details = " ".join(a["detail"].lower() for a in r["action_items"])
    assert "kubernetes" in details


def test_missing_link_becomes_action():
    r = S.build(projects=_PROJECTS, target_skills=["Python"])
    details = " ".join(a["detail"].lower() for a in r["action_items"])
    assert "sketch" in details and "link" in details


def test_link_checker_injected_offline():
    calls = {}
    def checker(url):
        calls[url] = True
        return "payflow" in url
    r = S.build(projects=_PROJECTS, target_skills=["Python"], link_checker=checker)
    by_name = {p["name"]: p for p in r["projects"]}
    assert by_name["PayFlow"]["link_live"] is True
    assert calls  # checker was actually invoked


def test_no_target_skills_coverage_zero_but_no_crash():
    r = S.build(projects=_PROJECTS)
    assert r["skill_evidence_coverage_percent"] == 0
    assert r["project_count"] == 2


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
