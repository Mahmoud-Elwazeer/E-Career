"""
Event consumers for processing emitted events.

This module contains consumers that process events from the event log:
- AnalyticsAggregator: Aggregates events for analytics dashboards
- AuditTrailWriter: Writes events to audit trail for compliance
"""
from __future__ import annotations

import structlog
from datetime import datetime, timedelta
from typing import Any

from django.db.models import Count, Avg, Sum
from django.utils import timezone

logger = structlog.get_logger()


class AnalyticsAggregator:
    """
    Aggregate events for analytics dashboards.
    
    Processes events and creates aggregated metrics for:
    - Daily active users
    - Job engagement metrics
    - Search analytics
    - CV parsing success rates
    - AI usage patterns
    """
    
    def __init__(self):
        self._processed_events: set[str] = set()
    
    def aggregate_daily_metrics(self, date: datetime | None = None) -> dict[str, Any]:
        """
        Aggregate daily metrics from events.
        
        Args:
            date: Date to aggregate (defaults to yesterday)
            
        Returns:
            Dictionary of aggregated metrics
        """
        if date is None:
            date = timezone.now().date() - timedelta(days=1)
        
        start = timezone.make_aware(
            datetime.combine(date, datetime.min.time())
        )
        end = start + timedelta(days=1)
        
        from apps.events.models import EventLog
        
        events = EventLog.objects.filter(
            created_at__gte=start,
            created_at__lt=end
        )
        
        metrics = {
            "date": str(date),
            "generated_at": timezone.now().isoformat(),
            "total_events": events.count(),
            "by_category": {},
            "by_event_type": {},
            "by_user": {},
        }
        
        # Aggregate by category
        category_counts = events.values("category").annotate(
            count=Count("id")
        )
        metrics["by_category"] = {
            item["category"]: item["count"] for item in category_counts
        }
        
        # Aggregate by event type
        type_counts = events.values("event_type").annotate(
            count=Count("id")
        )
        metrics["by_event_type"] = {
            item["event_type"]: item["count"] for item in type_counts
        }
        
        # Aggregate by user (top 100)
        user_counts = events.filter(user__isnull=False).values(
            "user_id"
        ).annotate(
            count=Count("id")
        ).order_by("-count")[:100]
        metrics["by_user"] = {
            str(item["user_id"]): item["count"] for item in user_counts
        }
        
        # Specific metrics
        metrics["daily_active_users"] = events.filter(
            user__isnull=False
        ).values("user_id").distinct().count()
        
        metrics["job_views"] = events.filter(
            event_type="job_viewed"
        ).count()
        
        metrics["job_saves"] = events.filter(
            event_type="job_saved"
        ).count()
        
        metrics["job_applied"] = events.filter(
            event_type="job_applied"
        ).count()
        
        metrics["searches"] = events.filter(
            event_type="search_performed"
        ).count()
        
        metrics["cv_uploads"] = events.filter(
            event_type="cv_uploaded"
        ).count()
        
        metrics["cv_parsed"] = events.filter(
            event_type="cv_parsed"
        ).count()
        
        metrics["ai_calls"] = events.filter(
            event_type="ai_model_called"
        ).count()
        
        # Cost tracking
        ai_events = events.filter(event_type="ai_model_called")
        if ai_events.exists():
            total_cost = sum(
                e.data.get("cost_usd", 0) for e in ai_events
            )
            metrics["ai_total_cost_usd"] = round(total_cost, 4)
        
        logger.info(
            "daily_analytics_aggregated",
            date=str(date),
            total_events=metrics["total_events"],
            dau=metrics["daily_active_users"],
        )
        
        return metrics
    
    def aggregate_user_metrics(self, user_id: int, days: int = 30) -> dict[str, Any]:
        """
        Aggregate metrics for a specific user.
        
        Args:
            user_id: User ID to aggregate
            days: Number of days to look back
            
        Returns:
            Dictionary of user metrics
        """
        from apps.events.models import EventLog
        
        cutoff = timezone.now() - timedelta(days=days)
        
        events = EventLog.objects.filter(
            user_id=user_id,
            created_at__gte=cutoff
        )
        
        metrics = {
            "user_id": user_id,
            "period_days": days,
            "generated_at": timezone.now().isoformat(),
            "total_events": events.count(),
            "by_category": {},
            "by_event_type": {},
        }
        
        # Aggregate by category
        category_counts = events.values("category").annotate(
            count=Count("id")
        )
        metrics["by_category"] = {
            item["category"]: item["count"] for item in category_counts
        }
        
        # Aggregate by event type
        type_counts = events.values("event_type").annotate(
            count=Count("id")
        )
        metrics["by_event_type"] = {
            item["event_type"]: item["count"] for item in type_counts
        }
        
        # Last activity
        last_event = events.order_by("-created_at").first()
        if last_event:
            metrics["last_activity"] = last_event.created_at.isoformat()
        
        return metrics


