"""
OSS Repository Evaluation Command

Evaluated OssiumOfficial/Repolyze (formerly MxCorpIn/Repolyze; MIT license,
210 stars) during the Master Implementation Directive engagement. Repolyze
itself is a full, separately-hosted Next.js app requiring a GITHUB_TOKEN and
an OPENROUTER_API_KEY of its own — installing/running it would be exactly
the kind of disconnected second system this platform's AGENTS.md warns
against (see "avoid re-fragmenting into disconnected per-feature modules").
REFERENCE_ONLY for the software.

What's adapted here is its input/output *shape*: a GitHub repo URL in,
a structured health/decision row out. This formalizes a pattern that this
engagement's own audit docs (`audit/PLATFORM_ENGINE_ENRICHMENT_MASTER.md`
and others) have hand-typed as markdown tables at least 4 times with no
shared generator — e.g.:

    | Library | Repo | License (verified) | Latest version | Decision |

This command produces the same shape from a live GitHub API lookup instead
of a human re-typing it, using the GitHub API wrapper this app already has
(`apps.core.github_service.GitHubService`) rather than introducing a new
HTTP client.

Usage:
    python manage.py evaluate_repo https://github.com/<owner>/<repo>
    python manage.py evaluate_repo <owner>/<repo>
    python manage.py evaluate_repo <owner>/<repo> --json
    python manage.py evaluate_repo <owner>/<repo> --decision ADAPT --reason "..."
"""
import json
import re
from typing import Optional
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError

from apps.core.github_service import GitHubService

VALID_DECISIONS = (
    "KEEP_EXISTING",
    "ADAPT",
    "INTEGRATE",
    "REFERENCE_ONLY",
    "ISOLATE",
    "EXPERIMENT",
    "DEFER",
    "REJECT",
)


def parse_owner_repo(value: str) -> tuple[str, str]:
    """Accepts a bare `owner/repo` slug or a full GitHub URL."""
    value = value.strip()
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        if "github.com" not in parsed.netloc:
            raise CommandError(f"Not a github.com URL: {value}")
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            raise CommandError(f"Could not extract owner/repo from URL: {value}")
        owner, repo = parts[0], parts[1]
    else:
        match = re.match(r"^([^/\s]+)/([^/\s]+)$", value)
        if not match:
            raise CommandError(
                f"Expected 'owner/repo' or a github.com URL, got: {value!r}"
            )
        owner, repo = match.group(1), match.group(2)

    repo = repo.removesuffix(".git")
    return owner, repo


class Command(BaseCommand):
    help = (
        "Evaluate a GitHub repository against this platform's OSS-adoption "
        "rubric (license / activity / decision) and emit a structured row, "
        "replacing the hand-typed audit-doc tables with a repeatable check."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "repo",
            help="GitHub repo as 'owner/repo' or a full https://github.com/... URL",
        )
        parser.add_argument(
            "--token",
            default=None,
            help="GitHub token for higher API rate limits (optional for public repos).",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            dest="as_json",
            help="Emit machine-readable JSON instead of a markdown table row.",
        )
        parser.add_argument(
            "--decision",
            choices=VALID_DECISIONS,
            default=None,
            help="Record a human decision alongside the fetched metadata.",
        )
        parser.add_argument(
            "--reason",
            default=None,
            help="Free-text justification for --decision (required if --decision is set).",
        )

    def handle(self, *args, **options):
        owner, repo = parse_owner_repo(options["repo"])
        decision: Optional[str] = options.get("decision")
        reason: Optional[str] = options.get("reason")

        if decision and not reason:
            raise CommandError("--reason is required when --decision is provided.")

        service = GitHubService(access_token=options.get("token"))

        try:
            analysis = service.analyze_repository(owner, repo)
        except Exception as exc:  # network/4xx/5xx from the GitHub API
            raise CommandError(
                f"Failed to fetch {owner}/{repo} from the GitHub API: {exc}"
            ) from exc

        license_info = self._get_license(service, owner, repo)

        row = {
            "name": analysis.get("name") or f"{owner}/{repo}",
            "url": f"https://github.com/{owner}/{repo}",
            "license": license_info,
            "stars": analysis.get("stars", 0),
            "forks": analysis.get("forks", 0),
            "open_issues": analysis.get("open_issues", 0),
            "primary_language": self._primary_language(analysis.get("language_breakdown", {})),
            "last_updated": analysis.get("updated_at"),
            "is_fork": analysis.get("is_fork", False),
            "quality_score": analysis.get("quality_score"),
            "decision": decision,
            "reason": reason,
        }

        if options["as_json"]:
            self.stdout.write(json.dumps(row, indent=2))
            return

        self._print_table_row(row)

    def _get_license(self, service: GitHubService, owner: str, repo: str) -> str:
        try:
            details = service.get_repo_details(owner, repo)
        except Exception:
            return "UNKNOWN"
        license_obj = details.get("license") or {}
        return license_obj.get("spdx_id") or license_obj.get("name") or "NONE"

    def _primary_language(self, language_breakdown: dict) -> str:
        if not language_breakdown:
            return "unknown"
        return max(language_breakdown, key=language_breakdown.get)

    def _print_table_row(self, row: dict):
        header = "| Repo | License | Stars | Open Issues | Language | Last Updated | Decision | Reason |"
        separator = "|---|---|---|---|---|---|---|---|"
        decision = row["decision"] or "(unset)"
        reason = row["reason"] or "(use --decision/--reason to record one)"
        line = (
            f"| [{row['name']}]({row['url']}) | {row['license']} | {row['stars']} | "
            f"{row['open_issues']} | {row['primary_language']} | {row['last_updated']} | "
            f"{decision} | {reason} |"
        )
        self.stdout.write(header)
        self.stdout.write(separator)
        self.stdout.write(line)
        if row["quality_score"] is not None:
            self.stdout.write("")
            self.stdout.write(
                self.style.NOTICE(
                    f"(informational quality_score heuristic: {row['quality_score']} — "
                    f"not a substitute for the decision rubric in AGENTS.md)"
                )
            )
