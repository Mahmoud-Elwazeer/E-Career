"""Tests for the GitHub Profile README Builder (§31).

Verifies deterministic Markdown output, no fabricated sections, and safe
rendering from a profile-like object. Pure Python; no DB.
"""
from apps.career.github_readme_builder import github_readme_builder as B


def test_minimal_readme_has_header_only_facts():
    md = B.build(name="Jane Dev")
    assert md.startswith("# Hi, I'm Jane Dev")
    # no sections fabricated when data absent
    assert "## Skills" not in md
    assert "## Featured Projects" not in md
    assert "GitHub Stats" not in md


def test_skills_render_as_badges():
    md = B.build(name="Jane", skills=["Python", "Django", "AWS"])
    assert "🛠️ Skills & Technologies" in md
    assert "img.shields.io/badge/Python" in md
    assert "img.shields.io/badge/Django" in md


def test_projects_only_render_when_present():
    md = B.build(name="Jane", top_projects=[
        {"name": "CoolApp", "url": "https://github.com/jane/coolapp", "description": "A cool app"},
        {"name": "NoUrl", "description": "no link project"},
    ])
    assert "🚀 Featured Projects" in md
    assert "[CoolApp](https://github.com/jane/coolapp)" in md
    assert "**NoUrl**" in md  # renders without a broken link


def test_github_stats_only_with_username():
    with_user = B.build(name="Jane", github_username="janedev")
    without = B.build(name="Jane")
    assert "github-readme-stats" in with_user
    assert "janedev" in with_user
    assert "github-readme-stats" not in without


def test_connect_links_rendered():
    md = B.build(name="Jane", linkedin_url="https://linkedin.com/in/jane",
                 email="jane@example.com", github_username="janedev")
    assert "[LinkedIn](https://linkedin.com/in/jane)" in md
    assert "mailto:jane@example.com" in md


def test_build_from_profile_is_safe_on_sparse_object():
    class P:
        full_name = "Sparse User"
        skills = ["Go"]
    md = B.build_from_profile(P())
    assert "Sparse User" in md
    assert "img.shields.io/badge/Go" in md


def test_deterministic_output():
    a = B.build(name="Jane", skills=["Python"], github_username="j")
    b = B.build(name="Jane", skills=["Python"], github_username="j")
    assert a == b


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
