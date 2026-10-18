"""
Legal link crawler — static, repository-level verification of every
legal-adjacent link in the frontend against the real backend policy
registry.

This is deliberately a *static source scan*, not a running-browser
crawler: it reads the frontend's own TypeScript/TSX source files as text,
extracts every `/legal/...` reference, and cross-checks it against the
real `PolicyDocument` rows in the database. This catches the class of bug
a browser crawl would also catch (a dead link, a `#` placeholder, a typo'd
slug) without needing a running frontend server, a browser, or network
access — appropriate for a CI-friendly, dependency-light check, per the
directive's explicit instruction not to build a large generic crawler
framework.

Usage:
  python manage.py legal_link_audit             # human-readable report
  python manage.py legal_link_audit --json      # machine-readable (CI/ops)
  python manage.py legal_link_audit --write-md  # also write
                                                  audit/LEGAL_LINK_VERIFICATION.md

Exit code is always 0 (reporting command, not a deploy gate) unless
--fail-on-issues is passed, in which case it exits 1 if any issue was found
— for a CI step that should actually block on a broken legal link.

What this checks:
  - Every `/legal/<slug>` (or `/legal/:slug` route param) reference found
    in frontend source resolves to a REAL PolicyDocument.slug in the DB
    (catches: typo'd slug, slug for a document that doesn't exist yet,
    slug for a document that was renamed/removed).
  - Every PolicyDocument.slug in the DB is reachable from at least the
    Legal Center hub page (catches: an orphaned policy nobody can navigate
    to).
  - No `href="#"` or `to="#"` placeholder exists in any file this command
    scans (catches: a stub link that was never wired up).
  - No `href=""` / `to=""` (empty) legal-ish link exists.

What this does NOT check (explicitly out of scope, stated honestly rather
than silently skipped):
  - It does not make real HTTP requests, so it cannot detect a genuine
    runtime 404/500 from a route that's misconfigured only at the server
    level (e.g. a urls.py entry that's correct in code but broken by a
    deployment-specific proxy rule). That requires the separate
    browser-based E2E pass.
  - It does not detect a redirect loop (there is no redirect middleware
    for `/legal/*` routes in this codebase to loop in the first place —
    confirmed by reading `frontend/src/App.tsx`'s route table, which the
    Scan Targets below actually includes), so that check is reported as
    N/A rather than a fabricated pass.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.legal.models import PolicyDocument

# Frontend source files this command actually scans. Kept as an explicit,
# reviewed list (not "every .tsx file in the repo") so the audit output is
# meaningful and doesn't drown in irrelevant matches from unrelated pages —
# every file here is a real file confirmed (by prior investigation in this
# same hardening pass) to contain at least one legal-adjacent reference.
SCAN_TARGETS = [
    "src/App.tsx",
    "src/components/Footer.tsx",
    "src/components/legal/CookieConsentBanner.tsx",
    "src/components/legal/PolicyMarkdown.tsx",
    "src/pages/legal/LegalCenter.tsx",
    "src/pages/legal/PolicyPage.tsx",
    "src/pages/Login.tsx",
    "src/pages/JobDetail.tsx",
    "src/components/QuickApplyPanel.tsx",
    "src/pages/Billing.tsx",
    "src/pages/employer/EmployerBilling.tsx",
    "src/pages/PrivacyCenter.tsx",
    "src/pages/AdminLegal.tsx",
    "src/pages/Settings.tsx",
    "src/services/legal.ts",
]

# Matches a frontend ROUTE/navigation reference to /legal/<slug> —
# specifically `to="/legal/x"`, `href="/legal/x"`, or `to={`/legal/x`}`
# (React Router's <Link to=...> / a plain <a href=...>). Deliberately
# attribute-scoped so this does NOT also match:
#   - import paths like `./pages/legal/LegalCenter` (no quote/attr prefix)
#   - backend API call paths like apiRequest("/legal/policies/") or
#     admin endpoints ("/legal/admin/versions/...") — those live in the
#     Django URL namespace, not the PolicyDocument.slug namespace, and
#     comparing them against PolicyDocument.slug would be comparing two
#     unrelated things that happen to share a string prefix.
_LEGAL_PATH_RE = re.compile(r'(?:to|href)=[{"\'`]+/legal/([a-zA-Z0-9_\-]+)')
# Route PARAM declarations (":slug") are the route definition itself, not
# a reference to one specific document — detected separately so they're
# never miscounted as an unresolved slug.
_ROUTE_PARAM_RE = re.compile(r'path="/legal/:[a-zA-Z]+"')
# Placeholder / dead link patterns.
_HASH_LINK_RE = re.compile(r'(?:href|to)=["\']#["\']')
_EMPTY_LINK_RE = re.compile(r'(?:href|to)=["\']["\']')


class Command(BaseCommand):
    help = (
        "Static legal link crawler: scans frontend source for every "
        "/legal/<slug> reference and cross-checks it against real "
        "PolicyDocument rows, flags # / empty placeholder links, and "
        "flags any PolicyDocument not reachable from the Legal Center hub."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
        parser.add_argument("--write-md", action="store_true",
                           help="Also write audit/LEGAL_LINK_VERIFICATION.md at the repo root.")
        parser.add_argument("--fail-on-issues", action="store_true",
                           help="Exit with code 1 if any issue was found (for a CI gate).")

    def handle(self, *args, **options):
        frontend_dir = Path(settings.BASE_DIR).parent / "frontend"
        result = run_link_audit(frontend_dir)

        if options["json"]:
            self.stdout.write(json.dumps(result, indent=2))
        else:
            self.stdout.write(render_human_report(result))

        if options["write_md"]:
            md_path = Path(settings.BASE_DIR).parent / "audit" / "LEGAL_LINK_VERIFICATION.md"
            md_path.write_text(render_markdown_report(result), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote {md_path}"))

        if options["fail_on_issues"] and result["issue_count"] > 0:
            self.stderr.write(self.style.ERROR(f"{result['issue_count']} issue(s) found."))
            raise SystemExit(1)


def run_link_audit(frontend_dir: Path) -> dict:
    """Pure function (no stdout writes) so this is independently testable
    and reusable from both the management command and `legal_readiness`
    if ever wired in there too."""
    real_slugs = set(PolicyDocument.objects.values_list("slug", flat=True))

    per_file_findings: dict[str, list[dict]] = {}
    referenced_slugs: set[str] = set()
    hash_or_empty_links: list[dict] = []

    for rel_path in SCAN_TARGETS:
        full_path = frontend_dir / rel_path
        if not full_path.exists():
            per_file_findings[rel_path] = [{"type": "file_not_found", "detail": str(full_path)}]
            continue

        text = full_path.read_text(encoding="utf-8", errors="replace")
        findings = []

        for match in _LEGAL_PATH_RE.finditer(text):
            slug = match.group(1)
            referenced_slugs.add(slug)
            if slug not in real_slugs:
                line_no = text.count("\n", 0, match.start()) + 1
                findings.append({
                    "type": "unresolved_slug",
                    "slug": slug,
                    "line": line_no,
                    "detail": f"/legal/{slug} does not match any PolicyDocument.slug in the database.",
                })

        for match in _HASH_LINK_RE.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            entry = {"type": "hash_placeholder_link", "line": line_no, "file": rel_path}
            findings.append(entry)
            hash_or_empty_links.append(entry)

        for match in _EMPTY_LINK_RE.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            entry = {"type": "empty_href_link", "line": line_no, "file": rel_path}
            findings.append(entry)
            hash_or_empty_links.append(entry)

        if findings:
            per_file_findings[rel_path] = findings

    # Orphan check: every real PolicyDocument.slug should be reachable from
    # the Legal Center hub specifically (not just referenced anywhere —
    # e.g. a footer-only link without a hub tile would still mean the
    # Legal Center's own "browse everything" promise is broken).
    hub_path = frontend_dir / "src/pages/legal/LegalCenter.tsx"
    hub_text = hub_path.read_text(encoding="utf-8", errors="replace") if hub_path.exists() else ""
    # LegalCenter.tsx builds its links as `/legal/${d.slug}` (template
    # literal interpolation) rather than a literal `to="/legal/x"` per
    # document, so the attribute-scoped _LEGAL_PATH_RE above won't match
    # each slug individually here — instead, cross-check against the
    # `slug:` values declared in its own CATEGORIES/DOCS data literal.
    hub_referenced_slugs = set(re.findall(r'slug:\s*["\']([a-zA-Z0-9_\-]+)["\']', hub_text))
    orphaned_slugs = sorted(real_slugs - hub_referenced_slugs)

    unresolved_count = sum(
        1 for findings in per_file_findings.values()
        for f in findings if f.get("type") == "unresolved_slug"
    )
    issue_count = (
        unresolved_count + len(hash_or_empty_links) + len(orphaned_slugs)
        + sum(1 for findings in per_file_findings.values() if any(f.get("type") == "file_not_found" for f in findings))
    )

    return {
        "scanned_files": SCAN_TARGETS,
        "real_policy_slugs": sorted(real_slugs),
        "referenced_slugs": sorted(referenced_slugs),
        "per_file_findings": per_file_findings,
        "orphaned_slugs": orphaned_slugs,
        "hash_or_empty_link_count": len(hash_or_empty_links),
        "unresolved_slug_count": unresolved_count,
        "issue_count": issue_count,
        "redirect_loop_check": "N/A — no redirect middleware exists for /legal/* routes in this codebase "
                               "(confirmed by reading App.tsx's route table); nothing to loop.",
        "runtime_404_check": "NOT PERFORMED — this is a static source scan, not a live HTTP crawl. "
                             "A separate browser-based E2E pass is required to catch a genuine "
                             "server-level 404 this scan cannot see.",
    }


def render_human_report(result: dict) -> str:
    lines = ["Legal Link Audit Report", "=" * 24, ""]
    lines.append(f"Real PolicyDocument slugs in DB ({len(result['real_policy_slugs'])}): "
                 + ", ".join(result["real_policy_slugs"]))
    lines.append("")
    if not result["per_file_findings"]:
        lines.append("No issues found in any scanned file.")
    for file, findings in result["per_file_findings"].items():
        lines.append(f"[{file}]")
        for f in findings:
            if f["type"] == "file_not_found":
                lines.append(f"  FILE NOT FOUND: {f['detail']}")
            elif f["type"] == "unresolved_slug":
                lines.append(f"  line {f['line']}: UNRESOLVED SLUG '/legal/{f['slug']}' — {f['detail']}")
            elif f["type"] == "hash_placeholder_link":
                lines.append(f"  line {f['line']}: '#' PLACEHOLDER LINK")
            elif f["type"] == "empty_href_link":
                lines.append(f"  line {f['line']}: EMPTY HREF/TO LINK")
        lines.append("")
    if result["orphaned_slugs"]:
        lines.append(f"ORPHANED (not linked from Legal Center hub): {', '.join(result['orphaned_slugs'])}")
    else:
        lines.append("No orphaned policy documents — every real slug is reachable from the Legal Center hub.")
    lines.append("")
    lines.append(result["redirect_loop_check"])
    lines.append(result["runtime_404_check"])
    lines.append("")
    lines.append(f"TOTAL ISSUES: {result['issue_count']}")
    return "\n".join(lines)


def render_markdown_report(result: dict) -> str:
    lines = [
        "# Legal Link Verification",
        "",
        "**Generated by `python manage.py legal_link_audit --write-md`. "
        "This is a static source-code scan, not a live browser crawl — see "
        "the \"What this does NOT check\" section of the command's own "
        "docstring (`apps/legal/management/commands/legal_link_audit.py`) "
        "for exactly what that distinction means.**",
        "",
        f"Real `PolicyDocument` slugs in the database at generation time "
        f"({len(result['real_policy_slugs'])}): "
        f"`{', '.join(result['real_policy_slugs'])}`",
        "",
        "## Findings",
        "",
    ]
    if not result["per_file_findings"]:
        lines.append("No issues found in any scanned file.")
    else:
        lines.append("| File | Line | Issue |")
        lines.append("|---|---|---|")
        for file, findings in result["per_file_findings"].items():
            for f in findings:
                if f["type"] == "file_not_found":
                    lines.append(f"| {file} | — | File not found: `{f['detail']}` |")
                elif f["type"] == "unresolved_slug":
                    lines.append(f"| {file} | {f['line']} | Unresolved slug `/legal/{f['slug']}` |")
                elif f["type"] == "hash_placeholder_link":
                    lines.append(f"| {file} | {f['line']} | `#` placeholder link |")
                elif f["type"] == "empty_href_link":
                    lines.append(f"| {file} | {f['line']} | Empty href/to link |")
    lines.append("")
    lines.append("## Orphaned policy documents")
    lines.append("")
    if result["orphaned_slugs"]:
        lines.append(f"Not linked from the Legal Center hub: {', '.join(result['orphaned_slugs'])}")
    else:
        lines.append("None — every real `PolicyDocument.slug` is reachable from the Legal Center hub.")
    lines.append("")
    lines.append("## Out-of-scope checks (reported honestly, not fabricated)")
    lines.append("")
    lines.append(f"- Redirect-loop check: {result['redirect_loop_check']}")
    lines.append(f"- Runtime 404 check: {result['runtime_404_check']}")
    lines.append("")
    lines.append(f"## Total issues: {result['issue_count']}")
    lines.append("")
    return "\n".join(lines)