class AuditTrailWriter:
    """
    Write events to audit trail for compliance.
    
    Ensures all significant events are logged for:
    - Security auditing
    - Regulatory compliance
    - User activity tracking
    - Data provenance
    """
    
    def __init__(self):
        self._batch_size = 100
        self._batch: list[dict[str, Any]] = []
    
    def write_event(self, event: dict[str, Any]) -> None:
        """
        Write an event to the audit trail.
        
        Args:
            event: Event data dictionary
        """
        self._batch.append({
            "event_type": event.get("event_type"),
            "category": event.get("category"),
            "user_id": event.get("user_id"),
            "target_type": event.get("target_type"),
            "target_id": event.get("target_id"),
            "data": event.get("data", {}),
            "ip_address": event.get("ip_address"),
            "user_agent": event.get("user_agent"),
            "created_at": event.get("created_at"),
        })
        
        if len(self._batch) >= self._batch_size:
            self._flush()
    
    def _flush(self) -> None:
        """Flush the batch to the database."""
        if not self._batch:
            return
        
        from apps.events.models import EventLog
        
        try:
            EventLog.objects.bulk_create([
                EventLog(**event) for event in self._batch
            ])
            logger.info(
                "audit_trail_batch_written",
                count=len(self._batch),
            )
            self._batch = []
        except Exception as e:
            logger.error(
                "audit_trail_batch_failed",
                error=str(e),
                count=len(self._batch),
            )
    
    def flush(self) -> None:
        """Force flush any pending events."""
        self._flush()


