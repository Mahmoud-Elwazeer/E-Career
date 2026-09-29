"""Recommendation feedback capture + signal aggregation (§17).

Thin, deterministic helpers to record behavioral signals and expose them to the
recommendation ranker. No AI. Idempotent per (user, job, signal): repeat signals
bump count + timestamp instead of duplicating.
"""
from __future__ import annotations

import structlog

logger = structlog.get_logger()


def record_feedback(user_id: int, job_id, signal: str, reason: str = "") -> bool:
    """Record a single behavioral signal. Returns True on success."""
    from apps.users.models import RecommendationFeedback

    valid = {s for s, _ in RecommendationFeedback.SIGNAL_CHOICES}
    if signal not in valid:
        logger.warning("recfeedback_invalid_signal", signal=signal)
        return False
    try:
        obj, created = RecommendationFeedback.objects.get_or_create(
            user_id=user_id, job_id=job_id, signal=signal,
            defaults={"reason": reason},
        )
        if not created:
            from django.db.models import F
            RecommendationFeedback.objects.filter(pk=obj.pk).update(
                count=F("count") + 1
            )
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("recfeedback_record_failed", error=str(exc))
        return False


def user_job_signal_weight(user_id: int, job_id) -> float:
    """Aggregate signed feedback weight for a (user, job) — a ranking signal.

    Positive = interest (view/save/apply/interview); negative = disinterest
    (dismiss/not_interested). Used to boost/suppress items in re-ranking.
    """
    from apps.users.models import RecommendationFeedback

    total = 0.0
    for fb in RecommendationFeedback.objects.filter(user_id=user_id, job_id=job_id):
        total += fb.weight * min(fb.count, 3)  # cap repeat influence
    return round(total, 3)


def suppressed_job_ids(user_id: int) -> set:
    """Job ids the user explicitly dismissed / marked not interested."""
    from apps.users.models import RecommendationFeedback

    return set(
        RecommendationFeedback.objects.filter(
            user_id=user_id, signal__in=["dismiss", "not_interested"]
        ).values_list("job_id", flat=True)
    )
