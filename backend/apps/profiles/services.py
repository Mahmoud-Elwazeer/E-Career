"""
Job matching service
Will be enhanced with AWS Bedrock in Phase 2A
"""

class MatchingService:
    """Calculate job-profile match scores"""
    
    def calculate_match_score(self, profile, job):
        """
        Basic matching algorithm (will be AI-powered in Phase 2A)
        
        Weights:
        - Skills match: 40%
        - Location match: 20%
        - Experience level match: 15%
        - Salary match: 15%
        - Industry match: 10%
        """
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
        if hasattr(profile, 'preferred_locations') and profile.preferred_locations and job.location:
            location_match = any(
                loc.lower() in job.location.lower()
                for loc in profile.preferred_locations
                if loc
            )
            if location_match:
                score += 20
        
        # Experience level match (15%)
        if hasattr(profile, 'years_of_experience') and profile.years_of_experience and job.experience_level:
            exp_mapping = {
                'entry': (0, 2),
                'junior': (1, 3),
                'mid': (3, 6),
                'senior': (6, 10),
                'lead': (8, None),
                'executive': (10, None)
            }
            
            min_exp, max_exp = exp_mapping.get(job.experience_level, (0, None))
            user_exp = profile.years_of_experience
            
            if max_exp is None:
                if user_exp >= min_exp:
                    score += 15
            elif min_exp <= user_exp <= max_exp:
                score += 15
            elif user_exp >= min_exp:
                score += 10  # Over-qualified but still a match
        
        # Salary match (15%)
        if hasattr(profile, 'desired_salary_min') and profile.desired_salary_min and job.salary_min:
            if job.salary_min >= profile.desired_salary_min:
                score += 15
            elif job.salary_max and job.salary_max >= profile.desired_salary_min:
                score += 10
        
        # Industry match (10%)
        if hasattr(profile, 'preferred_industries') and profile.preferred_industries and job.company and job.company.industry:
            if job.company.industry in profile.preferred_industries:
                score += 10
        
        return min(score, 100)  # Cap at 100
    
    def get_match_breakdown(self, profile, job):
        """Detailed breakdown of match components"""
        breakdown = {
            'overall_score': self.calculate_match_score(profile, job),
            'components': {}
        }
        
        # Skills
        if hasattr(profile, 'skills') and profile.skills:
            profile_skills = set(skill.lower() for skill in profile.skills if skill)
            job_tags = job.tags.all() if hasattr(job, 'tags') else []
            job_skills = set(tag.name.lower() for tag in job_tags)
            matched_skills = profile_skills & job_skills
            
            breakdown['components']['skills'] = {
                'score': len(matched_skills) / len(job_skills) * 100 if job_skills else 0,
                'matched': list(matched_skills),
                'missing': list(job_skills - profile_skills)
            }
        
        # Location
        location_match = False
        if hasattr(profile, 'preferred_locations') and profile.preferred_locations and job.location:
            location_match = any(
                loc.lower() in job.location.lower()
                for loc in profile.preferred_locations
                if loc
            )
        breakdown['components']['location'] = {
            'score': 100 if location_match else 0,
            'user_preference': getattr(profile, 'preferred_locations', None),
            'job_location': job.location
        }
        
        # Experience
        breakdown['components']['experience'] = {
            'user_years': getattr(profile, 'years_of_experience', None),
            'job_requirement': job.experience_level
        }
        
        # Salary
        breakdown['components']['salary'] = {
            'user_expectation': getattr(profile, 'desired_salary_min', None),
            'job_offer_min': job.salary_min,
            'job_offer_max': job.salary_max
        }
        
        return breakdown