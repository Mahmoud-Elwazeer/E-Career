"""
Profile Completeness Calculator

Calculates the completeness score for a user's career profile based on
filled fields, verified skills, and external signals.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

from django.utils import timezone

logger = logging.getLogger(__name__)


class ProfileCompletenessCalculator:
    """
    Calculates profile completeness score for career profiles.
    
    Scoring dimensions:
    - Basic Information (15%): Name, email, location
    - Professional Summary (10%): Bio, headline, career goals
    - Experience (20%): Years, current role, company, achievements
    - Education (15%): Degrees, institutions, graduation dates
    - Skills (20%): Verified skills, skill diversity
    - External Signals (10%): GitHub, portfolio, certifications
    - Career Preferences (10%): Target roles, locations, salary
    
    Total: 100%
    """
    
    # Weight distribution
    WEIGHTS = {
        'basic_info': 0.15,
        'professional_summary': 0.10,
        'experience': 0.20,
        'education': 0.15,
        'skills': 0.20,
        'external_signals': 0.10,
        'career_preferences': 0.10,
    }
    
    def __init__(self, career_profile):
        """
        Initialize calculator with career profile.
        
        Args:
            career_profile: CareerProfile instance
        """
        self.career_profile = career_profile
        self.user = career_profile.user
        self._profile_data = None
        self._skills = None
        self._github_data = None
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calculate complete profile completeness score.
        
        Returns:
            Dictionary with:
            - score: Overall completeness score (0-100)
            - breakdown: Score by dimension
            - missing_fields: List of missing/empty fields
            - recommendations: Suggestions to improve score
        """
        # Get profile data
        profile_data = self._get_profile_data()
        
        # Calculate scores for each dimension
        scores = {
            'basic_info': self._calculate_basic_info_score(profile_data),
            'professional_summary': self._calculate_professional_summary_score(profile_data),
            'experience': self._calculate_experience_score(profile_data),
            'education': self._calculate_education_score(profile_data),
            'skills': self._calculate_skills_score(),
            'external_signals': self._calculate_external_signals_score(profile_data),
            'career_preferences': self._calculate_career_preferences_score(profile_data),
        }
        
        # Calculate weighted total
        total_score = sum(
            scores[dim] * self.WEIGHTS[dim] 
            for dim in self.WEIGHTS
        )
        
        # Get missing fields and recommendations
        missing_fields = self._get_missing_fields(profile_data)
        recommendations = self._get_recommendations(scores, missing_fields)
        
        return {
            'score': round(total_score, 1),
            'breakdown': {k: round(v, 1) for k, v in scores.items()},
            'missing_fields': missing_fields,
            'recommendations': recommendations,
            'calculated_at': timezone.now().isoformat(),
        }
    
    def _get_profile_data(self) -> Dict[str, Any]:
        """Get profile data as dictionary."""
        return {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'location': getattr(self.career_profile, 'location', ''),
            'bio': getattr(self.career_profile, 'bio', ''),
            'headline': getattr(self.career_profile, 'headline', ''),
            'experience_years': self.career_profile.experience_years,
            'current_role': self.career_profile.current_role,
            'current_company': self.career_profile.current_company,
            'target_roles': self.career_profile.target_roles,
            'target_locations': self.career_profile.target_locations,
            'target_salary_min': self.career_profile.target_salary_min,
            'open_to_remote': self.career_profile.open_to_remote,
            'github_username': self.career_profile.github_username,
            'portfolio_url': self.career_profile.portfolio_url,
            'cv_parsed_data': self.career_profile.cv_parsed_data,
        }
    
    def _calculate_basic_info_score(self, data: Dict[str, Any]) -> float:
        """Calculate basic information score (0-100)."""
        score = 0
        
        # Name (50% weight within dimension)
        if data.get('first_name') and data.get('last_name'):
            score += 50
        elif data.get('first_name') or data.get('last_name'):
            score += 25
        
        # Email (50% weight within dimension)
        if data.get('email'):
            score += 50
        
        return min(score, 100)
    
    def _calculate_professional_summary_score(self, data: Dict[str, Any]) -> float:
        """Calculate professional summary score (0-100)."""
        score = 0
        
        # Bio (40% weight)
        bio = data.get('bio', '')
        if bio and len(bio) >= 100:
            score += 40
        elif bio and len(bio) >= 50:
            score += 20
        
        # Headline (30% weight)
        headline = data.get('headline', '')
        if headline and len(headline) >= 10:
            score += 30
        
        # Career goals (30% weight)
        target_roles = data.get('target_roles', [])
        if target_roles and len(target_roles) >= 1:
            score += 30
        
        return min(score, 100)
    
    def _calculate_experience_score(self, data: Dict[str, Any]) -> float:
        """Calculate experience score (0-100)."""
        score = 0
        
        # Experience years (30% weight)
        years = data.get('experience_years', 0)
        if years >= 10:
            score += 30
        elif years >= 5:
            score += 20
        elif years >= 1:
            score += 10
        
        # Current role (30% weight)
        if data.get('current_role'):
            score += 30
        
        # Current company (20% weight)
        if data.get('current_company'):
            score += 20
        
        # CV parsed data (20% weight)
        cv_data = data.get('cv_parsed_data', {})
        if cv_data and cv_data.get('experience'):
            score += 20
        
        return min(score, 100)
    
    def _calculate_education_score(self, data: Dict[str, Any]) -> float:
        """Calculate education score (0-100)."""
        score = 0
        
        cv_data = data.get('cv_parsed_data', {})
        education = cv_data.get('education', [])
        
        if education:
            score += 50  # Has education data
        
        # Check for degree type
        for edu in education:
            if edu.get('degree'):
                score += 25
                break
        
        # Check for institution
        for edu in education:
            if edu.get('institution'):
                score += 25
                break
        
        return min(score, 100)
    
    def _calculate_skills_score(self) -> float:
        """Calculate skills score (0-100)."""
        from apps.career.models import CareerUserSkill
        
        # Get verified skills
        verified_skills = CareerUserSkill.objects.filter(
            user=self.user,
            verified=True
        ).select_related('skill')
        
        skill_count = verified_skills.count()
        
        if skill_count == 0:
            return 0
        
        # Base score for having skills
        score = min(skill_count * 10, 50)  # Max 50 for skill count
        
        # Add score for skill diversity
        skill_types = verified_skills.values_list('skill__type', flat=True).distinct()
        if len(skill_types) >= 3:
            score += 25
        elif len(skill_types) >= 2:
            score += 15
        elif len(skill_types) >= 1:
            score += 10
        
        # Add score for skill verification
        if skill_count >= 10:
            score += 25
        elif skill_count >= 5:
            score += 15
        elif skill_count >= 3:
            score += 10
        
        return min(score, 100)
    
    def _calculate_external_signals_score(self, data: Dict[str, Any]) -> float:
        """Calculate external signals score (0-100)."""
        score = 0
        
        # GitHub (50% weight)
        github_username = data.get('github_username', '')
        if github_username:
            github_data = data.get('github_data', {})
            if github_data:
                score += 50  # GitHub data exists
            else:
                score += 25  # Username provided but data not fetched
        
        # Portfolio (30% weight)
        portfolio_url = data.get('portfolio_url', '')
        if portfolio_url:
            score += 30
        
        # Certifications (20% weight)
        cv_data = data.get('cv_parsed_data', {})
        certifications = cv_data.get('certifications', [])
        if certifications:
            score += 20
        
        return min(score, 100)
    
    def _calculate_career_preferences_score(self, data: Dict[str, Any]) -> float:
        """Calculate career preferences score (0-100)."""
        score = 0
        
        # Target roles (30% weight)
        target_roles = data.get('target_roles', [])
        if target_roles and len(target_roles) >= 1:
            score += 30
        
        # Target locations (30% weight)
        target_locations = data.get('target_locations', [])
        if target_locations and len(target_locations) >= 1:
            score += 30
        
        # Salary expectations (20% weight)
        if data.get('target_salary_min'):
            score += 20
        
        # Open to remote (20% weight)
        if data.get('open_to_remote') is not None:
            score += 20
        
        return min(score, 100)
    
    def _get_missing_fields(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get list of missing/empty fields."""
        missing = []
        
        if not data.get('first_name'):
            missing.append({'field': 'first_name', 'label': 'First Name'})
        if not data.get('last_name'):
            missing.append({'field': 'last_name', 'label': 'Last Name'})
        if not data.get('headline'):
            missing.append({'field': 'headline', 'label': 'Professional Headline'})
        if not data.get('bio') or len(data.get('bio', '')) < 50:
            missing.append({'field': 'bio', 'label': 'Professional Bio (min 50 chars)'})
        if not data.get('current_role'):
            missing.append({'field': 'current_role', 'label': 'Current Role'})
        if not data.get('target_roles'):
            missing.append({'field': 'target_roles', 'label': 'Target Roles'})
        if not data.get('target_locations'):
            missing.append({'field': 'target_locations', 'label': 'Target Locations'})
        
        return missing
    
    def _get_recommendations(
        self, 
        scores: Dict[str, float], 
        missing_fields: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Get recommendations to improve profile score."""
        recommendations = []
        
        # Dimension-specific recommendations
        if scores.get('basic_info', 0) < 50:
            recommendations.append({
                'category': 'basic_info',
                'title': 'Complete Your Basic Information',
                'description': 'Add your first name, last name, and location to improve your profile visibility.',
            })
        
        if scores.get('professional_summary', 0) < 50:
            recommendations.append({
                'category': 'professional_summary',
                'title': 'Write a Professional Summary',
                'description': 'Add a headline and bio that highlights your professional background and career goals.',
            })
        
        if scores.get('skills', 0) < 50:
            recommendations.append({
                'category': 'skills',
                'title': 'Add More Skills',
                'description': 'Add verified skills to your profile to improve skill-based job matching.',
            })
        
        if scores.get('external_signals', 0) < 50:
            recommendations.append({
                'category': 'external_signals',
                'title': 'Connect External Accounts',
                'description': 'Link your GitHub profile and portfolio to showcase your work.',
            })
        
        # Missing field recommendations
        for field in missing_fields[:3]:  # Top 3 missing fields
            recommendations.append({
                'category': 'missing_field',
                'title': f'Add {field["label"]}',
                'description': f'Your profile is missing {field["label"]}. This helps employers understand your background better.',
            })
        
        return recommendations[:6]  # Return top 6 recommendations


def calculate_profile_completeness(career_profile) -> Dict[str, Any]:
    """
    Convenience function to calculate profile completeness.
    
    Args:
        career_profile: CareerProfile instance
        
    Returns:
        Completeness score dictionary
    """
    calculator = ProfileCompletenessCalculator(career_profile)
    return calculator.calculate()