"""
Enhanced Job Matching Service - Phase F AI Enhancements

Semantic job search and personalized ranking using embeddings and AI.
"""
import logging
from typing import List, Dict, Tuple
from django.db.models import Q, F
from apps.jobs.models import Job
from apps.vectors.services import vector_service
from apps.intelligence.career_ai import career_ai_service as bedrock_service

logger = logging.getLogger(__name__)


class JobMatchingService:
    """
    Advanced job matching using semantic search and AI ranking.
    """

    def __init__(self):
        self.vector_service = vector_service
        self.bedrock = bedrock_service

    def semantic_job_search(
        self,
        query: str,
        user_profile: dict = None,
        limit: int = 20,
        filters: dict = None
    ) -> List[Dict]:
        """
        Semantic job search using embeddings.

        Args:
            query: Search query text
            user_profile: User profile for personalization
            limit: Number of results
            filters: Additional filters (location, salary, etc.)

        Returns:
            List of jobs with match scores
        """
        try:
            # Get embedding for search query
            query_embedding = self.vector_service.embed_text(query)

            # Vector similarity search
            similar_jobs = self.vector_service.similarity_search(
                query_embedding=query_embedding,
                top_k=limit * 2,  # Get more candidates for reranking
                filters=filters
            )

            # Rerank based on user profile if available
            if user_profile:
                similar_jobs = self._personalized_rerank(similar_jobs, user_profile)

            return similar_jobs[:limit]

        except Exception as e:
            logger.error(f"Semantic job search failed: {e}")
            # Fallback to keyword search
            return self._fallback_search(query, filters, limit)

    def _personalized_rerank(
        self,
        jobs: List[Dict],
        user_profile: dict
    ) -> List[Dict]:
        """
        Rerank jobs based on user profile and preferences.

        Considers:
        - Skills match
        - Experience level fit
        - Location preferences
        - Salary expectations
        - Career trajectory
        """
        user_skills = set(user_profile.get('skills', []))
        user_exp_level = user_profile.get('experience_level', 'entry')
        preferred_locations = set(user_profile.get('preferred_locations', []))
        salary_min = user_profile.get('salary_expectation_min', 0)

        scored_jobs = []

        for job in jobs:
            score = job.get('similarity_score', 0.5)

            # Skill match boost
            job_skills = set(job.get('required_skills', []))
            skill_overlap = len(user_skills & job_skills)
            if skill_overlap > 0:
                score += 0.1 * min(skill_overlap, 5)  # Max +0.5 boost

            # Experience level match
            if job.get('experience_level') == user_exp_level:
                score += 0.15
            elif self._is_adjacent_exp_level(job.get('experience_level'), user_exp_level):
                score += 0.05

            # Location preference
            if job.get('location') in preferred_locations:
                score += 0.1

            # Salary match
            job_salary_max = job.get('salary_max', 0)
            if job_salary_max >= salary_min:
                score += 0.05

            # Remote work preference
            if user_profile.get('prefers_remote') and job.get('remote_type') == 'remote':
                score += 0.1

            job['personalized_score'] = min(score, 1.0)  # Cap at 1.0
            scored_jobs.append(job)

        # Sort by personalized score
        scored_jobs.sort(key=lambda x: x['personalized_score'], reverse=True)

        return scored_jobs

    def _is_adjacent_exp_level(self, level1: str, level2: str) -> bool:
        """Check if experience levels are adjacent"""
        levels = ['student', 'entry', 'mid', 'senior', 'director', 'c_level']
        try:
            idx1 = levels.index(level1)
            idx2 = levels.index(level2)
            return abs(idx1 - idx2) == 1
        except ValueError:
            return False

    def _fallback_search(self, query: str, filters: dict, limit: int) -> List[Dict]:
        """Fallback keyword search if semantic search fails"""
        queryset = Job.objects.filter(status='active')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query)
            )

        if filters:
            if filters.get('location'):
                queryset = queryset.filter(location__icontains=filters['location'])
            if filters.get('remote_type'):
                queryset = queryset.filter(work_arrangement=filters['remote_type'])
            if filters.get('experience_level'):
                queryset = queryset.filter(experience_level=filters['experience_level'])

        jobs = queryset.select_related('company')[:limit]

        return [
            {
                'id': str(job.id),
                'title': job.title,
                'company': job.company.name,
                'location': job.location,
                'similarity_score': 0.5,  # Default score
            }
            for job in jobs
        ]

    def analyze_skill_gaps(
        self,
        user_skills: List[str],
        target_job_id: str
    ) -> Dict:
        """
        Analyze skill gaps between user and target job.

        Returns:
            {
                'matched_skills': [...],
                'missing_skills': [...],
                'match_percentage': 75.0,
                'recommendations': [...]
            }
        """
        try:
            job = Job.objects.get(id=target_job_id)
            job_skills = set(skill.name for skill in job.required_skills.all())
            user_skills_set = set(user_skills)

            matched = user_skills_set & job_skills
            missing = job_skills - user_skills_set

            match_percentage = (len(matched) / len(job_skills) * 100) if job_skills else 0

            return {
                'matched_skills': list(matched),
                'missing_skills': list(missing),
                'match_percentage': round(match_percentage, 1),
                'recommendations': self._generate_learning_recommendations(list(missing)),
                'overall_fit': 'Strong' if match_percentage >= 70 else 'Moderate' if match_percentage >= 50 else 'Developing'
            }

        except Job.DoesNotExist:
            logger.error(f"Job not found: {target_job_id}")
            return {'error': 'Job not found'}
        except Exception as e:
            logger.error(f"Skill gap analysis failed: {e}")
            return {'error': str(e)}

    def _generate_learning_recommendations(self, missing_skills: List[str]) -> List[Dict]:
        """Generate learning recommendations for missing skills"""
        recommendations = []

        for skill in missing_skills[:5]:  # Top 5 skills
            recommendations.append({
                'skill': skill,
                'priority': 'High' if missing_skills.index(skill) < 3 else 'Medium',
                'resources': [
                    {'type': 'Course', 'title': f'Learn {skill}'},
                    {'type': 'Project', 'title': f'Build with {skill}'},
                ]
            })

        return recommendations

    def predict_career_path(
        self,
        current_role: str,
        current_skills: List[str],
        years_experience: int
    ) -> Dict:
        """
        Predict potential career progression paths.

        Returns:
            {
                'next_roles': [...],
                'skills_to_develop': [...],
                'timeline': '2-3 years'
            }
        """
        try:
            # Use AI to predict career progression
            prompt = f"""Based on this profile, suggest 3 potential career progression paths:

Current Role: {current_role}
Current Skills: {', '.join(current_skills[:10])}
Years of Experience: {years_experience}

For each path, provide:
1. Target role
2. Skills needed
3. Estimated timeline
4. Key milestones

Format as JSON."""

            response = self.bedrock.generate_text(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
            )

            # Parse AI response
            import json
            try:
                career_paths = json.loads(response)
            except:
                # Fallback if JSON parsing fails
                career_paths = {
                    'paths': [
                        {
                            'target_role': 'Senior ' + current_role,
                            'skills_needed': ['Leadership', 'Architecture'],
                            'timeline': '2-3 years',
                            'milestones': ['Lead projects', 'Mentor juniors']
                        }
                    ]
                }

            return career_paths

        except Exception as e:
            logger.error(f"Career path prediction failed: {e}")
            return {'error': str(e)}

    def calculate_job_compatibility(
        self,
        user_id: str,
        job_id: str
    ) -> Dict:
        """
        Calculate comprehensive compatibility score between user and job.

        Returns:
            {
                'overall_score': 0.85,
                'breakdown': {
                    'skills': 0.90,
                    'experience': 0.80,
                    'location': 1.0,
                    'salary': 0.85,
                    'culture': 0.80
                },
                'recommendation': 'Highly Recommended'
            }
        """
        try:
            from apps.accounts.models import User

            user = User.objects.get(id=user_id)
            job = Job.objects.get(id=job_id)

            scores = {
                'skills': self._calculate_skill_score(user, job),
                'experience': self._calculate_experience_score(user, job),
                'location': self._calculate_location_score(user, job),
                'salary': self._calculate_salary_score(user, job),
            }

            overall = sum(scores.values()) / len(scores)

            recommendation = (
                'Highly Recommended' if overall >= 0.8 else
                'Recommended' if overall >= 0.6 else
                'Consider Applying' if overall >= 0.4 else
                'May Not Be Ideal'
            )

            return {
                'overall_score': round(overall, 2),
                'breakdown': {k: round(v, 2) for k, v in scores.items()},
                'recommendation': recommendation,
                'strengths': [k for k, v in scores.items() if v >= 0.8],
                'areas_to_improve': [k for k, v in scores.items() if v < 0.6]
            }

        except Exception as e:
            logger.error(f"Compatibility calculation failed: {e}")
            return {'error': str(e)}

    def _calculate_skill_score(self, user, job) -> float:
        """Calculate skill match score"""
        user_skills = set(
            skill.skill.name
            for skill in user.career_profile.career_user_skills.all()
        ) if hasattr(user, 'career_profile') else set()

        job_skills = set(skill.name for skill in job.required_skills.all())

        if not job_skills:
            return 0.5  # Neutral if no requirements

        matched = len(user_skills & job_skills)
        return min(matched / len(job_skills), 1.0)

    def _calculate_experience_score(self, user, job) -> float:
        """Calculate experience level match"""
        user_level = getattr(user.career_profile, 'career_stage', 'entry') if hasattr(user, 'career_profile') else 'entry'
        job_level = job.experience_level

        if user_level == job_level:
            return 1.0
        elif self._is_adjacent_exp_level(user_level, job_level):
            return 0.7
        else:
            return 0.4

    def _calculate_location_score(self, user, job) -> float:
        """Calculate location match"""
        # Simple check - can be enhanced with user preferences
        if job.work_arrangement == 'remote':
            return 1.0
        return 0.5  # Neutral if no preference data

    def _calculate_salary_score(self, user, job) -> float:
        """Calculate salary expectation match"""
        # Placeholder - would use user salary expectations
        if job.salary_max and job.salary_max > 0:
            return 0.8
        return 0.5  # Neutral if no salary data


# Singleton instance
job_matching_service = JobMatchingService()
