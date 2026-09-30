"""GitHub Profile README Builder (Professional Presence §31).

Generates a professional GitHub profile README (Markdown) from a candidate's
profile/CV data. Deterministic + template-based — no AI dependency (works while
Bedrock is blocked), and no copied third-party code.

OSS licensing (researched 2026-09-29, documented in the master doc):
- readme.so (MIT) and rahuldkjain/github-profile-readme-generator (Apache-2.0)
  are permissively licensed and could be adopted with attribution, but this
  implementation is written from scratch (our own templates) so there is no
  embedding/attribution obligation.
- ProfileMe is AGPLv3 → NOT embedded or copied here.

The builder emits standard, widely-supported Markdown (headings, badges via
img.shields.io, lists). It NEVER fabricates facts: sections are only rendered
when the corresponding profile data exists.
"""
from __future__ import annotations

from typing import Iterable, Optional


def _badge(label: str, color: str = "0A66C2") -> str:
    """A shields.io static badge for a skill/tech. Label is URL-encoded."""
    safe = (label.replace(" ", "%20").replace("-", "--").replace("_", "__"))
    return f"![{label}](https://img.shields.io/badge/{safe}-{color}?style=flat-square)"


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body}\n"


class GitHubReadmeBuilder:
    """Builds a GitHub profile README from structured profile data."""

    def build(
        self,
        *,
        name: str,
        headline: str = "",
        about: str = "",
        skills: Optional[Iterable[str]] = None,
        github_username: str = "",
        linkedin_url: str = "",
        website: str = "",
        email: str = "",
        currently_learning: str = "",
        top_projects: Optional[list[dict]] = None,
    ) -> str:
        skills = [s for s in (skills or []) if s]
        top_projects = top_projects or []

        parts: list[str] = []

        # Header
        header = f"# Hi, I'm {name} 👋"
        if headline:
            header += f"\n\n### {headline}"
        parts.append(header + "\n")

        # About
        if about:
            parts.append(_section("About Me", about.strip()))

        # Skills as badges (only if provided)
        if skills:
            badges = " ".join(_badge(s) for s in skills[:24])
            parts.append(_section("🛠️ Skills & Technologies", badges))

        # Currently learning
        if currently_learning:
            parts.append(_section("🌱 Currently Learning", currently_learning.strip()))

        # Featured projects (only rendered facts)
        if top_projects:
            lines = []
            for p in top_projects[:6]:
                title = p.get("name") or p.get("title") or "Project"
                url = p.get("url", "")
                desc = p.get("description", "")
                if url:
                    lines.append(f"- **[{title}]({url})** — {desc}".rstrip(" —"))
                else:
                    lines.append(f"- **{title}** — {desc}".rstrip(" —"))
            parts.append(_section("🚀 Featured Projects", "\n".join(lines)))

        # GitHub stats (only if username known; uses the widely-used public
        # stats image service — an external widget, not embedded code).
        if github_username:
            stats = (
                f"![{name}'s GitHub stats]"
                f"(https://github-readme-stats.vercel.app/api?username={github_username}"
                f"&show_icons=true&hide_border=true)"
            )
            parts.append(_section("📊 GitHub Stats", stats))

        # Connect
        links = []
        if linkedin_url:
            links.append(f"[LinkedIn]({linkedin_url})")
        if website:
            links.append(f"[Website]({website})")
        if github_username:
            links.append(f"[GitHub](https://github.com/{github_username})")
        if email:
            links.append(f"[Email](mailto:{email})")
        if links:
            parts.append(_section("📫 Connect", " · ".join(links)))

        return "\n".join(parts).strip() + "\n"

    def build_from_profile(self, profile) -> str:
        """Convenience: pull common fields off a profile-like object safely."""
        g = lambda attr, default="": getattr(profile, attr, default) or default
        skills = getattr(profile, "skills", None) or []
        return self.build(
            name=g("full_name") or g("name") or "Your Name",
            headline=g("headline") or g("title"),
            about=g("about") or g("bio") or g("summary"),
            skills=skills,
            github_username=g("github_username") or g("github_org"),
            linkedin_url=g("linkedin_url"),
            website=g("website") or g("portfolio_url"),
            email=g("public_email"),
            currently_learning=g("currently_learning"),
        )


github_readme_builder = GitHubReadmeBuilder()
