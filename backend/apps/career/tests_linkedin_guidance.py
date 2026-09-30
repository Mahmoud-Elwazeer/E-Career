"""Tests for LinkedIn Profile Guidance (§31). Pure Python; no DB."""
from apps.career.linkedin_guidance_service import linkedin_guidance_service as S


def test_empty_profile_fails_and_needs_work():
    r = S.analyze()
    assert r["band"] == "needs_work"
    fields = {c["field"]: c["status"] for c in r["checks"]}
    assert fields["headline"] == "fail"
    assert fields["about"] == "fail"


def test_strong_profile_scores_well():
    r = S.analyze(
        headline="Senior Backend Engineer | Python, Django | Scaling APIs for millions",
        about=("Backend engineer with 8 years building high-scale services. " * 6),
        skills=["Python", "Django", "PostgreSQL", "AWS", "Kubernetes", "Redis"],
        experience_count=3, has_photo=True,
    )
    assert r["band"] in ("good", "excellent")
    assert r["completeness_score"] >= 70


def test_keyword_alignment_reports_missing():
    r = S.analyze(
        headline="Backend Engineer",
        about="I build services.",
        skills=["Python"],
        target_role="Senior Kubernetes Platform Engineer",
        target_keywords=["kubernetes", "terraform", "aws"],
    )
    ka = r["keyword_alignment"]
    assert ka is not None
    assert "kubernetes" in ka["missing_keywords"]
    assert "terraform" in ka["missing_keywords"]
    assert ka["coverage_percent"] < 100


def test_keyword_alignment_present_when_covered():
    r = S.analyze(
        headline="Kubernetes Platform Engineer",
        about="I work with terraform and aws every day.",
        skills=["Kubernetes", "Terraform", "AWS"],
        target_keywords=["kubernetes", "terraform", "aws"],
    )
    ka = r["keyword_alignment"]
    assert ka["coverage_percent"] == 100
    assert ka["missing_keywords"] == []


def test_no_target_means_no_keyword_section():
    r = S.analyze(headline="Engineer", about="x" * 250, skills=["a", "b", "c", "d", "e"])
    assert r["keyword_alignment"] is None


def test_every_fail_has_a_fix():
    r = S.analyze()
    for c in r["checks"]:
        if c["status"] in ("warn", "fail"):
            assert c.get("fix"), f"{c['field']} missing a fix"


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
