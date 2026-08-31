"""
Machine Learning Recommendation Engine

This module implements a LightFM-based recommendation engine for job recommendations.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from django.db.models import QuerySet
from django.conf import settings

from apps.jobs.models import Job
from apps.career.models import CareerUserSkill, CareerLearning, TalentScore
from apps.core.models import GitHubConnection

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Machine learning recommendation engine using LightFM.
    
    Features:
    - Collaborative filtering recommendations
    - Content-based filtering recommendations
    - Hybrid recommendations (weighted combination)
    - Personalized job recommendations
    - Similar job recommendations
    """
    
    def __init__(self, user):
        """
        Initialize the recommendation engine for a specific user.
        
        Args:
            user: Django User instance
        """
        self.user = user
        self._model = None
        self._item_features = None
        self._user_features = None
        self._job_mapping = None
        self._skill_mapping = None
    
    @property
    def model(self):
        """Get or create the LightFM model."""
        if self._model is None:
            try:
                import lightfm
                from lightfm import LightFM
                self._model = LightFM(
                    loss='warp',
                    learning_rate=0.05,
                    no_components=64,
                    k=5,
                    n=10,
                    max_sampled=10,
                    random_state=42,
                )
            except ImportError:
                logger.warning("LightFM not installed, using fallback recommendations")
                return None
        return self._model
    
    @property
    def item_features(self):
        """Get item features matrix."""
        if self._item_features is None:
            self._build_item_features()
        return self._item_features
    
    @property
    def user_features(self):
        """Get user features matrix."""
        if self._user_features is None:
            self._build_user_features()
        return self._user_features
    
    @property
    def job_mapping(self):
        """Get job ID to index mapping."""
        if self._job_mapping is None:
            self._build_mappings()
        return self._job_mapping
    
    @property
    def skill_mapping(self):
        """Get skill ID to index mapping."""
        if self._skill_mapping is None:
            self._build_mappings()
        return self._skill_mapping
    
    # =========================================================================
    # Feature Building Methods
    # =========================================================================
    
    def _build_mappings(self):
        """Build job and skill ID mappings."""
        # Get all active jobs
        jobs = Job.objects.filter(status='active').values_list('id', 'uuid')
        self._job_mapping = {str(job.uuid): idx for idx, job in enumerate(jobs)}
        
        # Get all skills
        from apps.skills.models import Skill
        skills = Skill.objects.all().values_list('id', 'name')
        self._skill_mapping = {skill_id: idx for idx, (skill_id, _) in enumerate(skills)}
    
    def _build_item_features(self):
        """Build item features matrix from job data."""
        try:
            from scipy import sparse
        except ImportError:
            logger.warning("Scipy not installed, using fallback recommendations")
            return None
        
        # Get all active jobs
        jobs = Job.objects.filter(status='active')
        
        n_jobs = len(jobs)
        n_skills = len(self.skill_mapping)
        
        # Create sparse matrix for item features
        item_features = sparse.lil_matrix((n_jobs, n_skills), dtype=np.float32)
        
        for job_idx, job in enumerate(jobs):
            # Get job skills
            job_skills = job.skills.all() if hasattr(job, 'skills') else []
            for skill in job_skills:
                if skill.id in self.skill_mapping:
                    skill_idx = self.skill_mapping[skill.id]
                    item_features[job_idx, skill_idx] = 1.0
            
            # Add job type features
            if job.employment_type:
                type_idx = self._get_type_feature_index(job.employment_type)
                if type_idx is not None:
                    item_features[job_idx, type_idx] = 1.0
            
            # Add location features
            if job.location:
                loc_idx = self._get_location_feature_index(job.location)
                if loc_idx is not None:
                    item_features[job_idx, loc_idx] = 1.0
        
        self._item_features = item_features.tocsr()
        return self._item_features
    
    def _build_user_features(self):
        """Build user features matrix from user data."""
        try:
            from scipy import sparse
        except ImportError:
            logger.warning("Scipy not installed, using fallback recommendations")
            return None
        
        n_users = 1  # Single user
        n_skills = len(self.skill_mapping)
        
        # Create sparse matrix for user features
        user_features = sparse.lil_matrix((n_users, n_skills), dtype=np.float32)
        
        # Get user skills
        user_skills = CareerUserSkill.objects.filter(user=self.user)
        for user_skill in user_skills:
            if user_skill.skill.id in self.skill_mapping:
                skill_idx = self.skill_mapping[user_skill.skill.id]
                # Weight by proficiency
                proficiency_weights = {
                    'beginner': 0.5,
                    'intermediate': 0.75,
                    'advanced': 0.9,
                    'expert': 1.0,
                }
                weight = proficiency_weights.get(user_skill.proficiency, 0.5)
                user_features[0, skill_idx] = weight
        
        # Get user learning history
        learning = CareerLearning.objects.filter(user=self.user)
        for learn in learning:
            for skill_data in learn.skills_gained:
                skill_name = skill_data.get('skill_name')
                if skill_name and skill_name in self.skill_mapping:
                    skill_idx = self.skill_mapping[skill_name]
                    user_features[0, skill_idx] = min(
                        user_features[0, skill_idx] + 0.3, 1.0
                    )
        
        self._user_features = user_features.tocsr()
        return self._user_features
    
    def _get_type_feature_index(self, employment_type: str) -> Optional[int]:
        """Get index for employment type feature."""
        type_features = {
            'full_time': 0,
            'part_time': 1,
            'contract': 2,
            'freelance': 3,
            'internship': 4,
        }
        return type_features.get(employment_type)
    
    def _get_location_feature_index(self, location: str) -> Optional[int]:
        """Get index for location feature."""
        # Simple hash-based location encoding
        return hash(location) % 100
    
    # =========================================================================
    # Training Methods
    # =========================================================================
    
    def train(self, jobs: Optional[QuerySet] = None) -> Dict[str, Any]:
        """
        Train the recommendation model.
        
        Args:
            jobs: Optional queryset of jobs to train on
            
        Returns:
            Dictionary with training results
        """
        try:
            from scipy import sparse
        except ImportError:
            return {'error': 'Scipy not installed'}
        
        if jobs is None:
            jobs = Job.objects.filter(status='active')
        
        # Build mappings if not already built
        if self._job_mapping is None:
            self._build_mappings()
        
        n_jobs = len(jobs)
        n_users = 1  # Single user
        
        # Build interaction matrix
        interactions = sparse.lil_matrix((n_users, n_jobs), dtype=np.float32)
        
        # Get user's job applications
        from apps.jobs.models import JobApplication
        applications = JobApplication.objects.filter(user=self.user)
        
        # Positive interactions (applied jobs)
        for app in applications:
            if app.job and str(app.job.uuid) in self.job_mapping:
                job_idx = self.job_mapping[str(app.job.uuid)]
                # Weight by application status
                status_weights = {
                    'submitted': 1.0,
                    'screening': 1.5,
                    'interview': 2.0,
                    'offer': 2.5,
                    'accepted': 3.0,
                }
                weight = status_weights.get(app.status, 1.0)
                interactions[0, job_idx] = weight
        
        # Train the model
        if self.model is None:
            return {'error': 'Model not initialized'}
        
        self.model.fit(
            sparse.csr_matrix(interactions),
            item_features=self.item_features,
            epochs=30,
            num_threads=4,
            verbose=True,
        )
        
        return {
            'success': True,
            'n_jobs': n_jobs,
            'n_interactions': interactions.nnz,
            'model_trained': True,
        }
    
    # =========================================================================
    # Recommendation Methods
    # =========================================================================
    
    def get_recommendations(
        self,
        n_recommendations: int = 10,
        n_items: int = 20,
        item_features: Optional[Any] = None,
        user_features: Optional[Any] = None,
        num_threads: int = 4,
        exclude_seen: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get job recommendations for the user.
        
        Args:
            n_recommendations: Number of recommendations to return
            n_items: Number of items to consider
            item_features: Optional item features matrix
            user_features: Optional user features matrix
            num_threads: Number of threads to use
            exclude_seen: Whether to exclude already applied jobs
            
        Returns:
            List of recommended jobs with scores
        """
        if self.model is None:
            return self._get_fallback_recommendations(n_recommendations)
        
        if item_features is None:
            item_features = self.item_features
        
        if user_features is None:
            user_features = self.user_features
        
        # Get scores for all jobs
        scores = self.model.predict(
            user_ids=np.array([0]),
            item_ids=np.arange(len(self.job_mapping)),
            item_features=item_features,
            user_features=user_features,
            num_threads=num_threads,
        )
        
        # Get indices sorted by score
        job_indices = np.argsort(-scores)
        
        # Get recommended jobs
        recommendations = []
        for idx in job_indices[:n_items]:
            # Find job UUID from index
            job_uuid = None
            for uuid, index in self.job_mapping.items():
                if index == idx:
                    job_uuid = uuid
                    break
            
            if job_uuid:
                try:
                    job = Job.objects.get(uuid=job_uuid)
                    
                    # Calculate hybrid score
                    content_score = self._calculate_content_score(job)
                    collaborative_score = scores[idx] / 10.0  # Normalize
                    
                    # Weighted combination
                    hybrid_score = (
                        collaborative_score * 0.6 +
                        content_score * 0.4
                    )
                    
                    recommendations.append({
                        'job_id': str(job.uuid),
                        'job_title': job.title,
                        'company_name': job.company.name if job.company else '',
                        'location': job.location,
                        'score': round(hybrid_score, 3),
                        'collaborative_score': round(collaborative_score, 3),
                        'content_score': round(content_score, 3),
                        'employment_type': job.employment_type,
                        'work_arrangement': job.work_arrangement,
                        'salary_min': job.salary_min,
                        'salary_max': job.salary_max,
                    })
                except Job.DoesNotExist:
                    continue
        
        # Exclude already applied jobs if requested
        if exclude_seen:
            from apps.jobs.models import JobApplication
            applied_jobs = set(
                str(app.job.uuid) for app in JobApplication.objects.filter(user=self.user)
            )
            recommendations = [
                r for r in recommendations if r['job_id'] not in applied_jobs
            ]
        
        return recommendations[:n_recommendations]
    
    def _calculate_content_score(self, job: Job) -> float:
        """
        Calculate content-based score for a job.
        
        Args:
            job: Job instance
            
        Returns:
            Content-based score (0-1)
        """
        score = 0.0
        
        # Skill match score
        user_skills = set(
            s.skill.id for s in CareerUserSkill.objects.filter(user=self.user)
        )
        job_skills = set(
            s.id for s in job.skills.all() if hasattr(job, 'skills')
        )
        
        if user_skills and job_skills:
            overlap = len(user_skills & job_skills)
            union = len(user_skills | job_skills)
            skill_match = overlap / union if union > 0 else 0
            score += skill_match * 0.4
        
        # Experience match
        user_profile = getattr(self.user, 'career_profile', None)
        if user_profile and user_profile.experience_years:
            experience_diff = abs({'entry': 1, 'mid': 4, 'senior': 8, 'lead': 12}.get(job.experience_level, 4) - user_profile.experience_years)
            experience_score = max(0, 1 - experience_diff / 10)
            score += experience_score * 0.3
        
        # Location match
        if user_profile and user_profile.open_to_remote:
            if job.work_arrangement in ['remote', 'hybrid']:
                score += 0.3
            elif user_profile.target_locations:
                for loc in user_profile.target_locations:
                    loc_str = loc.get('city', '') if isinstance(loc, dict) else str(loc)
                    if loc_str and loc_str in job.location:
                        score += 0.3
                        break
        
        return min(score, 1.0)
    
    def _get_fallback_recommendations(self, n_recommendations: int) -> List[Dict[str, Any]]:
        """
        Get fallback recommendations when ML model is not available.

        Production-quality content-based + collaborative signals engine.

        Args:
            n_recommendations: Number of recommendations to return

        Returns:
            List of recommended jobs with comprehensive scoring
        """
        # Import models at function level to avoid circular imports
        from apps.users.models import SavedJob
        from apps.jobs.models import JobApplication

        # Get user profile
        user_profile = getattr(self.user, 'career_profile', None)

        # Build user preference data
        user_data = self._build_user_preference_data(user_profile)

        # Get collaborative signals
        collab_signals = self._get_collaborative_signals()

        # Get active jobs with related data
        jobs = Job.objects.filter(status='active').select_related('company').prefetch_related('skills')[:500]

        # Score jobs
        scored_jobs = []
        company_counts = {}

        for job in jobs:
            # Calculate comprehensive score
            score = self._calculate_fallback_score(job, user_data, collab_signals, user_profile)

            if score > 0:
                company_name = job.company.name if job.company else 'Unknown'

                scored_jobs.append({
                    'job': job,
                    'job_id': str(job.uuid),
                    'job_title': job.title,
                    'company_name': company_name,
                    'location': job.location,
                    'score': round(score, 3),
                    'collaborative_score': 0.0,
                    'content_score': round(score, 3),
                    'employment_type': job.employment_type,
                    'work_arrangement': job.work_arrangement,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max,
                })

        # Sort by score
        scored_jobs.sort(key=lambda x: x['score'], reverse=True)

        # Apply diversity constraint (max 3 jobs per company)
        final_recommendations = []
        company_counts = {}

        for item in scored_jobs:
            company_name = item['company_name']
            if company_counts.get(company_name, 0) < 3:
                final_recommendations.append(item)
                company_counts[company_name] = company_counts.get(company_name, 0) + 1

                if len(final_recommendations) >= n_recommendations:
                    break

        # Remove the job object from final output
        for item in final_recommendations:
            item.pop('job', None)

        return final_recommendations

    def _build_user_preference_data(self, user_profile) -> Dict[str, Any]:
        """
        Build user preference data for matching.

        Args:
            user_profile: CareerProfile instance or None

        Returns:
            Dictionary with user preferences
        """
        data = {
            'target_roles': [],
            'skills': {},
            'experience_years': 0,
            'target_locations': [],
            'open_to_remote': True,
            'target_salary_min': None,
            'target_salary_currency': 'USD',
        }

        if not user_profile:
            return data

        # Target roles
        if user_profile.target_roles:
            data['target_roles'] = [
                (r.get('role', '') if isinstance(r, dict) else str(r)).lower()
                for r in user_profile.target_roles
            ]

        # Skills with proficiency levels
        user_skills = CareerUserSkill.objects.filter(user=self.user).select_related('skill')
        proficiency_weights = {
            'beginner': 0.4,
            'intermediate': 0.7,
            'advanced': 0.9,
            'expert': 1.0,
        }
        for us in user_skills:
            weight = proficiency_weights.get(us.proficiency, 0.5)
            data['skills'][us.skill.name.lower()] = {
                'weight': weight,
                'skill_obj': us.skill,
            }

        # Experience and preferences
        data['experience_years'] = user_profile.experience_years or 0
        data['open_to_remote'] = user_profile.open_to_remote
        data['target_salary_min'] = user_profile.target_salary_min
        data['target_salary_currency'] = user_profile.target_salary_currency or 'USD'

        # Target locations
        if user_profile.target_locations:
            data['target_locations'] = [
                (loc.get('city', '') if isinstance(loc, dict) else str(loc)).lower()
                for loc in user_profile.target_locations
            ]

        return data

    def _get_collaborative_signals(self) -> Dict[str, float]:
        """
        Get collaborative filtering signals from user interactions.

        Returns:
            Dictionary mapping job_id to signal strength
        """
        from apps.users.models import SavedJob
        from apps.jobs.models import JobApplication

        signals = {}

        # Application signals (stronger)
        applications = JobApplication.objects.filter(user=self.user).select_related('job')
        status_weights = {
            'submitted': 1.0,
            'screening': 1.5,
            'interview': 2.0,
            'offer': 2.5,
            'accepted': 3.0,
            'rejected': -0.5,
            'withdrawn': -0.3,
        }
        for app in applications:
            if app.job:
                weight = status_weights.get(app.status, 1.0)
                signals[str(app.job.uuid)] = weight

        # Saved job signals (moderate - weight 0.5 as specified)
        saved_jobs = SavedJob.objects.filter(user=self.user).select_related('job')
        for saved in saved_jobs:
            if saved.job:
                job_id = str(saved.job.uuid)
                # Don't override stronger application signals
                if job_id not in signals or signals[job_id] < 0.5:
                    signals[job_id] = 0.5

        return signals

    def _calculate_fallback_score(
        self,
        job: Job,
        user_data: Dict[str, Any],
        collab_signals: Dict[str, float],
        user_profile
    ) -> float:
        """
        Calculate comprehensive fallback score for a job.

        Args:
            job: Job instance
            user_data: User preference data
            collab_signals: Collaborative signals
            user_profile: CareerProfile instance

        Returns:
            Final score (0-10)
        """
        score = 0.0

        # 1. Collaborative signal (if exists)
        job_id = str(job.uuid)
        if job_id in collab_signals:
            signal = collab_signals[job_id]
            if signal > 0:
                # Positive signals boost similar jobs
                score += 2.0
            elif signal < 0:
                # Negative signals penalize
                return 0.0  # Don't recommend rejected/withdrawn jobs

        # 2. Title match with target roles (weight: 2.5)
        job_title_lower = job.title.lower()
        for role in user_data['target_roles']:
            if role and role in job_title_lower:
                score += 2.5
                break

        # 3. Skill matching with proficiency weighting (weight: 3.0)
        skill_score = self._calculate_skill_match_score(job, user_data['skills'])
        score += skill_score * 3.0

        # 4. Experience level matching (weight: 1.5)
        exp_score = self._calculate_experience_match_score(job, user_data['experience_years'])
        score += exp_score * 1.5

        # 5. Location and remote preference matching (weight: 1.5)
        location_score = self._calculate_location_match_score(
            job,
            user_data['target_locations'],
            user_data['open_to_remote']
        )
        score += location_score * 1.5

        # 6. Salary range matching (weight: 1.0)
        salary_score = self._calculate_salary_match_score(
            job,
            user_data['target_salary_min'],
            user_data['target_salary_currency']
        )
        score += salary_score * 1.0

        # 7. Recency boost (weight: 0.5)
        recency_score = self._calculate_recency_score(job)
        score += recency_score * 0.5

        return score

    def _calculate_skill_match_score(self, job: Job, user_skills: Dict[str, Dict]) -> float:
        """
        Calculate skill match score with proficiency weighting.

        Args:
            job: Job instance
            user_skills: Dict mapping skill name to {weight, skill_obj}

        Returns:
            Score between 0 and 1
        """
        if not user_skills:
            return 0.0

        job_description_lower = (job.description or '').lower()
        job_title_lower = job.title.lower()

        # Get job skills from relationship
        job_skills = set()
        try:
            for skill in job.skills.all():
                job_skills.add(skill.name.lower())
        except:
            pass

        matched_weight = 0.0
        total_weight = sum(s['weight'] for s in user_skills.values())

        for skill_name, skill_data in user_skills.items():
            skill_weight = skill_data['weight']

            # Check for skill in job skills, title, or description
            if skill_name in job_skills:
                matched_weight += skill_weight
            elif skill_name in job_title_lower:
                matched_weight += skill_weight * 0.8
            elif skill_name in job_description_lower:
                matched_weight += skill_weight * 0.5

        return matched_weight / total_weight if total_weight > 0 else 0.0

    def _calculate_experience_match_score(self, job: Job, user_experience_years: int) -> float:
        """
        Calculate experience level match score.

        Args:
            job: Job instance
            user_experience_years: User's years of experience

        Returns:
            Score between 0 and 1
        """
        if not job.experience_level or user_experience_years is None:
            return 0.5  # Neutral score

        # Map experience levels to years
        level_to_years = {
            'entry': 1,
            'junior': 2,
            'mid': 4,
            'senior': 8,
            'lead': 12,
            'principal': 15,
        }

        job_years = level_to_years.get(job.experience_level, 4)
        diff = abs(job_years - user_experience_years)

        # Score decreases with difference
        if diff == 0:
            return 1.0
        elif diff <= 2:
            return 0.8
        elif diff <= 4:
            return 0.6
        elif diff <= 6:
            return 0.4
        else:
            return 0.2

    def _calculate_location_match_score(
        self,
        job: Job,
        target_locations: List[str],
        open_to_remote: bool
    ) -> float:
        """
        Calculate location preference match score.

        Args:
            job: Job instance
            target_locations: List of target location strings
            open_to_remote: Whether user is open to remote work

        Returns:
            Score between 0 and 1
        """
        score = 0.0

        # Remote/hybrid preference
        if open_to_remote:
            if job.work_arrangement == 'remote':
                score = 1.0
            elif job.work_arrangement == 'hybrid':
                score = 0.8
            else:
                # Still check location match for on-site
                score = 0.3

        # Location match
        if target_locations and job.location:
            job_location_lower = job.location.lower()
            for target_loc in target_locations:
                if target_loc and target_loc in job_location_lower:
                    score = max(score, 0.9)
                    break

        # If no preferences set, neutral score
        if not open_to_remote and not target_locations:
            score = 0.5

        return score

    def _calculate_salary_match_score(
        self,
        job: Job,
        target_salary_min: Optional[float],
        target_currency: str
    ) -> float:
        """
        Calculate salary range match score.

        Args:
            job: Job instance
            target_salary_min: User's minimum target salary
            target_currency: User's target currency

        Returns:
            Score between 0 and 1
        """
        if not target_salary_min or not job.salary_min:
            return 0.5  # Neutral score when data unavailable

        # Simple currency check (ideally would use conversion rates)
        job_currency = getattr(job, 'salary_currency', 'USD') or 'USD'
        if job_currency != target_currency:
            return 0.5  # Neutral when currencies don't match

        # Check if job salary range meets or exceeds target
        if job.salary_max and job.salary_max >= target_salary_min:
            # Job can meet target
            if job.salary_min >= target_salary_min:
                return 1.0  # Entire range above target
            else:
                # Range includes target
                range_size = job.salary_max - job.salary_min
                overlap = job.salary_max - target_salary_min
                return 0.7 + (overlap / range_size * 0.3) if range_size > 0 else 0.7
        elif job.salary_min >= target_salary_min * 0.8:
            # Close to target (within 20%)
            return 0.6
        else:
            # Below target
            return 0.3

    def _calculate_recency_score(self, job: Job) -> float:
        """
        Calculate recency boost score.

        Args:
            job: Job instance

        Returns:
            Score between 0 and 1
        """
        if not job.posted_at:
            return 0.5  # Neutral for unknown post date

        from datetime import date
        today = date.today()
        days_old = (today - job.posted_at).days

        # Boost newer jobs
        if days_old <= 3:
            return 1.0
        elif days_old <= 7:
            return 0.9
        elif days_old <= 14:
            return 0.8
        elif days_old <= 30:
            return 0.6
        elif days_old <= 60:
            return 0.4
        else:
            return 0.2
    
    def get_similar_jobs(self, job_uuid: str, n_similar: int = 5) -> List[Dict[str, Any]]:
        """
        Get jobs similar to a specific job.
        
        Args:
            job_uuid: UUID of the job to find similar jobs for
            n_similar: Number of similar jobs to return
            
        Returns:
            List of similar jobs with scores
        """
        if self.model is None:
            return []
        
        if str(job_uuid) not in self.job_mapping:
            return []
        
        job_idx = self.job_mapping[str(job_uuid)]
        
        # Get item features for this job
        item_features = self.item_features[job_idx:job_idx+1]
        
        # Get scores for all jobs
        scores = self.model.predict(
            user_ids=np.array([0] * len(self.job_mapping)),
            item_ids=np.arange(len(self.job_mapping)),
            item_features=self.item_features,
            num_threads=4,
        )
        
        # Get indices sorted by score
        job_indices = np.argsort(-scores)
        
        # Get similar jobs
        similar_jobs = []
        for idx in job_indices[:n_similar + 1]:
            if idx == job_idx:
                continue  # Skip the original job
            
            # Find job UUID from index
            job_uuid = None
            for uuid, index in self.job_mapping.items():
                if index == idx:
                    job_uuid = uuid
                    break
            
            if job_uuid:
                try:
                    job = Job.objects.get(uuid=job_uuid)
                    similar_jobs.append({
                        'job_id': str(job.uuid),
                        'job_title': job.title,
                        'company_name': job.company.name if job.company else '',
                        'location': job.location,
                        'score': round(scores[idx], 3),
                        'employment_type': job.employment_type,
                        'work_arrangement': job.work_arrangement,
                    })
                except Job.DoesNotExist:
                    continue
        
        return similar_jobs
    
    def get_user_profile_embedding(self) -> List[float]:
        """
        Get user profile embedding for similarity matching.
        
        Returns:
            List of floats representing user profile embedding
        """
        # Get user skills
        user_skills = CareerUserSkill.objects.filter(user=self.user)
        skill_scores = [0.0] * len(self.skill_mapping)
        
        for user_skill in user_skills:
            if user_skill.skill.id in self.skill_mapping:
                skill_idx = self.skill_mapping[user_skill.skill.id]
                proficiency_weights = {
                    'beginner': 0.5,
                    'intermediate': 0.75,
                    'advanced': 0.9,
                    'expert': 1.0,
                }
                skill_scores[skill_idx] = proficiency_weights.get(
                    user_skill.proficiency, 0.5
                )
        
        return skill_scores


# Global recommendation engine instance
recommendation_engine = None


def get_recommendation_engine(user) -> RecommendationEngine:
    """
    Get or create a recommendation engine for a user.
    
    Args:
        user: Django User instance
        
    Returns:
        RecommendationEngine instance
    """
    global recommendation_engine
    recommendation_engine = RecommendationEngine(user)
    return recommendation_engine