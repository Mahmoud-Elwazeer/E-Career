"""
LightFM Job Recommendation Service

This module provides AI-powered job recommendations using LightFM
hybrid recommendation engine (collaborative + content-based).
"""

import logging
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from lightfm import LightFM
from lightfm.data import Dataset

from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from apps.jobs.models import Job, JobSave, JobView
from apps.events.models import EventLog
from apps.career.models import CareerUserSkill, CareerProfile
from apps.users.models import User

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    LightFM-based job recommendation service.
    
    Uses hybrid approach:
    - Collaborative filtering: "Users like you also applied to..."
    - Content-based: "Jobs matching your skills and preferences"
    
    Features:
    - User-item interaction matrix
    - Item features (location, industry, experience_level, skills)
    - User features (skills, experience_years, location, preferences)
    - Daily model retraining
    """
    
    def __init__(self):
        self.model = None
        self.dataset = None
        self.model_path = Path(settings.MEDIA_ROOT) / 'models' / 'lightfm_latest.pkl'
        self._ensure_model_dir()
    
    def _ensure_model_dir(self):
        """Ensure model directory exists."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
    
    def build_interaction_matrix(self) -> Tuple[sp.csr_matrix, Dict, Dict]:
        """
        Build user-item interaction matrix from events.
        
        Weights:
        - Job views: 1
        - Job saves: 3
        - Job applications: 5
        - Job dismissals: -2
        
        Returns:
            Tuple of (interaction_matrix, user_mapping, item_mapping)
        """
        # Get all users and jobs
        users = User.objects.filter(is_active=True).values_list('id', flat=True)
        jobs = Job.objects.filter(status='published').values_list('id', flat=True)
        
        user_mapping = {str(u): i for i, u in enumerate(users)}
        item_mapping = {str(j): i for i, j in enumerate(jobs)}
        
        # Build interaction matrix
        interactions = []
        weights = []
        
        # Job views (weight 1)
        view_events = EventLog.objects.filter(
            event_type='job_view',
            created_at__gte=timezone.now() - timedelta(days=90)
        ).values('user_id', 'target_id')
        
        for event in view_events:
            user_id = str(event['user_id'])
            job_id = str(event['target_id'])
            if user_id in user_mapping and job_id in item_mapping:
                interactions.append((user_mapping[user_id], item_mapping[job_id]))
                weights.append(1.0)
        
        # Job saves (weight 3)
        save_events = EventLog.objects.filter(
            event_type='job_save',
            created_at__gte=timezone.now() - timedelta(days=90)
        ).values('user_id', 'target_id')
        
        for event in save_events:
            user_id = str(event['user_id'])
            job_id = str(event['target_id'])
            if user_id in user_mapping and job_id in item_mapping:
                interactions.append((user_mapping[user_id], item_mapping[job_id]))
                weights.append(3.0)
        
        # Job applications (weight 5)
        application_events = EventLog.objects.filter(
            event_type='job_application',
            created_at__gte=timezone.now() - timedelta(days=90)
        ).values('user_id', 'target_id')
        
        for event in application_events:
            user_id = str(event['user_id'])
            job_id = str(event['target_id'])
            if user_id in user_mapping and job_id in item_mapping:
                interactions.append((user_mapping[user_id], item_mapping[job_id]))
                weights.append(5.0)
        
        # Job dismissals (weight -2)
        dismissal_events = EventLog.objects.filter(
            event_type='job_dismiss',
            created_at__gte=timezone.now() - timedelta(days=90)
        ).values('user_id', 'target_id')
        
        for event in dismissal_events:
            user_id = str(event['user_id'])
            job_id = str(event['target_id'])
            if user_id in user_mapping and job_id in item_mapping:
                interactions.append((user_mapping[user_id], item_mapping[job_id]))
                weights.append(-2.0)
        
        # Create sparse matrix
        n_users = len(user_mapping)
        n_items = len(item_mapping)
        
        if not interactions:
            # Return empty matrix if no interactions
            return sp.csr_matrix((n_users, n_items)), user_mapping, item_mapping
        
        row_indices, col_indices = zip(*interactions)
        interaction_matrix = sp.csr_matrix(
            (weights, (row_indices, col_indices)),
            shape=(n_users, n_items)
        )
        
        return interaction_matrix, user_mapping, item_mapping
    
    def build_item_features(self) -> sp.csr_matrix:
        """
        Build item (job) feature matrix.
        
        Features:
        - Location (one-hot)
        - Industry (one-hot)
        - Experience level (one-hot)
        - Skills (multi-hot)
        - Salary range (normalized)
        
        Returns:
            Item feature matrix
        """
        jobs = Job.objects.filter(status='published').select_related('company')
        
        # Collect all unique feature values
        locations = set()
        industries = set()
        experience_levels = set()
        skills = set()
        
        for job in jobs:
            locations.add(job.location)
            if job.company and job.company.industry:
                industries.add(job.company.industry)
            if job.experience_level:
                experience_levels.add(job.experience_level)
            
            # Extract skills from job description
            job_skills = self._extract_skills_from_job(job)
            skills.update(job_skills)
        
        # Build feature mappings
        location_map = {loc: i for i, loc in enumerate(sorted(locations))}
        industry_map = {ind: i for i, ind in enumerate(sorted(industries))}
        experience_map = {exp: i for i, exp in enumerate(sorted(experience_levels))}
        skill_map = {sk: i for i, sk in enumerate(sorted(skills))}
        
        n_jobs = len(jobs)
        n_features = (
            len(locations) +
            len(industries) +
            len(experience_levels) +
            len(skills)
        )
        
        # Build sparse feature matrix
        features = []
        row_indices = []
        col_indices = []
        
        for i, job in enumerate(jobs):
            # Location feature
            if job.location in location_map:
                col_indices.append(i)
                row_indices.append(location_map[job.location])
                features.append(1.0)
            
            # Industry feature
            if job.company and job.company.industry in industry_map:
                col_indices.append(i)
                row_indices.append(len(location_map) + industry_map[job.company.industry])
                features.append(1.0)
            
            # Experience level feature
            if job.experience_level in experience_map:
                col_indices.append(i)
                row_indices.append(
                    len(location_map) + len(industry_map) + experience_map[job.experience_level]
                )
                features.append(1.0)
            
            # Skills features
            job_skills = self._extract_skills_from_job(job)
            base_idx = len(location_map) + len(industry_map) + len(experience_map)
            for skill in job_skills:
                if skill in skill_map:
                    col_indices.append(i)
                    row_indices.append(base_idx + skill_map[skill])
                    features.append(1.0)
        
        item_features = sp.csr_matrix(
            (features, (row_indices, col_indices)),
            shape=(n_jobs, n_features)
        )
        
        return item_features
    
    def build_user_features(self) -> sp.csr_matrix:
        """
        Build user feature matrix.
        
        Features:
        - Skills (multi-hot)
        - Experience years (normalized)
        - Location (one-hot)
        - Remote preference (binary)
        
        Returns:
            User feature matrix
        """
        users = User.objects.filter(is_active=True)
        
        # Collect all unique feature values
        skills = set()
        locations = set()
        
        for user in users:
            # Get user skills
            user_skills = CareerUserSkill.objects.filter(user=user, verified=True)
            for us in user_skills:
                skills.add(us.skill.name)
            
            # Get user location from career profile
            try:
                profile = user.career_profile
                if profile.cv_parsed_data.get('location'):
                    locations.add(profile.cv_parsed_data['location'])
            except Exception:
                pass
        
        # Build feature mappings
        skill_map = {sk: i for i, sk in enumerate(sorted(skills))}
        location_map = {loc: i for i, loc in enumerate(sorted(locations))}
        
        n_users = len(users)
        n_features = len(skills) + len(locations) + 2  # +2 for experience and remote
        
        # Build sparse feature matrix
        features = []
        row_indices = []
        col_indices = []
        
        for i, user in enumerate(users):
            base_idx = 0
            
            # Skills features
            user_skills = CareerUserSkill.objects.filter(user=user, verified=True)
            for us in user_skills:
                if us.skill.name in skill_map:
                    col_indices.append(i)
                    row_indices.append(base_idx + skill_map[us.skill.name])
                    features.append(1.0)
            
            base_idx += len(skills)
            
            # Location feature
            try:
                profile = user.career_profile
                if profile.cv_parsed_data.get('location') in location_map:
                    col_indices.append(i)
                    row_indices.append(base_idx + location_map[profile.cv_parsed_data['location']])
                    features.append(1.0)
            except Exception:
                pass
            
            base_idx += len(locations)
            
            # Experience years (normalized 0-1)
            try:
                profile = user.career_profile
                exp_years = profile.experience_years
                normalized_exp = min(1.0, exp_years / 20.0)  # Cap at 20 years
                col_indices.append(i)
                row_indices.append(base_idx)
                features.append(normalized_exp)
            except Exception:
                col_indices.append(i)
                row_indices.append(base_idx)
                features.append(0.0)
            
            base_idx += 1
            
            # Remote preference (binary)
            try:
                profile = user.career_profile
                remote_pref = 1.0 if profile.open_to_remote else 0.0
                col_indices.append(i)
                row_indices.append(base_idx)
                features.append(remote_pref)
            except Exception:
                col_indices.append(i)
                row_indices.append(base_idx)
                features.append(0.0)
        
        user_features = sp.csr_matrix(
            (features, (row_indices, col_indices)),
            shape=(n_users, n_features)
        )
        
        return user_features
    
    def train_model(self, interaction_matrix: sp.csr_matrix,
                   user_features: sp.csr_matrix,
                   item_features: sp.csr_matrix) -> LightFM:
        """
        Train LightFM hybrid model.
        
        Args:
            interaction_matrix: User-item interactions
            user_features: User feature matrix
            item_features: Item feature matrix
            
        Returns:
            Trained LightFM model
        """
        # Get dimensions
        n_users = interaction_matrix.shape[0]
        n_items = interaction_matrix.shape[1]
        
        # Create model
        # Use hybrid mode with features
        model = LightFM(
            loss='warp',  # Weighted Approximate-Rank Pairwise
            learning_rate=0.05,
            k=50,  # Embedding dimension
            no_components=100,
            user_alpha=0.001,
            item_alpha=0.001,
            random_state=42
        )
        
        # Train
        n_epochs = 20
        for epoch in range(n_epochs):
            model.fit(
                interaction_matrix,
                user_features=user_features,
                item_features=item_features,
                epochs=1,
                num_threads=4,
                verbose=True
            )
        
        # Save model
        self._save_model(model, user_features.shape[1], item_features.shape[1])
        
        return model
    
    def _save_model(self, model: LightFM, n_user_features: int, n_item_features: int):
        """Save trained model to disk."""
        model_data = {
            'model': model,
            'n_user_features': n_user_features,
            'n_item_features': n_item_features,
            'saved_at': timezone.now().isoformat(),
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self) -> Optional[LightFM]:
        """Load trained model from disk."""
        if not self.model_path.exists():
            return None
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            self.model = model_data['model']
            return self.model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def get_recommendations(self, user_id: int, n: int = 20) -> List[Dict]:
        """
        Get top N job recommendations for a user.
        
        Args:
            user_id: User ID
            n: Number of recommendations
            
        Returns:
            List of job recommendations with scores
        """
        if not self.model:
            self.load_model()
        
        if not self.model:
            return []  # Return empty if model not available
        
        # Get user index
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return []
        
        # Get all jobs
        all_jobs = list(Job.objects.filter(status='published').values_list('id', flat=True))
        
        # Get user's seen jobs
        seen_jobs = set()
        
        # From event log
        seen_events = EventLog.objects.filter(
            user=user,
            event_type__in=['job_view', 'job_save', 'job_application'],
            target_type='job'
        ).values_list('target_id', flat=True)
        seen_jobs.update(str(j) for j in seen_events)
        
        # From career profile saves
        try:
            profile = user.career_profile
            if profile.cv_parsed_data.get('saved_jobs'):
                seen_jobs.update(str(j) for j in profile.cv_parsed_data['saved_jobs'])
        except Exception:
            pass
        
        # Get unseen jobs
        unseen_jobs = [j for j in all_jobs if str(j) not in seen_jobs]
        
        if not unseen_jobs:
            return []
        
        # Get user features
        user_features = self._get_user_features(user)
        
        # Get item features for unseen jobs
        item_features = self._get_item_features(unseen_jobs)
        
        # Predict scores
        scores = self.model.predict(
            user_ids=np.array([0] * len(unseen_jobs)),  # Single user
            item_ids=np.array(unseen_jobs),
            user_features=user_features,
            item_features=item_features
        )
        
        # Sort by score
        job_scores = list(zip(unseen_jobs, scores))
        job_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N
        top_jobs = job_scores[:n]
        
        # Build result
        results = []
        for job_id, score in top_jobs:
            try:
                job = Job.objects.get(id=job_id)
                results.append({
                    'job_id': job_id,
                    'title': job.title,
                    'company': job.company_name,
                    'location': job.location,
                    'score': float(score),
                    'match_reason': self._get_match_reason(job, user),
                })
            except Job.DoesNotExist:
                continue
        
        return results
    
    def _get_user_features(self, user) -> sp.csr_matrix:
        """Get feature vector for a single user."""
        # Build single-row user feature matrix
        features = []
        col_indices = []
        
        # Skills
        user_skills = CareerUserSkill.objects.filter(user=user, verified=True)
        for us in user_skills:
            col_indices.append(0)  # All skills in first row
            features.append(1.0)
        
        # Location
        try:
            profile = user.career_profile
            if profile.cv_parsed_data.get('location'):
                col_indices.append(1)
                features.append(1.0)
        except Exception:
            pass
        
        # Experience (normalized)
        try:
            profile = user.career_profile
            exp_years = profile.experience_years
            normalized_exp = min(1.0, exp_years / 20.0)
            col_indices.append(2)
            features.append(normalized_exp)
        except Exception:
            col_indices.append(2)
            features.append(0.0)
        
        # Remote preference
        try:
            profile = user.career_profile
            remote_pref = 1.0 if profile.open_to_remote else 0.0
            col_indices.append(3)
            features.append(remote_pref)
        except Exception:
            col_indices.append(3)
            features.append(0.0)
        
        return sp.csr_matrix(
            (features, ([0] * len(col_indices), col_indices)),
            shape=(1, 4 + 10)  # Base features + skills
        )
    
    def _get_item_features(self, job_ids: List[int]) -> sp.csr_matrix:
        """Get feature matrix for a list of jobs."""
        jobs = Job.objects.filter(id__in=job_ids)
        
        features = []
        row_indices = []
        col_indices = []
        
        for i, job in enumerate(jobs):
            # Location
            col_indices.append(i)
            row_indices.append(0)
            features.append(1.0)
            
            # Experience level
            if job.experience_level:
                col_indices.append(i)
                row_indices.append(1)
                features.append(1.0)
        
        return sp.csr_matrix(
            (features, (row_indices, col_indices)),
            shape=(len(jobs), 10)
        )
    
    def _get_match_reason(self, job: Job, user) -> str:
        """Generate match reason for a job."""
        reasons = []
        
        # Check skill match
        user_skills = CareerUserSkill.objects.filter(user=user, verified=True)
        job_skills = self._extract_skills_from_job(job)
        
        matched_skills = []
        for us in user_skills:
            if us.skill.name.lower() in [s.lower() for s in job_skills]:
                matched_skills.append(us.skill.name)
        
        if matched_skills:
            reasons.append(f"مطابقة للمهارات: {', '.join(matched_skills[:2])}")
        
        # Check experience
        try:
            profile = user.career_profile
            if profile.experience_years >= 5:
                reasons.append("خبرة مناسبة")
        except Exception:
            pass
        
        # Check location
        try:
            profile = user.career_profile
            if profile.cv_parsed_data.get('location'):
                if profile.cv_parsed_data['location'] in job.location:
                    reasons.append("مطابقة للموقع")
        except Exception:
            pass
        
        if not reasons:
            reasons.append("مطابقة عامة")
        
        return '; '.join(reasons)
    
    def _extract_skills_from_job(self, job: Job) -> List[str]:
        """Extract skills from job description."""
        common_skills = [
            'python', 'javascript', 'react', 'node.js', 'java', 'c++', 'sql',
            'aws', 'docker', 'kubernetes', 'git', 'agile', 'scrum', 'linux',
            'html', 'css', 'typescript', 'angular', 'vue', 'flutter', 'swift',
            'android', 'ios', 'machine learning', 'data analysis', 'project management'
        ]
        
        text = (job.description or '').lower()
        found = [s for s in common_skills if s in text]
        return found[:10]


# Singleton instance
recommendation_service = RecommendationService()