"""
Trend Detection Service using BERTopic.

Detects emerging skills, technologies, and job market trends
by analyzing job descriptions over time. Runs as a weekly
Celery task on the latest job postings.
"""
from __future__ import annotations

import structlog
from datetime import timedelta
from typing import Any

from django.utils import timezone

logger = structlog.get_logger()


class TrendDetectionService:
    """Detect emerging trends from job posting data using BERTopic."""

    def __init__(self):
        self._model = None

    def detect_skill_trends(self, days: int = 90) -> list[TrendResult]:
        """Detect trending skills from recent job descriptions."""
        documents, timestamps = self._get_job_descriptions(days)
        if len(documents) < 50:
            logger.info("trend_detection_skipped", reason="insufficient_data", count=len(documents))
            return []

        topics = self._run_topic_modeling(documents, timestamps)
        return self._extract_trends(topics)

    def get_emerging_skills(self, days: int = 30) -> list[dict[str, Any]]:
        """Get skills that are growing in frequency."""
        from apps.jobs.models import Job
        from django.db.models import Count

        now = timezone.now()
        recent_cutoff = now - timedelta(days=days)
        previous_cutoff = recent_cutoff - timedelta(days=days)

        recent_skills = (
            Job.objects.filter(status='active', created_at__gte=recent_cutoff)
            .values("tags__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:50]
        )

        previous_skills = (
            Job.objects.filter(
                status='active',
                created_at__gte=previous_cutoff,
                created_at__lt=recent_cutoff,
            )
            .values("tags__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:50]
        )

        previous_map = {s["tags__name"]: s["count"] for s in previous_skills if s["tags__name"]}
        emerging = []

        for skill in recent_skills:
            name = skill["tags__name"]
            if not name:
                continue
            recent_count = skill["count"]
            prev_count = previous_map.get(name, 0)

            if prev_count > 0:
                growth = ((recent_count - prev_count) / prev_count) * 100
            else:
                growth = 100.0 if recent_count > 0 else 0.0

            if growth > 20:
                emerging.append({
                    "skill": name,
                    "recent_count": recent_count,
                    "previous_count": prev_count,
                    "growth_pct": round(growth, 1),
                    "status": "emerging" if prev_count == 0 else "growing",
                })

        return sorted(emerging, key=lambda x: x["growth_pct"], reverse=True)[:20]

    def get_declining_skills(self, days: int = 30) -> list[dict[str, Any]]:
        """Get skills that are declining in frequency."""
        from apps.jobs.models import Job
        from django.db.models import Count

        now = timezone.now()
        recent_cutoff = now - timedelta(days=days)
        previous_cutoff = recent_cutoff - timedelta(days=days)

        recent_skills = (
            Job.objects.filter(status='active', created_at__gte=recent_cutoff)
            .values("tags__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:50]
        )
        recent_map = {s["tags__name"]: s["count"] for s in recent_skills if s["tags__name"]}

        previous_skills = (
            Job.objects.filter(
                status='active',
                created_at__gte=previous_cutoff,
                created_at__lt=recent_cutoff,
            )
            .values("tags__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:50]
        )

        declining = []
        for skill in previous_skills:
            name = skill["tags__name"]
            if not name:
                continue
            prev_count = skill["count"]
            recent_count = recent_map.get(name, 0)

            if prev_count > 5:
                decline = ((recent_count - prev_count) / prev_count) * 100
                if decline < -20:
                    declining.append({
                        "skill": name,
                        "recent_count": recent_count,
                        "previous_count": prev_count,
                        "decline_pct": round(abs(decline), 1),
                        "status": "declining",
                    })

        return sorted(declining, key=lambda x: x["decline_pct"], reverse=True)[:20]

    def _get_job_descriptions(self, days: int) -> tuple[list[str], list]:
        """Get job descriptions and their timestamps for topic modeling."""
        from apps.jobs.models import Job

        cutoff = timezone.now() - timedelta(days=days)
        jobs = Job.objects.filter(
            status='active',
            created_at__gte=cutoff,
            description__isnull=False,
        ).values_list("description", "created_at").order_by("created_at")

        documents = []
        timestamps = []
        for desc, created in jobs:
            if desc and len(desc) > 100:
                documents.append(desc[:3000])
                timestamps.append(created)

        return documents, timestamps

    def _run_topic_modeling(self, documents: list[str], timestamps: list) -> dict[str, Any]:
        """Run BERTopic on documents with timestamps."""
        try:
            from bertopic import BERTopic

            topic_model = BERTopic(
                language="multilingual",
                min_topic_size=10,
                nr_topics="auto",
                verbose=False,
            )

            topics, probs = topic_model.fit_transform(documents)
            topics_over_time = topic_model.topics_over_time(documents, timestamps)

            topic_info = topic_model.get_topic_info()
            return {
                "topics": topics,
                "topic_info": topic_info.to_dict() if hasattr(topic_info, 'to_dict') else {},
                "over_time": topics_over_time.to_dict() if hasattr(topics_over_time, 'to_dict') else {},
                "model": topic_model,
            }
        except ImportError:
            logger.warning("bertopic_not_installed")
            return {}
        except Exception as e:
            logger.error("bertopic_failed", error=str(e))
            return {}

    def _extract_trends(self, topics: dict[str, Any]) -> list[TrendResult]:
        """Extract trend results from BERTopic output."""
        if not topics or "model" not in topics:
            return []

        results = []
        model = topics["model"]
        topic_info = model.get_topic_info()

        for _, row in topic_info.iterrows():
            if row["Topic"] == -1:
                continue
            topic_words = model.get_topic(row["Topic"])
            if topic_words:
                results.append(TrendResult(
                    topic_id=row["Topic"],
                    keywords=[w for w, _ in topic_words[:5]],
                    document_count=row.get("Count", 0),
                    representative_words=[w for w, _ in topic_words[:10]],
                ))

        return results


class TrendResult:
    """A detected trend."""

    def __init__(
        self,
        topic_id: int,
        keywords: list[str],
        document_count: int,
        representative_words: list[str] = None,
        growth_rate: float = 0.0,
    ):
        self.topic_id = topic_id
        self.keywords = keywords
        self.document_count = document_count
        self.representative_words = representative_words or []
        self.growth_rate = growth_rate

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "keywords": self.keywords,
            "document_count": self.document_count,
            "representative_words": self.representative_words,
            "growth_rate": self.growth_rate,
        }


_service: TrendDetectionService | None = None


def get_trend_service() -> TrendDetectionService:
    global _service
    if _service is None:
        _service = TrendDetectionService()
    return _service
