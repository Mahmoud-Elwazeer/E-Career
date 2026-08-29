"""
AI Candidate Ranking Service for Employers

This module provides AI-powered candidate ranking and shortlisting
functionality for employer job postings.
"""

import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from apps.jobs.models import Job
from apps.career.models import CareerUserSkill, CareerBrain
from apps.employers.models import JobApplication, CandidateRanking, KnockoutQuestion
from apps.intelligence.career_ai import career_ai_service as bedrock_service

logger = logging.getLogger(__name__)


class CandidateRankingService:
    """
    AI-powered candidate ranking service for employers.
    
    Provides:
    - Candidate ranking with AI-generated explanations
    - Automatic shortlist generation
    - Side-by-side candidate comparison
    """
    
    def __init__(self):
        self.bedrock = bedrock_service
    
    def rank_candidates(self, job_id: int, candidate_ids: List[int], employer=None) -> List[Dict]:
        """
        Rank candidates for a job using AI analysis.

        Args:
            job_id: The job ID to rank candidates for
            candidate_ids: List of candidate user IDs to rank
            employer: EmployerProfile instance (required for persisting rankings)

        Returns:
            List of ranking results with scores and explanations
        """
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return [{'error': f'Job {job_id} not found'}]

        results = []

        for candidate_id in candidate_ids:
            try:
                ranking = self._rank_single_candidate(job, candidate_id, employer=employer)
                results.append(ranking)
            except Exception as e:
                logger.error(f"Error ranking candidate {candidate_id} for job {job_id}: {e}")
                results.append({
                    'user_id': candidate_id,
                    'error': str(e),
                    'rank': None,
                    'score': 0,
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Add rank numbers
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return results
    
    def _rank_single_candidate(self, job: Job, candidate_id: int, employer=None) -> Dict:
        """
        Rank a single candidate for a job.
        
        Args:
            job: Job instance
            candidate_id: User ID of candidate
            
        Returns:
            Ranking dictionary with scores and explanations
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            candidate = User.objects.get(id=candidate_id)
        except User.DoesNotExist:
            return {
                'user_id': candidate_id,
                'error': 'Candidate not found',
                'rank': None,
                'score': 0,
            }
        
        # Get job requirements
        job_requirements = self._extract_job_requirements(job)
        
        # Get candidate profile
        candidate_profile = self._get_candidate_profile(candidate)
        
        # Calculate scores
        skill_match = self._calculate_skill_match(job_requirements, candidate_profile)
        experience_match = self._calculate_experience_match(job_requirements, candidate_profile)
        location_match = self._calculate_location_match(job_requirements, candidate_profile)
        salary_match = self._calculate_salary_match(job_requirements, candidate_profile)
        
        # Calculate overall score (weighted average)
        overall_score = (
            skill_match * 0.40 +
            experience_match * 0.30 +
            location_match * 0.15 +
            salary_match * 0.15
        )
        
        # Generate AI explanations
        explanations = self._generate_explanations(
            job=job,
            candidate=candidate,
            job_requirements=job_requirements,
            candidate_profile=candidate_profile,
            skill_match=skill_match,
            experience_match=experience_match,
            location_match=location_match,
            salary_match=salary_match,
        )
        
        # Check knockout questions
        knockout_passed, knockout_failures = self._check_knockout_questions(
            job, candidate, explanations
        )
        
        # Create or update ranking record
        ranking, _ = CandidateRanking.objects.update_or_create(
            job=job,
            user=candidate,
            employer=employer,
            defaults={
                'overall_score': overall_score,
                'skill_match_score': skill_match,
                'experience_score': experience_match,
                'education_score': 0.5,  # Placeholder
                'salary_expectation_score': salary_match,
                'knockout_passed': knockout_passed,
                'knockout_failures': knockout_failures,
                'explanations': explanations,
                'status': 'ranked',
            }
        )
        
        return {
            'user_id': candidate.id,
            'rank': None,  # Will be set after sorting
            'score': round(overall_score, 3),
            'skill_match_score': round(skill_match, 3),
            'experience_match_score': round(experience_match, 3),
            'location_match_score': round(location_match, 3),
            'salary_match_score': round(salary_match, 3),
            'match_reasons': explanations.get('match_reasons', []),
            'gaps': explanations.get('gaps', []),
            'knockout_passed': knockout_passed,
            'knockout_failures': knockout_failures,
            'ai_explanation': explanations.get('summary', ''),
        }
    
    def _extract_job_requirements(self, job: Job) -> Dict:
        """Extract job requirements from job description."""
        return {
            'required_skills': self._extract_skills_from_text(job.description),
            'required_experience_years': self._extract_experience_years(job.description),
            'required_education': self._extract_education(job.description),
            'location': job.location,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'remote_type': job.remote_type,
        }
    
    def _get_candidate_profile(self, candidate) -> Dict:
        """Get candidate profile from CareerBrain and CareerUserSkill."""
        profile = {
            'skills': {},
            'experience_years': 0,
            'education': [],
            'location': '',
            'salary_expectation': None,
        }
        
        # Get skills from CareerBrain
        try:
            career_brain = candidate.career_brain
            if career_brain and career_brain.skills:
                profile['skills'] = career_brain.skills
        except Exception:
            pass
        
        # Get skills from CareerUserSkill
        user_skills = CareerUserSkill.objects.filter(user=candidate)
        for us in user_skills:
            if us.skill.name not in profile['skills']:
                profile['skills'][us.skill.name] = {
                    'level': us.proficiency,
                    'verified': us.verified,
                    'years': us.years_experience,
                }
        
        # Get experience from career profile
        try:
            career_profile = candidate.career_profile
            profile['experience_years'] = career_profile.experience_years or 0
            profile['location'] = career_profile.cv_parsed_data.get('location', '')
            profile['salary_expectation'] = career_profile.target_salary_min
        except Exception:
            pass
        
        return profile
    
    def _calculate_skill_match(self, job_req: Dict, candidate: Dict) -> float:
        """Calculate skill match score (0-1)."""
        if not job_req.get('required_skills') or not candidate.get('skills'):
            return 0.5  # Default if no data
        
        required = set(job_req['required_skills'])
        candidate_skills = set(candidate['skills'].keys())
        
        if not required:
            return 1.0
        
        # Calculate overlap
        matched = required & candidate_skills
        match_ratio = len(matched) / len(required)
        
        # Bonus for having more skills than required
        extra_skills = len(candidate_skills - required)
        bonus = min(0.1, extra_skills * 0.02)
        
        return min(1.0, match_ratio + bonus)
    
    def _calculate_experience_match(self, job_req: Dict, candidate: Dict) -> float:
        """Calculate experience match score (0-1)."""
        required_years = job_req.get('required_experience_years', 0)
        candidate_years = candidate.get('experience_years', 0)
        
        if required_years == 0:
            return 1.0
        
        if candidate_years >= required_years:
            return min(1.0, 0.8 + (candidate_years - required_years) * 0.05)
        else:
            return candidate_years / required_years * 0.8
    
    def _calculate_location_match(self, job_req: Dict, candidate: Dict) -> float:
        """Calculate location match score (0-1)."""
        job_location = job_req.get('location', '').lower()
        candidate_location = candidate.get('location', '').lower()
        remote_type = job_req.get('remote_type', 'onsite')
        
        if remote_type == 'remote':
            return 1.0
        
        if not job_location or not candidate_location:
            return 0.5
        
        # Check for location match
        if job_location in candidate_location or candidate_location in job_location:
            return 1.0
        
        # Check for country match
        job_country = job_location.split(',')[-1].strip()
        candidate_country = candidate_location.split(',')[-1].strip()
        
        if job_country == candidate_country:
            return 0.8
        
        return 0.3
    
    def _calculate_salary_match(self, job_req: Dict, candidate: Dict) -> float:
        """Calculate salary expectation match score (0-1)."""
        salary_min = job_req.get('salary_min')
        salary_max = job_req.get('salary_max')
        candidate_expectation = candidate.get('salary_expectation')
        
        if not salary_min or not salary_max or not candidate_expectation:
            return 0.5  # Default if no data
        
        try:
            candidate_expectation = float(candidate_expectation)
            mid_salary = (salary_min + salary_max) / 2
            
            if salary_min <= candidate_expectation <= salary_max:
                # Perfect match
                return 1.0
            elif candidate_expectation < salary_min:
                # Under expectation
                return 0.7
            else:
                # Over expectation
                return 0.5
        except (ValueError, TypeError):
            return 0.5
    
    def _generate_explanations(
        self, job, candidate, job_requirements, candidate_profile,
        skill_match, experience_match, location_match, salary_match
    ) -> Dict:
        """Generate AI-powered explanations for ranking."""
        # Build prompt for AI explanation
        prompt = f"""أنت مستشار توظيف خبير. قم بتحليل توافق المرشح للوظيفة التالية:

الوظيفة: {job.title} في {job.company_name}
المتطلبات:
- المهارات المطلوبة: {', '.join(job_requirements.get('required_skills', [])[:5])}
- سنوات الخبرة: {job_requirements.get('required_experience_years', 0)}+
- الموقع: {job_requirements.get('location', 'غير محدد')}

المرشح: {candidate.email}
الملف:
- المهارات: {', '.join(list(candidate_profile.get('skills', {}).keys())[:5])}
- الخبرة: {candidate_profile.get('experience_years', 0)} سنوات
- الموقع: {candidate_profile.get('location', 'غير محدد')}

قم بإنشاء تحليل مختصر بالعربية يحتوي على:
1. أسباب التوافق (3-4 نقاط)
2. الفجوات المطلوبة (2-3 نقاط)
3. تقييم عام

أعد النتيجة بصيغة JSON فقط بدون أي نص إضافي:
{{
    "match_reasons": ["سبب 1", "سبب 2", "سبب 3"],
    "gaps": ["فجوة 1", "فجوة 2"],
    "summary": "تقييم عام مختصر"
}}"""

        try:
            if self.bedrock.is_available:
                response = self.bedrock.invoke_model(
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.3
                )
                
                # Parse JSON from response
                import json
                import re
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            # Fallback if Bedrock unavailable
            return self._generate_fallback_explanations(
                skill_match, experience_match, location_match, salary_match
            )
            
        except Exception as e:
            logger.error(f"Error generating explanations: {e}")
            return self._generate_fallback_explanations(
                skill_match, experience_match, location_match, salary_match
            )
    
    def _generate_fallback_explanations(
        self, skill_match, experience_match, location_match, salary_match
    ) -> Dict:
        """Generate fallback explanations without AI."""
        reasons = []
        gaps = []
        
        if skill_match >= 0.8:
            reasons.append("مطابقة ممتازة للمهارات المطلوبة")
        elif skill_match >= 0.6:
            reasons.append("مطابقة جيدة للمهارات الأساسية")
        else:
            gaps.append("تحتاج لتطوير بعض المهارات المطلوبة")
        
        if experience_match >= 0.8:
            reasons.append("خبرة كافية أو تجاوزت المتطلبات")
        elif experience_match >= 0.5:
            reasons.append("خبرة قريبة من المتطلبات")
        else:
            gaps.append("تحتاج لسنوات خبرة إضافية")
        
        if location_match >= 0.8:
            reasons.append("مطابقة جيدة للموقع أو متاح للعمل عن بُعد")
        
        if salary_match >= 0.8:
            reasons.append("توقعات الراتب متوافقة مع الميزانية")
        
        return {
            "match_reasons": reasons[:3],
            "gaps": gaps[:2],
            "summary": f"المرشح متوافق بنسبة {skill_match*100:.0f}% مع متطلبات الوظيفة."
        }
    
    def _check_knockout_questions(
        self, job: Job, candidate, explanations: Dict
    ) -> tuple:
        """Check if candidate passes knockout questions."""
        from apps.employers.models import EmployerProfile
        
        try:
            employer_profile = EmployerProfile.objects.get(
                user=job.employer.user
            )
        except EmployerProfile.DoesNotExist:
            return True, []
        
        knockout_questions = KnockoutQuestion.objects.filter(
            employer=employer_profile,
            is_active=True
        )
        
        failures = []
        for question in knockout_questions:
            passed = self._evaluate_knockout_question(question, candidate, explanations)
            if not passed:
                failures.append({
                    'question': question.question_text,
                    'required': question.required_answer,
                    'candidate_response': 'Not evaluated',
                })
        
        return len(failures) == 0, failures
    
    def _evaluate_knockout_question(
        self, question: KnockoutQuestion, candidate, explanations: Dict
    ) -> bool:
        """Evaluate a single knockout question."""
        # This is a placeholder - implement actual evaluation logic
        # based on question type and candidate data
        return True
    
    def generate_shortlist(self, job_id: int, max_candidates: int = 10, employer=None) -> List[Dict]:
        """
        Auto-generate a shortlist of top candidates for a job.
        
        Args:
            job_id: The job ID
            max_candidates: Maximum number of candidates to return
            
        Returns:
            List of top candidates with scores and explanations
        """
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return [{'error': f'Job {job_id} not found'}]
        
        # Get all applications for this job
        applications = JobApplication.objects.filter(job=job).select_related('user')
        
        if not applications:
            return []
        
        # Get candidate IDs
        candidate_ids = [app.user.id for app in applications]
        
        # Rank all candidates
        rankings = self.rank_candidates(job_id, candidate_ids, employer=employer)

        # Sort by score and limit
        rankings.sort(key=lambda x: x.get('score', 0), reverse=True)

        return rankings[:max_candidates]
    
    def compare_candidates(
        self, job_id: int, candidate_ids: List[int], employer=None
    ) -> Dict[str, Any]:
        """
        Generate side-by-side comparison of candidates.

        Args:
            job_id: The job ID
            candidate_ids: List of candidate user IDs to compare
            employer: EmployerProfile instance

        Returns:
            Comparison dictionary with scores and explanations
        """
        rankings = self.rank_candidates(job_id, candidate_ids, employer=employer)
        
        # Build comparison summary
        comparison = {
            'job_id': job_id,
            'candidates': rankings,
            'summary': self._generate_comparison_summary(rankings),
        }
        
        return comparison
    
    def _generate_comparison_summary(self, rankings: List[Dict]) -> str:
        """Generate a summary of candidate comparisons."""
        if not rankings:
            return "لا يوجد مرشحين كافيين للمقارنة."
        
        top_candidate = rankings[0]
        summary = f"أفضل مرشح: {top_candidate.get('user_id', 'Unknown')} "
        summary += f"بدرجة {top_candidate.get('score', 0):.0%}"
        
        if len(rankings) > 1:
            second = rankings[1]
            diff = top_candidate.get('score', 0) - second.get('score', 0)
            summary += f" (متفوق بـ {diff:.0%} عن المرشح الثاني)"
        
        return summary
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from job description text."""
        # Simple keyword extraction - can be enhanced with NLP
        common_skills = [
            'python', 'javascript', 'react', 'node.js', 'java', 'c++', 'sql',
            'aws', 'docker', 'kubernetes', 'git', 'agile', 'scrum', 'linux',
            'html', 'css', 'typescript', 'angular', 'vue', 'flutter', 'swift',
            'android', 'ios', 'machine learning', 'data analysis', 'project management'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills[:10]
    
    def _extract_experience_years(self, text: str) -> int:
        """Extract required experience years from job description."""
        import re
        
        patterns = [
            r'(\d+)\+?\s*سنوات?\s*خبرة?',
            r'(\d+)\+?\s*years?\s*experience?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return 0
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education requirements from job description."""
        education_terms = [
            'بكالوريوس', 'ماجستير', 'دكتوراه', 'bachelor', 'master', 'phd',
            'degree', 'certificate', 'diploma'
        ]
        
        found = []
        text_lower = text.lower()
        
        for term in education_terms:
            if term in text_lower:
                found.append(term)
        
        return found


# Singleton instance
ranking_service = CandidateRankingService()