"""Tests for the `evaluate_repo` management command.

Evaluated against OssiumOfficial/Repolyze's input/output shape (GitHub URL
in, structured health/decision row out) without installing Repolyze itself
(REFERENCE_ONLY — see command docstring). All GitHub API calls are mocked;
no network access or real GITHUB_TOKEN required to run these.
"""
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.management.commands.evaluate_repo import parse_owner_repo


class TestParseOwnerRepo:
    def test_bare_slug(self):
        assert parse_owner_repo("thruwire/foreman") == ("thruwire", "foreman")

    def test_full_https_url(self):
        assert parse_owner_repo("https://github.com/thruwire/foreman") == (
            "thruwire",
            "foreman",
        )

    def test_url_with_trailing_slash_and_git_suffix(self):
        assert parse_owner_repo("https://github.com/hydra-db/open-glean.git/") == (
            "hydra-db",
            "open-glean",
        )

    def test_non_github_url_rejected(self):
        with pytest.raises(CommandError):
            parse_owner_repo("https://gitlab.com/owner/repo")

    def test_malformed_slug_rejected(self):
        with pytest.raises(CommandError):
            parse_owner_repo("not-a-valid-anything")


ANALYZE_RESULT = {
    "name": "LeulAria/Aria-Icons",
    "description": "Icon catalog CLI/MCP server",
    "stars": 74,
    "forks": 5,
    "open_issues": 2,
    "languages": ["TypeScript"],
    "language_breakdown": {"TypeScript": 50000, "JavaScript": 1000},
    "is_private": False,
    "is_fork": False,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2026-10-05T00:00:00Z",
    "quality_score": 0.55,
}

REPO_DETAILS = {
    "license": {"spdx_id": "MIT", "name": "MIT License"},
}


@patch("apps.core.management.commands.evaluate_repo.GitHubService.get_repo_details")
@patch("apps.core.management.commands.evaluate_repo.GitHubService.analyze_repository")
class TestEvaluateRepoCommand:
    def test_prints_markdown_table_row(self, mock_analyze, mock_details):
        mock_analyze.return_value = ANALYZE_RESULT
        mock_details.return_value = REPO_DETAILS

        out = StringIO()
        call_command("evaluate_repo", "LeulAria/Aria-Icons", stdout=out)
        output = out.getvalue()

        assert "| Repo | License | Stars |" in output
        assert "LeulAria/Aria-Icons" in output
        assert "MIT" in output
        assert "74" in output
        assert "TypeScript" in output

    def test_json_output_is_well_formed(self, mock_analyze, mock_details):
        import json

        mock_analyze.return_value = ANALYZE_RESULT
        mock_details.return_value = REPO_DETAILS

        out = StringIO()
        call_command("evaluate_repo", "LeulAria/Aria-Icons", "--json", stdout=out)
        data = json.loads(out.getvalue())

        assert data["name"] == "LeulAria/Aria-Icons"
        assert data["license"] == "MIT"
        assert data["stars"] == 74
        assert data["primary_language"] == "TypeScript"
        assert data["decision"] is None

    def test_records_decision_and_reason(self, mock_analyze, mock_details):
        import json

        mock_analyze.return_value = ANALYZE_RESULT
        mock_details.return_value = REPO_DETAILS

        out = StringIO()
        call_command(
            "evaluate_repo",
            "LeulAria/Aria-Icons",
            "--json",
            "--decision",
            "ADAPT",
            "--reason",
            "Dev-time icon discovery only, no runtime dependency.",
            stdout=out,
        )
        data = json.loads(out.getvalue())

        assert data["decision"] == "ADAPT"
        assert "Dev-time icon discovery" in data["reason"]

    def test_decision_without_reason_is_rejected(self, mock_analyze, mock_details):
        mock_analyze.return_value = ANALYZE_RESULT
        mock_details.return_value = REPO_DETAILS

        with pytest.raises(CommandError):
            call_command(
                "evaluate_repo",
                "LeulAria/Aria-Icons",
                "--decision",
                "ADAPT",
                stdout=StringIO(),
            )

    def test_license_lookup_failure_falls_back_to_unknown(self, mock_analyze, mock_details):
        mock_analyze.return_value = ANALYZE_RESULT
        mock_details.side_effect = Exception("rate limited")

        out = StringIO()
        call_command("evaluate_repo", "LeulAria/Aria-Icons", "--json", stdout=out)
        import json

        data = json.loads(out.getvalue())
        assert data["license"] == "UNKNOWN"

    def test_analyze_repository_failure_raises_command_error(self, mock_analyze, mock_details):
        mock_analyze.side_effect = Exception("404 Not Found")

        with pytest.raises(CommandError):
            call_command("evaluate_repo", "owner/does-not-exist", stdout=StringIO())
