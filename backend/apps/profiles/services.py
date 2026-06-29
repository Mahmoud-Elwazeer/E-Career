"""
Enhanced job matching service with AI
"""

import logging
from typing import Dict, List, Optional
from django.db.models import Q

from apps.jobs.models import Job
from apps.users.models import UserProfile

logger = logging.getLogger(__name__)


class MatchingService:
    """Enhanced job matching with AI"""
    
    def calculate_match_score(self, profile: UserProfile, job: Job) -> float:
        """
        Calculate comprehensive match score using AI
        
        Returns:
            float: Match score 0-100
        """
        # Try AI-powered matching first
        try:
            from ai.bedrock import bedrock_service
            
            profile_data = self._serialize_profile(profile)
            job_data = self._serialize_job(job)
            
            match_result = bedrock_service.calculate_match_score(profile_data, job_data)
            return match_result.get('overall_score', 0)
        
        except Exception as e:
            logger.warning(f"AI matching failed, falling back to basic algorithm: {e}")
            return self._basic_match_score(profile, job)
    
    def get_match_breakdown(self, profile: UserProfile, job: Job) -> Dict:
        """
        Get detailed match breakdown with AI insights
        
        Returns:
            dict: Detailed breakdown with scores and recommendations
        """
        try:
            from ai.bedrock import bedrock_service
            
            profile_data = self._serialize_profile(profile)
            job_data = self._serialize_job(job)
            
            match_result = bedrock_service.calculate_match_score(profile_data, job_data)
            
            return {
                'overall_score': match_result.get('overall_score', 0),
                'breakdown': match_result.get('breakdown', {}),
                'strengths': match_result.get('strengths', []),
                'gaps': match_result.get('gaps', []),
                'recommendation': match_result.get('recommendation', ''),
                'improvement_tips': self._generate_improvement_tips(match_result)
            }
        
        except Exception as e:
            logger.error(f"Error getting match breakdown: {e}")
            return self._basic_match_breakdown(profile, job)
    
    def get_recommended_jobs(
        self,
        profile: UserProfile,
        limit: int = 20,
        min_score: float = 60.0
    ) -> List[Dict]:
        """
        Get personalized job recommendations
        
        Args:
            profile: User profile
            limit: Max number of jobs to return
            min_score: Minimum match score threshold
        
        Returns:
            List of {job, score, reasoning} dicts
        """
        # Build query based on profile preferences
        query = Q(is_active=True)
        
        # Filter by preferred locations
        if hasattr(profile, 'desired_locations') and profile.desired_locations:
            location_query = Q()
            for loc in profile.desired_locations:
                if loc:
                    location_query |= Q(location__icontains=loc)
            if location_query:
                query &= location_query
        
        # Filter by desired roles (fuzzy match)
        if hasattr(profile, 'desired_roles') and profile.desired_roles:
            title_query = Q()
            for title in profile.desired_roles:
                if title:
                    title_query |= Q(title__icontains=title)
            if title_query:
                query &= title_query
        
        # Filter by workplace preference
        if hasattr(profile, 'preferred_type') and profile.preferred_type:
            if profile.preferred_type == 'remote':
                query &= Q(location_type='remote')
            elif profile.preferred_type == 'onsite':
                query &= Q(location_type='onsite')
            elif profile.preferred_type == 'hybrid':
                query &= Q(location_type='hybrid')
        
        # Get candidate jobs
        jobs = Job.objects.filter(query).select_related('company').order_by('-posted_date')[:100]
        
        # Score and rank
        scored_jobs = []
        for job in jobs:
            score = self.calculate_match_score(profile, job)
            
            if score >= min_score:
                scored_jobs.append({
                    'job': job,
                    'score': score,
                    'reasoning': self._generate_match_reasoning(profile, job, score)
                })
        
        # Sort by score
        scored_jobs.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_jobs[:limit]
    
    def get_similar_jobs(self, job: Job, limit: int = 5) -> List[Job]:
        """Get jobs similar to the given job"""
        query = Q(is_active=True)
        query &= ~Q(id=job.id)  # Exclude the job itself
        
        # Same category/industry
        if job.company and job.company.industry:
            query &= Q(company__industry=job.company.industry)
        
        # Similar location
        if job.location:
            location_part = job.location.split(',')[0] if ',' in job.location else job.location
            query &= Q(location__icontains=location_part)
        
        # Similar experience level
        if job.experience_level:
            query &= Q(experience_level=job.experience_level)
        
        similar_jobs = Job.objects.filter(query).select_related('company').order_by('-posted_date')[:limit]
        
        return list(similar_jobs)
    
    def _serialize_profile(self, profile: UserProfile) -> Dict:
        """Serialize profile for AI processing"""
        return {
            'skills': profile.skills or [],
            'experience_years': getattr(profile, 'experience_years', 0) or 0,
            'education': getattr(profile, 'education', []) or [],
            'preferred_locations': getattr(profile, 'desired_locations', []) or [],
            'preferred_industries': getattr(profile, 'preferred_industries', []) or [],
            'desired_roles': getattr(profile, 'desired_roles', []) or [],
            'min_salary': getattr(profile, 'min_salary', None),
            'open_to_remote': getattr(profile, 'open_to_remote', False),
            'preferred_type': getattr(profile, 'preferred_type', ''),
            'languages': getattr(profile, 'languages', []) or [],
        }
    
    def _serialize_job(self, job: Job) -> Dict:
        """Serialize job for AI processing"""
        return {
            'title': job.title,
            'description': (job.description or '')[:500],  # Truncate for API limits
            'location': job.location or '',
            'location_type': getattr(job, 'location_type', '') or '',
            'employment_type': getattr(job, 'employment_type', '') or '',
            'experience_level': getattr(job, 'experience_level', '') or '',
            'salary_min': float(job.salary_min) if getattr(job, 'salary_min', None) else None,
            'salary_max': float(job.salary_max) if getattr(job, 'salary_max', None) else None,
            'company': {
                'name': job.company.name if job.company else '',
                'industry': job.company.industry if job.company else '',
            } if job.company else {},
            'required_skills': [tag.name for tag in job.tags.all()] if hasattr(job, 'tags') else [],
        }
    
    def _basic_match_score(self, profile: UserProfile, job: Job) -> float:
        """Fallback basic matching algorithm"""
        score = 0.0
        
        # Skills match (40%)
        if hasattr(profile, 'skills') and profile.skills:
            profile_skills = set(skill.lower() for skill in profile.skills if skill)
            job_tags = job.tags.all() if hasattr(job, 'tags') else []
            job_skills = set(tag.name.lower() for tag in job_tags)
            
            if job_skills:
                skills_match = len(profile_skills & job_skills) / len(job_skills)
                score += skills_match * 40
        
        # Location match (20%)
        if hasattr(profile, 'desired_locations') and profile.desired_locations and job.location:
            location_match = any(
                loc.lower() in job.location.lower()
                for loc in profile.desired_locations
                if loc
            )
            if location_match:
                score += 20
        
        # Experience level match (15%)
        if hasattr(profile, 'experience_years') and profile.experience_years and job.experience_level:
            exp_mapping = {
                'entry': (0, 2),
                'junior': (1, 3),
                'mid': (3, 6),
                'senior': (6, 10),
                'lead': (8, None),
                'executive': (10, None)
            }
            
            min_exp, max_exp = exp_mapping.get(job.experience_level, (0, None))
            user_exp = profile.experience_years
            
            if max_exp is None:
                if user_exp >= min_exp:
                    score += 15
            elif min_exp <= user_exp <= max_exp:
                score += 15
            elif user_exp >= min_exp:
                score += 10  # Over-qualified but still a match
        
        # Salary match (15%)
        if hasattr(profile, 'min_salary') and profile.min_salary and getattr(job, 'salary_min', None):
            if job.salary_min >= profile.min_salary:
                score += 15
            elif getattr(job, 'salary_max', None) and job.salary_max >= profile.min_salary:
                score += 10
        
        # Industry match (10%)
        if hasattr(profile, 'preferred_industries') and profile.preferred_industries:
            if job.company and job.company.industry:
                if job.company.industry in profile.preferred_industries:
                    score += 10
        
        return min(score, 100)  # Cap at 100
    
    def _basic_match_breakdown(self, profile: UserProfile, job: Job) -> Dict:
        """Fallback basic breakdown"""
        return {
            'overall_score': self._basic_match_score(profile, job),
            'breakdown': {
                'skills': {'score': 0, 'reasoning': 'Basic algorithm'},
                'experience': {'score': 0, 'reasoning': 'Basic algorithm'},
                'location': {'score': 0, 'reasoning': 'Basic algorithm'}
            },
            'strengths': [],
            'gaps': [],
            'recommendation': 'Consider applying if interested',
            'improvement_tips': []
        }
    
    def _generate_improvement_tips(self, match_result: Dict) -> List[str]:
        """Generate actionable tips to improve match score"""
        tips = []
        
        gaps = match_result.get('gaps', [])
        breakdown = match_result.get('breakdown', {})
        
        # Skills gaps
        if 'skills' in breakdown:
            skills_score = breakdown['skills'].get('score', 0)
            if skills_score < 70:
                missing_skills = breakdown['skills'].get('missing', [])
                if missing_skills:
                    tips.append(
                        f"Learn these skills to improve your match: {', '.join(missing_skills[:3])}"
                    )
        
        # Experience gaps
        if 'experience' in breakdown:
            exp_score = breakdown['experience'].get('score', 0)
            if exp_score < 70:
                tips.append(
                    "Gain more relevant experience in this field or highlight similar projects"
                )
        
        # Education gaps
        if 'education' in breakdown:
            edu_score = breakdown['education'].get('score', 0)
            if edu_score < 70:
                tips.append(
                    "Consider taking relevant courses or certifications"
                )
        
        return tips
    
    def _generate_match_reasoning(self, profile: UserProfile, job: Job, score: float) -> str:
        """Generate human-readable reasoning for match"""
        if score >= 90:
            return "Excellent match! Your profile aligns very well with this opportunity."
        elif score >= 75:
            return "Strong match. You meet most of the key requirements."
        elif score >= 60:
            return "Good match. Consider applying if the role interests you."
        else:
            return "Partial match. Some skills may need development."


# Singleton instance
matching_service = MatchingService()