class CareerBrainUpdater:
    """
    Update Career Brain based on user events.
    
    Listens to events and updates the Career Brain context:
    - SkillAdded: Update skills inventory
    - JobDismissed: Update career preferences
    - GoalSet: Update goals
    - InterviewCompleted: Update AI observations
    - CVParsed: Update history summary
    - LearningCompleted: Update learning summary
    - JobApplied: Update career trajectory
    - SearchPerformed: Update career interests
    """
    
    def __init__(self):
        self._processed_events: set[str] = set()
    
    def handle_event(self, event: dict[str, Any]) -> None:
        """
        Handle an event and update Career Brain accordingly.
        
        Args:
            event: Event data dictionary
        """
        event_type = event.get("event_type", "")
        user_id = event.get("user_id")
        data = event.get("data", {})
        
        if not user_id:
            return
        
        from django.contrib.auth import get_user_model
        from apps.career.models import CareerBrain, CareerProfile, CareerLearning, CareerUserSkill
        
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            career_brain, _ = CareerBrain.objects.get_or_create(user=user)
            
            # Update based on event type
            if event_type == "skill_added":
                self._update_skills(career_brain, data)
            elif event_type == "job_dismissed":
                self._update_preferences(career_brain, data)
            elif event_type == "goal_set":
                self._update_goals(career_brain, data)
            elif event_type == "interview_session_completed":
                self._update_observations(career_brain, data)
            elif event_type == "cv_parsed":
                self._update_history(career_brain, data)
            elif event_type == "learning_completed":
                self._update_learning(career_brain, data)
            elif event_type == "job_applied":
                self._update_trajectory(career_brain, data)
            elif event_type == "search_performed":
                self._update_interests(career_brain, data)
            
            # Update confidence score
            self._update_confidence(career_brain)
            
        except User.DoesNotExist:
            logger.error("user_not_found", user_id=user_id)
    
    def _update_skills(self, career_brain: CareerBrain, data: dict) -> None:
        """Update skills inventory from skill_added event."""
        skills = career_brain.skills or {}
        if "items" not in skills:
            skills["items"] = []
        
        skill_name = data.get("skill_name", data.get("name", ""))
        if skill_name and skill_name not in [s.get("name") for s in skills["items"]]:
            skills["items"].append({
                "name": skill_name,
                "level": data.get("proficiency", "intermediate"),
                "verified": data.get("verified", False),
                "added_at": data.get("created_at"),
            })
        
        career_brain.skills = skills
    
    def _update_preferences(self, career_brain: CareerBrain, data: dict) -> None:
        """Update preferences from job_dismissed event."""
        preferences = career_brain.preferences or {}
        
        if "excluded_companies" not in preferences:
            preferences["excluded_companies"] = []
        
        company = data.get("company", "")
        if company and company not in preferences["excluded_companies"]:
            preferences["excluded_companies"].append(company)
        
        career_brain.preferences = preferences
    
    def _update_goals(self, career_brain: CareerBrain, data: dict) -> None:
        """Update goals from goal_set event."""
        goals = career_brain.goals or []
        
        new_goal = {
            "id": data.get("goal_id"),
            "title": data.get("title", data.get("role", "")),
            "description": data.get("description", ""),
            "status": "active",
            "target_date": data.get("target_date"),
            "progress": 0,
        }
        
        # Avoid duplicates
        if not any(g.get("title") == new_goal["title"] for g in goals):
            goals.append(new_goal)
        
        career_brain.goals = goals
    
    def _update_observations(self, career_brain: CareerBrain, data: dict) -> None:
        """Update AI observations from interview_session_completed event."""
        observations = career_brain.ai_observations or {}
        
        if "interviews" not in observations:
            observations["interviews"] = []
        
        observations["interviews"].append({
            "date": data.get("completed_at"),
            "type": data.get("interview_type"),
            "score": data.get("overall_score"),
        })
        
        # Generate insight
        if len(observations["interviews"]) >= 3:
            observations["key_insights"] = [
                "Consistent interview performance detected",
                "Area for improvement identified",
            ]
        
        career_brain.ai_observations = observations
    
    def _update_history(self, career_brain: CareerBrain, data: dict) -> None:
        """Update history summary from cv_parsed event."""
        history = career_brain.history_summary or {}
        
        cv_data = data.get("cv_data", {})
        
        if "experiences" not in history:
            history["experiences"] = cv_data.get("experiences", [])
        
        if "education" not in history:
            history["education"] = cv_data.get("education", [])
        
        if "skills" not in history:
            history["skills"] = cv_data.get("skills", [])
        
        career_brain.history_summary = history
    
    def _update_learning(self, career_brain: CareerBrain, data: dict) -> None:
        """Update learning summary from learning_completed event."""
        learning = career_brain.learning or {}
        
        if "completed" not in learning:
            learning["completed"] = []
        
        learning["completed"].append({
            "title": data.get("title", ""),
            "platform": data.get("platform", ""),
            "completed_at": data.get("completed_at"),
            "skills_gained": data.get("skills_gained", []),
        })
        
        # Update recent topics
        if "recent_topics" not in learning:
            learning["recent_topics"] = []
        
        for skill in data.get("skills_gained", []):
            topic = skill.get("skill_name", skill.get("name", ""))
            if topic and topic not in learning["recent_topics"]:
                learning["recent_topics"].append(topic)
        
        career_brain.learning = learning
    
    def _update_trajectory(self, career_brain: CareerBrain, data: dict) -> None:
        """Update career trajectory from job_applied event."""
        observations = career_brain.ai_observations or {}
        
        if "applications" not in observations:
            observations["applications"] = []
        
        observations["applications"].append({
            "date": data.get("applied_at"),
            "job_title": data.get("job_title", ""),
            "company": data.get("company", ""),
            "status": "applied",
        })
        
        career_brain.ai_observations = observations
    
    def _update_interests(self, career_brain: CareerBrain, data: dict) -> None:
        """Update career interests from search_performed event."""
        preferences = career_brain.preferences or {}
        
        if "interests" not in preferences:
            preferences["interests"] = []
        
        query = data.get("query", "")
        if query and query not in preferences["interests"]:
            preferences["interests"].append(query)
        
        career_brain.preferences = preferences
    
    def _update_confidence(self, career_brain: CareerBrain) -> None:
        """Update confidence score based on data completeness."""
        confidence = 0.5
        
        # Skills
        if career_brain.skills and career_brain.skills.get("items"):
            confidence += 0.1 * min(len(career_brain.skills["items"]), 10) / 10
        
        # Goals
        if career_brain.goals:
            confidence += 0.1 * min(len(career_brain.goals), 5) / 5
        
        # Learning
        if career_brain.learning and career_brain.learning.get("completed"):
            confidence += 0.1 * min(len(career_brain.learning["completed"]), 5) / 5
        
        # History
        if career_brain.history_summary:
            confidence += 0.1
        
        # Observations
        if career_brain.ai_observations:
            confidence += 0.1
        
        career_brain.confidence_score = min(1.0, confidence)
        career_brain.save(update_fields=["confidence_score", "last_updated_at"])


# Singleton instances
analytics_aggregator = AnalyticsAggregator()
audit_trail_writer = AuditTrailWriter()
career_brain_updater = CareerBrainUpdater()
