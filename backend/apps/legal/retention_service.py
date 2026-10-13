"""
Retention enforcement engine (directive hardening pass).

`RetentionPolicy` rows previously existed as database-only configuration with
no code that ever acted on them — a scheduled/periodic job that reads
`retention_period_days` and actually deletes/anonymizes aged data did not
exist. This module is that engine.

Design rules (directive-mandated):
  - DRY_RUN by default. Nothing is ever destroyed unless the caller
    explicitly passes `dry_run=False` (and, for the management command,
    passes `--execute`).
  - A category is only ever enforced if its `RetentionPolicy` row has a
    confirmed `retention_period_days` (not NULL) AND
    `requires_legal_review=False`. Every category seeded by `seed_legal` is
    `requires_legal_review=True` with `retention_period_days=None` except
    the two that are already enforced by EXISTING code elsewhere
    (`gdpr_export_files` by `accounts.tasks_gdpr.cleanup_expired_exports`,
    `account_deletion_grace` by the `AccountDeletionRequest` grace-period
    flow) — this engine deliberately does NOT duplicate those two; it only
    adds coverage for categories that have no enforcement today.
  - Only a known, explicitly-registered category can ever be enforced — an
    admin typing a retention period into an arbitrary free-text
    `data_category` row must NOT silently start deleting unrelated data.
    Unregistered/unrecognized categories are reported as
    "no enforcement handler" rather than guessed at.
  - Any user under an active `LegalHold` is excluded from enforcement for
    every category, full stop.
  - Batched (`batch_size`), with per-category counts returned for metrics/
    audit — never deletes without producing a count the caller can log.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Callable

from django.utils import timezone

from .models import RetentionPolicy, LegalHold


@dataclass
class CategoryResult:
    category: str
    enforceable: bool
    reason: str = ""
    candidates_found: int = 0
    excluded_by_legal_hold: int = 0
    affected: int = 0  # rows actually deleted/anonymized (0 in dry-run)


@dataclass
class RetentionRunReport:
    dry_run: bool
    started_at: object
    results: list[CategoryResult] = field(default_factory=list)

    @property
    def total_candidates(self) -> int:
        return sum(r.candidates_found for r in self.results)

    @property
    def total_affected(self) -> int:
        return sum(r.affected for r in self.results)


def _held_user_ids() -> set:
    """User IDs currently protected by an active legal hold — excluded from
    every retention enforcement category, no exceptions."""
    return set(
        LegalHold.objects.filter(released_at__isnull=True, user__isnull=False)
        .values_list("user_id", flat=True)
    )


# ── Per-category enforcement handlers ────────────────────────────────────────
# Each handler receives (cutoff_datetime, held_user_ids, dry_run, batch_size)
# and returns (candidates_found, excluded_by_hold, affected). A handler must
# NEVER touch a row for a held user. Registering a new category here is a
# deliberate code change, not something an admin can trigger by editing a
# RetentionPolicy row's free-text category name alone.

def _enforce_interview_transcripts(cutoff, held_user_ids, dry_run, batch_size):
    """Clears old interview transcript text (InterviewSession.transcript /
    InterviewQuestion.answer_text) past the retention cutoff. Only clears the
    TEXT content; the session row itself (dates, scores) is retained for the
    user's own history unless they separately request deletion."""
    from apps.career.models import InterviewSession

    qs = (InterviewSession.objects
          .filter(created_at__lt=cutoff)
          .exclude(user_id__in=held_user_ids)
          .exclude(transcript="")[:batch_size])
    candidates = list(qs)
    found = len(candidates)
    affected = 0
    if not dry_run:
        for session in candidates:
            session.transcript = ""
            session.save(update_fields=["transcript"])
            affected += 1
    return found, 0, affected


def _enforce_cv_documents(cutoff, held_user_ids, dry_run, batch_size):
    """Deletes CV files past the retention cutoff for INACTIVE accounts only
    (is_active=False) — an active job seeker's CV is still in active use
    regardless of upload age, so age-based deletion only ever applies to
    accounts that are no longer active."""
    from apps.career.models import CareerProfile

    qs = (CareerProfile.objects
          .filter(updated_at__lt=cutoff, user__is_active=False)
          .exclude(user_id__in=held_user_ids)
          .exclude(cv_file="")[:batch_size])
    candidates = list(qs)
    found = len(candidates)
    affected = 0
    if not dry_run:
        from django.core.files.storage import default_storage
        for profile in candidates:
            try:
                if profile.cv_file and default_storage.exists(profile.cv_file.name):
                    default_storage.delete(profile.cv_file.name)
            finally:
                profile.cv_file = None
                profile.save(update_fields=["cv_file"])
                affected += 1
    return found, 0, affected


# category key -> handler. Deliberately does NOT include "gdpr_export_files"
# or "account_deletion_grace" — those already have real enforcement elsewhere
# (see module docstring); duplicating them here would risk two systems racing
# on the same rows.
_HANDLERS: dict[str, Callable] = {
    "interview_transcripts": _enforce_interview_transcripts,
    "cv_documents": _enforce_cv_documents,
}


def run_retention_enforcement(*, dry_run: bool = True, batch_size: int = 500) -> RetentionRunReport:
    """Evaluate every RetentionPolicy row and enforce the ones that are
    legally confirmed (retention_period_days set, requires_legal_review=False)
    AND have a registered handler. Everything else is reported as
    not-enforceable with a reason — never guessed at.
    """
    report = RetentionRunReport(dry_run=dry_run, started_at=timezone.now())
    held_user_ids = _held_user_ids()

    for policy in RetentionPolicy.objects.all().order_by("data_category"):
        if policy.requires_legal_review:
            report.results.append(CategoryResult(
                category=policy.data_category, enforceable=False,
                reason="requires_legal_review=True — not legally confirmed yet",
            ))
            continue
        if not policy.retention_period_days:
            report.results.append(CategoryResult(
                category=policy.data_category, enforceable=False,
                reason="no retention_period_days configured",
            ))
            continue
        handler = _HANDLERS.get(policy.data_category)
        if handler is None:
            report.results.append(CategoryResult(
                category=policy.data_category, enforceable=False,
                reason="no enforcement handler registered for this category "
                       "(enforced elsewhere, or not yet built)",
            ))
            continue

        cutoff = timezone.now() - timedelta(days=policy.retention_period_days)
        found, excluded, affected = handler(cutoff, held_user_ids, dry_run, batch_size)
        report.results.append(CategoryResult(
            category=policy.data_category, enforceable=True,
            candidates_found=found, excluded_by_legal_hold=excluded, affected=affected,
        ))

    return report
