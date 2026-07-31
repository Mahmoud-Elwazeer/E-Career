"""
Career Intelligence Services

This module provides services for profile embedding generation,
job matching, and talent scoring.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from django.utils import timezone

from apps.skills.models import Skill, Occupation, OccupationSkill
from apps.vectors.service import get_vector_service, JOBS_COLLECTION, USERS_COLLECTION

logger = logging.getLogger(__name__)


class ProfileEmbeddingService:
    """
    Service for generating and managing user profile embeddings.
    
    Generates embeddings from career profile data and stores them
    in Qdrant for semantic search.
    """
    
    def __init__(self):
        self.qdrant = QdrantService()
    
    def generate_profile_embedding(self, career_profile):
        """
        Generate embedding for a career profile.
        
        Combines: skills + experience + target roles + bio
        """
        profile_text = career_profile.get_profile_text()
        
        if not profile_text.strip():
            logger.warning(f"Profile {career_profile.id} has no text for embedding")
            return None
        
        try:
            embedding = self.qdrant.generate_embedding(profile_text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for profile {career_profile.id}: {e}")
            return None
    
    def store_profile_embedding(self, career_profile):
        """
        Store profile embedding in Qdrant users collection.
        """
        embedding = self.generate_profile_embedding(career_profile)
        
        if not embedding:
            return False
        
        try:
            # Prepare user payload
            payload = {
                'user_id': str(career_profile.user.id),
                'email': career_profile.user.email,
                'skills': self._get_user_skills(career_profile),
                'experience_years': career_profile.experience_years,
                'target_roles': [r.get('role', '') for r in career_profile.target_roles],
                'target_locations': [
                    f"{l.get('city', '')}, {l.get('country', '')}"
                    for l in career_profile.target_locations
                    if l.get('city') or l.get('country')
                ],
                'open_to_remote': career_profile.open_to_remote,
                'completeness_score': career_profile.completeness_score,
                'last_updated': timezone.now().isoformat(),
            }
            
            # Upsert to Qdrant
            self.qdrant.upsert_user(
                user_id=str(career_profile.user.id),
                vector=embedding,
                payload=payload
            )
            
            logger.info(f"Stored embedding for user {career_profile.user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embedding for profile {career_profile.id}: {e}")
            return False
    
    def _get_user_skills(self, career_profile) -> List[str]:
        """Get list of user's verified skills."""
        from .models import CareerUserSkill
        skills = CareerUserSkill.objects.filter(
            user=career_profile.user,
            verified=True
        ).select_related('skill')[:20]
        return [s.skill.name for s in skills]
    
    def reembed_all_profiles(self):
        """
        Re-embed all career profiles.
        
        Use this after updating the embedding model or Qdrant configuration.
        """
        from .models import CareerProfile
        
        profiles = CareerProfile.objects.select_related('user').all()
        success_count = 0
        fail_count = 0
        
        for profile in profiles:
            if self.store_profile_embedding(profile):
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(f"Re-embedding complete: {success_count} success, {fail_count} failed")
        return {'success': success_count, 'failed': fail_count}


class JobMatchingService:
    """
    Service for semantic job matching using vector similarity.
    
    Matches user profiles with jobs based on vector embeddings.
    """
    
    def __init__(self):
        self.qdrant = QdrantService()
    
    def find_matching_jobs(self, career_profile, limit: int = 20):
        """
        Find jobs matching user's profile using vector similarity.
        
        Args:
            career_profile: CareerProfile instance
            limit: Maximum number of results to return
            
        Returns:
            List of matching jobs with similarity scores
        """
        # Generate user embedding
        profile_text = career_profile.get_profile_text()
        if not profile_text.strip():
            return []
        
        user_embedding = self.qdrant.generate_embedding(profile_text)
        
        # Get user preferences
        user_preferences = {
            'locations': [
                loc.get('city')
                for loc in career_profile.target_locations
                if loc.get('city')
            ],
            'salary_min': career_profile.target_salary_min,
            'open_to_remote': career_profile.open_to_remote,
            'min_match_score': career_profile.min_match_score,
        }
        
        # Query Qdrant for similar jobs
        results = self.qdrant.search_jobs(
            vector=user_embedding,
            user_preferences=user_preferences,
            limit=limit
        )
        
        return results
    
    def get_profile_job_matches(self, career_profile):
        """
        Get detailed job matches with breakdown.
        
        Returns matches with similarity scores and explanations.
        """
        matches = self.find_matching_jobs(career_profile)
        
        return {
            'user_profile_id': str(career_profile.id),
            'match_count': len(matches),
            'matches': matches,
        }


