"""
Hybrid Recommendation Engine

Combines:
1. Content-based filtering (skill/experience matching via scoring engine)
2. Collaborative filtering (LightFM user-item interaction matrix)
3. Vector similarity (pgvector embeddings when available)

Produces ranked job recommendations for a user.
"""
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.db.models import Q, F, Count
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

try:
    from lightfm import LightFM
    from lightfm.data import Dataset
    from scipy.sparse import csr_matrix
    LIGHTFM_AVAILABLE = True
except ImportError:
    LIGHTFM_AVAILABLE = False


class RecommendationEngine:
    """
    Hybrid recommendation engine combining content-based and collaborative filtering.
    """

    CONTENT_WEIGHT = 0.6
    COLLABORATIVE_WEIGHT = 0.3
    RECENCY_WEIGHT = 0.1

    def __init__(self):
        self._model = None
        self._dataset = None
        self._user_map = {}
        self._item_map = {}
        self._last_trained = None

    def get_recommendations(self, user, limit: int = 20) -> List[Dict]:
        """
        Get job recommendations for a user, combining multiple signals.

        Returns a list of dicts: [{job_id, score, reasons, source}]
        """
        from apps.jobs.models import Job
        from apps.career.models import CareerProfile

        try:
            profile = CareerProfile.objects.get(user=user)
        except CareerProfile.DoesNotExist:
            return self._fallback_recommendations(user, limit)

        # 1. Content-based scores
        content_scores = self._content_based_scores(user, profile, limit * 3)

        # 2. Collaborative filtering scores (if model trained)
        collab_scores = {}
        if LIGHTFM_AVAILABLE and self._model and user.id in self._user_map:
            collab_scores = self._collaborative_scores(user, limit * 3)

        # 3. Recency boost for new postings
        recent_jobs = set(
            Job.objects.filter(
                status='active',
                created_at__gte=timezone.now() - timedelta(days=7)
            ).values_list('id', flat=True)[:100]
        )

        # Merge scores
        all_job_ids = set(content_scores.keys()) | set(collab_scores.keys())
        merged = []

        for job_id in all_job_ids:
            c_score = content_scores.get(job_id, {}).get('score', 0)
            cf_score = collab_scores.get(job_id, 0)
            recency = 1.0 if job_id in recent_jobs else 0.0

            final_score = (
                self.CONTENT_WEIGHT * c_score +
                self.COLLABORATIVE_WEIGHT * cf_score +
                self.RECENCY_WEIGHT * recency
            )

            reasons = content_scores.get(job_id, {}).get('reasons', [])
            if cf_score > 0.5:
                reasons.append('Similar users applied to this job')
            if job_id in recent_jobs:
                reasons.append('Recently posted')

            merged.append({
                'job_id': job_id,
                'score': round(final_score, 3),
                'reasons': reasons,
                'content_score': round(c_score, 3),
                'collaborative_score': round(cf_score, 3),
            })

        merged.sort(key=lambda x: x['score'], reverse=True)
        return merged[:limit]

    def _content_based_scores(self, user, profile, limit: int) -> Dict[int, Dict]:
        """Score jobs based on skill/location/role match."""
        from apps.jobs.models import Job

        user_skills = set(s.lower() for s in (profile.skills or []))
        target_roles = [r.lower() for r in (profile.target_roles or [])]
        target_locations = [l.lower() for l in (profile.target_locations or [])]

        candidates = Job.objects.filter(status='active').exclude(
            id__in=self._get_applied_job_ids(user)
        ).order_by('-created_at')[:500]

        scores = {}
        for job in candidates:
            score, reasons = self._score_job_match(job, user_skills, target_roles, target_locations)
            if score > 0.1:
                scores[job.id] = {'score': score, 'reasons': reasons}

        # Sort and take top
        sorted_ids = sorted(scores.keys(), key=lambda jid: scores[jid]['score'], reverse=True)
        return {jid: scores[jid] for jid in sorted_ids[:limit]}

    def _score_job_match(self, job, user_skills: set, target_roles: list, target_locations: list) -> Tuple[float, List[str]]:
        """Calculate content match score for a single job."""
        score = 0.0
        reasons = []

        # Skill match (0-0.5)
        job_text = f"{job.title} {job.description or ''}".lower()
        matched_skills = [s for s in user_skills if s in job_text]
        if user_skills:
            skill_ratio = len(matched_skills) / max(len(user_skills), 1)
            skill_score = min(skill_ratio * 0.5, 0.5)
            score += skill_score
            if matched_skills:
                reasons.append(f"Matches skills: {', '.join(matched_skills[:3])}")

        # Role match (0-0.3)
        title_lower = job.title.lower()
        for role in target_roles:
            if role in title_lower or title_lower in role:
                score += 0.3
                reasons.append(f"Matches target role: {job.title}")
                break

        # Location match (0-0.2)
        job_location = (getattr(job, 'location', '') or '').lower()
        for loc in target_locations:
            if loc in job_location or job_location in loc:
                score += 0.2
                reasons.append(f"Location match: {job_location}")
                break

        return min(score, 1.0), reasons

    def _collaborative_scores(self, user, limit: int) -> Dict[int, float]:
        """Get collaborative filtering scores from LightFM model."""
        if not self._model or user.id not in self._user_map:
            return {}

        user_idx = self._user_map[user.id]
        n_items = len(self._item_map)

        try:
            scores = self._model.predict(user_idx, np.arange(n_items))
            # Normalize to 0-1
            min_s, max_s = scores.min(), scores.max()
            if max_s > min_s:
                scores = (scores - min_s) / (max_s - min_s)
            else:
                scores = np.zeros_like(scores)

            # Map back to job IDs
            idx_to_job = {v: k for k, v in self._item_map.items()}
            result = {}
            for idx in np.argsort(scores)[::-1][:limit]:
                job_id = idx_to_job.get(int(idx))
                if job_id:
                    result[job_id] = float(scores[idx])
            return result
        except Exception as e:
            logger.warning("Collaborative scoring failed: %s", e)
            return {}

    def train_model(self):
        """
        Train the LightFM collaborative filtering model from interaction data.
        Call this periodically via Celery beat (e.g., daily).
        """
        if not LIGHTFM_AVAILABLE:
            logger.info("LightFM not available, skipping training")
            return

        from apps.jobs.models import Job
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Build interaction matrix from: saved jobs, applications, profile views
        interactions = self._build_interaction_matrix()
        if not interactions:
            logger.info("No interactions found, skipping training")
            return

        users, items, weights = zip(*interactions)
        unique_users = list(set(users))
        unique_items = list(set(items))

        self._user_map = {uid: idx for idx, uid in enumerate(unique_users)}
        self._item_map = {iid: idx for idx, iid in enumerate(unique_items)}

        n_users = len(unique_users)
        n_items = len(unique_items)

        rows = [self._user_map[u] for u in users]
        cols = [self._item_map[i] for i in items]
        data = list(weights)

        interaction_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(n_users, n_items)
        )

        self._model = LightFM(
            no_components=64,
            loss='warp',
            learning_rate=0.05,
            random_state=42,
        )
        self._model.fit(interaction_matrix, epochs=10, num_threads=2)
        self._last_trained = timezone.now()

        logger.info(
            "LightFM model trained: %d users, %d items, %d interactions",
            n_users, n_items, len(interactions)
        )

    def _build_interaction_matrix(self) -> List[Tuple[int, int, float]]:
        """Build user-job interactions from multiple signals."""
        interactions = []

        # Saved jobs (weight 1.0)
        try:
            from apps.career.models import CareerProfile
            for profile in CareerProfile.objects.exclude(saved_jobs=[]).only('user_id', 'saved_jobs'):
                if profile.saved_jobs:
                    for job_id in profile.saved_jobs:
                        interactions.append((profile.user_id, job_id, 1.0))
        except Exception:
            pass

        # Applications (weight 2.0 - stronger signal)
        try:
            from apps.employers.models import JobApplication
            for app in JobApplication.objects.all().values_list('applicant_id', 'job_id'):
                interactions.append((app[0], app[1], 2.0))
        except Exception:
            pass

        return interactions

    def _get_applied_job_ids(self, user) -> set:
        """Get job IDs the user already applied to (exclude from recs)."""
        try:
            from apps.employers.models import JobApplication
            return set(
                JobApplication.objects.filter(applicant=user).values_list('job_id', flat=True)
            )
        except Exception:
            return set()

    def _fallback_recommendations(self, user, limit: int) -> List[Dict]:
        """Fallback: return recent active jobs when no profile exists."""
        from apps.jobs.models import Job
        jobs = Job.objects.filter(status='active').order_by('-created_at')[:limit]
        return [
            {'job_id': j.id, 'score': 0.5, 'reasons': ['Recently posted'], 'content_score': 0, 'collaborative_score': 0}
            for j in jobs
        ]


recommendation_engine = RecommendationEngine()
