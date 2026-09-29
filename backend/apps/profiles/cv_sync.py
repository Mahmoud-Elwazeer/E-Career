"""CV → Profile synchronization with conflict flagging (Phase B, §20).

The previous behaviour unconditionally overwrote profile fields (skills,
experience_years, current_role, education, certifications) with CV-parsed
values — silently clobbering anything the user had entered. The directive is
explicit: DO NOT overwrite user data silently; enrich empty fields and FLAG
contradictions for the user to resolve.

Rules per field:
  - profile field EMPTY  → fill from CV        (status: extracted)
  - profile == CV value  → confirm             (status: confirmed)
  - profile != CV value  → keep profile, FLAG  (status: conflict)

Returns a sync report the caller can persist / surface in the UI. Pure/
deterministic — no AI, so it works while Bedrock is blocked.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldSync:
    field: str
    status: str          # "extracted" | "confirmed" | "conflict" | "skipped"
    profile_value: Any = None
    cv_value: Any = None


@dataclass
class SyncReport:
    applied: list[str] = field(default_factory=list)      # fields filled from CV
    confirmed: list[str] = field(default_factory=list)    # already matched
    conflicts: list[FieldSync] = field(default_factory=list)  # need user decision
    details: list[FieldSync] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "applied": self.applied,
            "confirmed": self.confirmed,
            "conflicts": [
                {"field": c.field, "profile_value": c.profile_value, "cv_value": c.cv_value}
                for c in self.conflicts
            ],
            "has_conflicts": bool(self.conflicts),
        }


def _is_empty(v) -> bool:
    return v is None or v == "" or v == [] or v == {} or v == 0


def _extract_skills(parsed: dict) -> list[str]:
    s = parsed.get("skills") or {}
    if isinstance(s, list):
        return [str(x) for x in s if x]
    out: list[str] = []
    for key in ("technical", "soft_skills", "tools"):
        vals = s.get(key) if isinstance(s, dict) else None
        if vals:
            out.extend(str(x) for x in vals if x)
    return out


def _experience_years(parsed: dict) -> int | None:
    from datetime import datetime

    exp = parsed.get("experience") or parsed.get("work_experience") or []
    if not isinstance(exp, list) or not exp:
        return None
    total_months = 0
    found = False
    for e in exp:
        if not isinstance(e, dict):
            continue
        start_str = e.get("start_date")
        if not start_str:
            continue
        try:
            start = datetime.strptime(start_str, "%Y-%m")
            end_str = e.get("end_date")
            end = datetime.now() if (not end_str or end_str == "Present") else datetime.strptime(end_str, "%Y-%m")
            months = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += max(0, months)
            found = True
        except Exception:
            continue
    return (total_months // 12) if found else None


def sync_cv_to_profile(profile, parsed_data: dict, *, apply: bool = True) -> SyncReport:
    """Merge CV-parsed data into a profile without silent overwrite.

    If apply=True, empty profile fields are filled in-place (caller saves).
    Conflicts are never auto-applied — they are returned for user resolution.
    """
    report = SyncReport()
    if not parsed_data:
        return report

    def handle(field_name: str, cv_value, list_compare: bool = False):
        if _is_empty(cv_value):
            return
        current = getattr(profile, field_name, None)
        if _is_empty(current):
            if apply:
                setattr(profile, field_name, cv_value)
            report.applied.append(field_name)
            report.details.append(FieldSync(field_name, "extracted", current, cv_value))
        else:
            same = (
                set(map(str, current)) == set(map(str, cv_value))
                if (list_compare and isinstance(current, list) and isinstance(cv_value, list))
                else str(current).strip().lower() == str(cv_value).strip().lower()
            )
            if same:
                report.confirmed.append(field_name)
                report.details.append(FieldSync(field_name, "confirmed", current, cv_value))
            else:
                # Keep the user's value; flag the contradiction.
                report.conflicts.append(FieldSync(field_name, "conflict", current, cv_value))
                report.details.append(FieldSync(field_name, "conflict", current, cv_value))

    # Skills
    handle("skills", _extract_skills(parsed_data), list_compare=True)

    # Languages
    langs = (parsed_data.get("skills") or {}).get("languages") if isinstance(parsed_data.get("skills"), dict) else None
    if langs:
        handle("languages", langs, list_compare=True)

    # Experience years
    yrs = _experience_years(parsed_data)
    if yrs is not None:
        handle("experience_years", yrs)

    # Current role
    exp = parsed_data.get("experience") or []
    if isinstance(exp, list) and exp:
        current_exp = next((e for e in exp if isinstance(e, dict) and e.get("end_date") == "Present"), exp[0])
        if isinstance(current_exp, dict) and current_exp.get("title"):
            handle("current_role", current_exp.get("title"))

    # Education / certifications (fill-empty only; lists are hard to auto-merge)
    if parsed_data.get("education"):
        handle("education", parsed_data["education"], list_compare=True)
    if parsed_data.get("certifications"):
        handle("certifications", parsed_data["certifications"], list_compare=True)

    # Portfolio URL
    personal = parsed_data.get("personal") or {}
    if personal.get("portfolio"):
        handle("portfolio_url", personal["portfolio"])

    return report