class SkillGapAnalysisService:
    """
    Service for analyzing skill gaps between user and target roles.
    
    Uses the occupation-skill mapping to identify missing skills.
    """
    
    def analyze_skill_gap(self, career_profile, target_role: str = None):
        """
        Analyze skill gaps for a career profile.
        
        Args:
            career_profile: CareerProfile instance
            target_role: Optional target role to analyze (uses first target if not provided)
            
        Returns:
            Dict with missing skills, importance, and learning resources
        """
        from .models import CareerUserSkill
        
        # Get target role
        if not target_role and career_profile.target_roles:
            target_role = career_profile.target_roles[0].get('role', '')
        
        if not target_role:
            return {
                'error': 'No target role specified',
                'missing_skills': [],
            }
        
        # Find matching occupation
        from django.db.models import Q
        occupations = Occupation.objects.filter(
            Q(name__icontains=target_role) | Q(name_ar__icontains=target_role)
        )[:5]
        
        if not occupations:
            return {
                'target_role': target_role,
                'missing_skills': [],
                'message': 'No matching occupation found',
            }
        
        occupation = occupations[0]
        
        # Get required skills for the occupation
        required_skills = OccupationSkill.objects.filter(
            occupation=occupation
        ).select_related('skill').order_by('-importance')[:20]
        
        # Get user's skills
        user_skill_ids = CareerUserSkill.objects.filter(
            user=career_profile.user
        ).values_list('skill_id', flat=True)
        
        # Calculate gaps
        missing_skills = []
        skill_importance = {}
        
        for req_skill in required_skills:
            if req_skill.skill_id not in user_skill_ids:
                missing_skills.append({
                    'skill_id': str(req_skill.skill.id),
                    'skill_name': req_skill.skill.name,
                    'importance': req_skill.importance,
                    'level_required': 'expert' if req_skill.importance >= 4 else 'advanced',
                })
            skill_importance[str(req_skill.skill.id)] = req_skill.importance
        
        # Get learning resources
        learning_resources = [
            {
                'skill_id': skill['skill_id'],
                'skill_name': skill['skill_name'],
                'title': f'Learn {skill["skill_name"]}',
                'platform': 'Coursera',
                'url': f'https://coursera.org/search?query={skill["skill_name"]}',
                'difficulty': 'beginner' if skill['importance'] < 3 else 'intermediate',
                'estimated_hours': int(skill['importance'] * 10),
            }
            for skill in missing_skills[:10]
        ]
        
        return {
            'target_role': target_role,
            'target_occupation': occupation.name,
            'missing_skills': missing_skills,
            'skill_importance': skill_importance,
            'learning_resources': learning_resources,
            'total_required_skills': len(required_skills),
            'missing_count': len(missing_skills),
            'user_skills_count': len(user_skill_ids),
        }


class TalentScoreService:
    """
    Service for calculating multi-dimensional talent scores.
    
    Calculates scores across multiple dimensions with explainability.
    """
    
    def calculate_talent_score(self, career_profile):
        """
        Calculate talent score for a career profile.
        
        Returns scores across multiple dimensions:
        - Skill score
        - Experience score
        - Education score
        - Portfolio score
        - Interview score
        - Growth score
        - Communication score
        """
        from .models import CareerUserSkill, CareerLearning, TalentScore
        
        # Skill score (based on verified skills and proficiency)
        verified_skills = CareerUserSkill.objects.filter(
            user=career_profile.user, verified=True
        ).count()
        total_skills = CareerUserSkill.objects.filter(user=career_profile.user).count()
        
        if total_skills > 0:
            skill_score = min(1.0, (verified_skills / max(total_skills, 1)) * 0.7 + (total_skills / 20) * 0.3)
        else:
            skill_score = 0.0
        
        # Experience score (based on experience_years)
        experience_score = min(1.0, career_profile.experience_years / 15)
        
        # Education score (placeholder - would parse education from CV)
        education_score = 0.5  # Default
        
        # Portfolio score (based on portfolio_url and github_data)
        portfolio_score = 0.0
        if career_profile.portfolio_url:
            portfolio_score += 0.5
        if career_profile.github_data:
            portfolio_score += 0.5
        
        # Interview score (placeholder - would use interview sessions)
        interview_score = 0.0
        
        # Growth score (based on learning history)
        learning_count = CareerLearning.objects.filter(user=career_profile.user).count()
        growth_score = min(1.0, learning_count / 10)
        
        # Communication score (placeholder - would analyze CV text)
        communication_score = 0.5
        
        # Calculate overall score
        overall_score = (
            skill_score * 0.30 +
            experience_score * 0.25 +
            education_score * 0.15 +
            portfolio_score * 0.10 +
            interview_score * 0.10 +
            growth_score * 0.05 +
            communication_score * 0.05
        )
        
        # Create or update talent score
        talent_score, created = TalentScore.objects.get_or_create(
            user=career_profile.user,
            defaults={
                'skill_score': skill_score,
                'experience_score': experience_score,
                'education_score': education_score,
                'portfolio_score': portfolio_score,
                'interview_score': interview_score,
                'growth_score': growth_score,
                'communication_score': communication_score,
                'overall_score': overall_score,
                'ai_confidence': 0.7,
            }
        )
        
        if not created:
            talent_score.skill_score = skill_score
            talent_score.experience_score = experience_score
            talent_score.education_score = education_score
            talent_score.portfolio_score = portfolio_score
            talent_score.interview_score = interview_score
            talent_score.growth_score = growth_score
            talent_score.communication_score = communication_score
            talent_score.overall_score = overall_score
            talent_score.ai_confidence = 0.7
            talent_score.save()
        
        return talent_score
    
    def get_talent_score(self, career_profile):
        """Get talent score for a career profile."""
        from .models import TalentScore
        
        try:
            return TalentScore.objects.get(user=career_profile.user)
        except TalentScore.DoesNotExist:
            return self.calculate_talent_score(career_profile)


class ProfileCompletenessService:
    """
    Service for calculating profile completeness scores.
    
    Tracks which fields are complete and provides recommendations.
    """
    
    def calculate_completeness(self, career_profile):
        """
        Calculate completeness score for a career profile.
        
        Each field contributes a percentage to the completeness_score.
        Returns a list of missing/incomplete fields for UI prompts.
        """
        fields = {
            'target_roles': 10,
            'target_locations': 10,
            'target_salary_min': 10,
            'open_to_remote': 5,
            'experience_years': 10,
            'current_role': 5,
            'current_company': 5,
            'github_username': 10,
            'portfolio_url': 5,
            'alert_frequency': 5,
            'min_match_score': 5,
            'cv_parsed_data': 20,
        }
        
        total_score = 0
        missing_fields = []
        
        for field, weight in fields.items():
            value = getattr(career_profile, field, None)
            if value is None or (isinstance(value, (str, list, dict)) and not value):
                missing_fields.append(field)
            else:
                total_score += weight
        
        completeness_score = total_score / 100.0
        
        # Update profile
        career_profile.completeness_score = completeness_score
        career_profile.save(update_fields=['completeness_score'])
        
        return {
            'score': completeness_score,
            'missing_fields': missing_fields,
            'total_fields': len(fields),
            'completed_fields': len(fields) - len(missing_fields),
            'recommendations': self._get_recommendations(missing_fields),
        }
    
    def _get_recommendations(self, missing_fields) -> List[Dict]:
        """Get recommendations for completing missing fields."""
        recommendations = []
        
        field_recommendations = {
            'target_roles': {
                'title': 'Set Target Roles',
                'description': 'Define the job titles you are targeting for better matches',
                'action': 'Add your target job roles',
            },
            'target_locations': {
                'title': 'Set Target Locations',
                'description': 'Specify locations where you want to work',
                'action': 'Add your preferred locations',
            },
            'experience_years': {
                'title': 'Update Experience',
                'description': 'Add your years of experience for better scoring',
                'action': 'Update your experience years',
            },
            'current_role': {
                'title': 'Update Current Role',
                'description': 'Add your current job title',
                'action': 'Update your current role',
            },
            'current_company': {
                'title': 'Update Current Company',
                'description': 'Add your current company name',
                'action': 'Update your current company',
            },
            'github_username': {
                'title': 'Add GitHub Profile',
                'description': 'Link your GitHub for portfolio verification',
                'action': 'Add your GitHub username',
            },
            'portfolio_url': {
                'title': 'Add Portfolio',
                'description': 'Link your portfolio or personal website',
                'action': 'Add your portfolio URL',
            },
            'cv_parsed_data': {
                'title': 'Upload CV',
                'description': 'Upload your CV for automatic skill extraction',
                'action': 'Upload your CV',
            },
        }
        
        for field in missing_fields:
            if field in field_recommendations:
                recommendations.append(field_recommendations[field])
        
        return recommendations