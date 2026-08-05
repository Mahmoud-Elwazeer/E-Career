"""
Talent Scoring Engine

This module provides a unified scoring engine for calculating multi-dimensional
talent scores with explainability and historical tracking.

Dimensions:
1. Skill Score (25%)
2. Experience Score (20%)
3. Education Score (15%)
4. Portfolio Score (15%)
5. Growth Score (15%)
6. Communication Score (10%)
7. Interview Score (15%)
8. AI Confidence (affects overall confidence)

Weighted Composite: Skill 25% + Experience 20% + Portfolio 15% + Interview 15% + Growth 15% + Communication 10%
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from decimal import Decimal

from django.db.models import QuerySet, Count, Avg, Max, Min
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ScoreResult:
    """
    Result of a score calculation.
    
    Attributes:
        value: The score value (0-1)
        confidence: Confidence in the score (0-1)
        grade: Letter grade (A-F)
        trend: Trend direction (improving/stable/declining)
        evidence: List of evidence items supporting the score
        explanation: Natural language explanation
        actions: Recommended actions to improve
        breakdown: Detailed breakdown by sub-factors
    """
    value: float
    confidence: float = 0.5
    grade: str = "C"
    trend: str = "stable"
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    explanation: str = ""
    actions: List[Dict[str, str]] = field(default_factory=list)
    breakdown: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "value": round(self.value, 3),
            "confidence": round(self.confidence, 3),
            "grade": self.grade,
            "trend": self.trend,
            "evidence": self.evidence,
            "explanation": self.explanation,
            "actions": self.actions,
            "breakdown": self.breakdown,
        }


# ============================================================================
# Scoring Engine
# ============================================================================

class ScoringEngine:
    """
    Unified scoring engine for calculating multi-dimensional talent scores.
    
    Provides consistent scoring across all dimensions with explainability
    and historical tracking.
    """
    
    def __init__(self, user):
        """
        Initialize the scoring engine for a specific user.
        
        Args:
            user: Django User instance
        """
        self.user = user
        self._profile = None
        self._skills = None
        self._learning = None
        self._interviews = None
        self._github_data = None
        self._portfolio_data = None
        self._job_skills = None
    
    # =========================================================================
    # Property getters for data access
    # =========================================================================
    
    @property
    def profile(self):
        """Get user's career profile."""
        if self._profile is None:
            from apps.career.models import CareerProfile
            try:
                self._profile = CareerProfile.objects.get(user=self.user)
            except CareerProfile.DoesNotExist:
                self._profile = None
        return self._profile
    
    @property
    def skills(self) -> QuerySet:
        """Get user's skills with proficiency."""
        if self._skills is None:
            from apps.career.models import CareerUserSkill
            self._skills = CareerUserSkill.objects.filter(user=self.user).select_related(
                'skill'
            )
        return self._skills
    
    @property
    def learning(self) -> QuerySet:
        """Get user's learning history."""
        if self._learning is None:
            from apps.career.models import CareerLearning
            self._learning = CareerLearning.objects.filter(user=self.user)
        return self._learning
    
    @property
    def interviews(self) -> QuerySet:
        """Get user's interview sessions."""
        if self._interviews is None:
            from apps.career.models import InterviewSession
            self._interviews = InterviewSession.objects.filter(user=self.user)
        return self._interviews
    
    @property
    def github_data(self) -> Dict[str, Any]:
        """Get user's GitHub data."""
        if self._github_data is None:
            if self.profile and self.profile.github_data:
                self._github_data = self.profile.github_data
            else:
                self._github_data = {}
        return self._github_data
    
    @property
    def portfolio_data(self) -> Dict[str, Any]:
        """Get user's portfolio data."""
        if self._portfolio_data is None:
            if self.profile and self.profile.portfolio_analysis:
                self._portfolio_data = self.profile.portfolio_analysis
            else:
                self._portfolio_data = {}
        return self._portfolio_data
    
    @property
    def job_skills(self) -> Dict[str, float]:
        """Get skill demand from job market."""
        if self._job_skills is None:
            # Get skill frequency from job postings
            from apps.jobs.models import JobTag
            skill_counts = JobTag.objects.values('tag_id').annotate(
                count=Count('id')
            ).order_by('-count')[:100]
            self._job_skills = {str(s['tag_id']): s['count'] for s in skill_counts}
        return self._job_skills
    
    # =========================================================================
    # Score Calculation Methods
    # =========================================================================
    
    def calculate_skill_score(self) -> ScoreResult:
        """
        Calculate skill score based on:
        - Technical depth (verified skills × proficiency)
        - Breadth (number × diversity)
        - Market demand (skill frequency in job postings)
        - Verification level (% verified)
        
        Returns:
            ScoreResult with skill score and explanation
        """
        total_skills = self.skills.count()
        verified_skills = self.skills.filter(verified=True)
        verified_count = verified_skills.count()
        
        # Calculate average proficiency
        proficiency_weights = {
            'beginner': 0.25,
            'intermediate': 0.5,
            'advanced': 0.75,
            'expert': 1.0,
        }
        
        total_proficiency = sum(
            proficiency_weights.get(s.proficiency, 0.5)
            for s in self.skills
        )
        avg_proficiency = total_proficiency / max(total_skills, 1)
        
        # Technical depth score
        technical_depth = (verified_count / max(total_skills, 1)) * 0.5 + avg_proficiency * 0.5
        
        # Breadth score (number of skills)
        skill_count_score = min(1.0, total_skills / 15)
        
        # Market demand score
        if self.job_skills:
            user_skill_ids = [str(s.skill_id) for s in self.skills]
            demand_scores = [
                self.job_skills.get(sid, 0) for sid in user_skill_ids
            ]
            avg_demand = sum(demand_scores) / max(len(demand_scores), 1)
            # Normalize demand score (assuming max demand ~1000)
            market_demand = min(1.0, avg_demand / 1000)
        else:
            market_demand = 0.5
        
        # Verification level
        verification_level = verified_count / max(total_skills, 1)
        
        # Calculate weighted score
        skill_score = (
            technical_depth * 0.35 +
            skill_count_score * 0.25 +
            market_demand * 0.25 +
            verification_level * 0.15
        )
        
        # Build evidence
        evidence = []
        if verified_count > 0:
            evidence.append({
                "type": "verified_skills",
                "count": verified_count,
                "description": f"{verified_count} skills verified through assessments or GitHub"
            })
        if total_skills > 10:
            evidence.append({
                "type": "skill_breadth",
                "count": total_skills,
                "description": f"Strong skill breadth with {total_skills} skills"
            })
        if avg_proficiency >= 0.7:
            evidence.append({
                "type": "proficiency",
                "level": "advanced",
                "description": "High average proficiency across skills"
            })
        
        # Build explanation
        explanation = (
            f"You have {total_skills} skills with {verified_count} verified. "
            f"Average proficiency is {'high' if avg_proficiency >= 0.7 else 'moderate'}."
        )
        
        # Build actions
        actions = []
        if verification_level < 0.5:
            actions.append({
                "type": "verification",
                "title": "Verify More Skills",
                "description": "Get skills verified through assessments or GitHub integration",
                "priority": "high"
            })
        if total_skills < 10:
            actions.append({
                "type": "skill_development",
                "title": "Expand Skill Range",
                "description": "Learn 5-10 more skills to improve your profile",
                "priority": "medium"
            })
        
        # Calculate confidence
        confidence = min(0.9, 0.5 + (total_skills * 0.05) + (verified_count * 0.03))
        
        # Determine grade
        if skill_score >= 0.8:
            grade = "A"
        elif skill_score >= 0.65:
            grade = "B"
        elif skill_score >= 0.5:
            grade = "C"
        elif skill_score >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(skill_score, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "technical_depth": round(technical_depth, 3),
                "skill_breadth": round(skill_count_score, 3),
                "market_demand": round(market_demand, 3),
                "verification_level": round(verification_level, 3),
            }
        )
    
    def calculate_experience_score(self) -> ScoreResult:
        """
        Calculate experience score based on:
        - Years relevant to target role
        - Career progression rate
        - Company quality tier
        - Responsibility growth
        
        Returns:
            ScoreResult with experience score and explanation
        """
        if not self.profile:
            return ScoreResult(value=0.0, confidence=0.0, grade="F")
        
        experience_years = self.profile.experience_years or 0
        current_role = self.profile.current_role or ""
        current_company = self.profile.current_company or ""
        target_roles = self.profile.target_roles or []
        
        # Calculate relevant experience
        # (simplified - would need job history for accurate calculation)
        relevant_experience = min(experience_years, 15)
        
        # Career progression (simplified)
        # Would need job history to calculate actual progression
        progression_score = 0.5 + min(0.3, experience_years * 0.03)
        
        # Company quality (placeholder - would need company data)
        company_quality = 0.5
        
        # Responsibility growth (placeholder)
        responsibility_growth = 0.5
        
        # Calculate weighted score
        experience_score = (
            (relevant_experience / 15) * 0.4 +
            progression_score * 0.2 +
            company_quality * 0.2 +
            responsibility_growth * 0.2
        )
        
        # Build evidence
        evidence = []
        if experience_years >= 5:
            evidence.append({
                "type": "experience_years",
                "years": experience_years,
                "description": "Significant experience in the field"
            })
        if current_role:
            evidence.append({
                "type": "current_role",
                "role": current_role,
                "description": f"Currently working as {current_role}"
            })
        
        # Build explanation
        explanation = (
            f"You have {experience_years} years of experience. "
            f"Current role: {current_role or 'Not specified'}."
        )
        
        # Build actions
        actions = []
        if experience_years < 3:
            actions.append({
                "type": "experience_building",
                "title": "Gain More Experience",
                "description": "Consider internships or junior roles to build experience",
                "priority": "high"
            })
        if not current_role:
            actions.append({
                "type": "profile_completion",
                "title": "Update Current Role",
                "description": "Add your current job title for better scoring",
                "priority": "medium"
            })
        
        # Calculate confidence
        confidence = 0.5 + min(0.4, experience_years * 0.03)
        
        # Determine grade
        if experience_score >= 0.8:
            grade = "A"
        elif experience_score >= 0.65:
            grade = "B"
        elif experience_score >= 0.5:
            grade = "C"
        elif experience_score >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(experience_score, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "relevant_experience": round(relevant_experience / 15, 3),
                "career_progression": round(progression_score, 3),
                "company_quality": round(company_quality, 3),
                "responsibility_growth": round(responsibility_growth, 3),
            }
        )
    
    def calculate_education_score(self) -> ScoreResult:
        """
        Calculate education score based on:
        - Degrees relevance
        - Certifications count + relevance
        - Recent learning activity
        
        Returns:
            ScoreResult with education score and explanation
        """
        learning_count = self.learning.count()
        completed_learning = self.learning.filter(completed_at__isnull=False)
        recent_learning = completed_learning.filter(
            completed_at__gte=timezone.now().date() - timedelta(days=180)
        )
        
        # Calculate degree relevance (placeholder - would need degree data)
        degree_relevance = 0.5
        
        # Certifications count
        certification_count = completed_learning.count()
        certification_score = min(1.0, certification_count / 5)
        
        # Recent learning activity
        recent_activity_score = min(1.0, recent_learning.count() / 2)
        
        # Calculate weighted score
        education_score = (
            degree_relevance * 0.3 +
            certification_score * 0.4 +
            recent_activity_score * 0.3
        )
        
        # Build evidence
        evidence = []
        if certification_count > 0:
            evidence.append({
                "type": "certifications",
                "count": certification_count,
                "description": f"{certification_count} certifications completed"
            })
        if recent_learning_count := recent_learning.count() > 0:
            evidence.append({
                "type": "recent_learning",
                "count": recent_learning_count,
                "description": "Active learning in the last 6 months"
            })
        
        # Build explanation
        explanation = (
            f"You have completed {certification_count} courses/certifications. "
            f"{'Recent learning activity detected.' if recent_learning_count > 0 else 'Consider recent learning to improve your score.'}"
        )
        
        # Build actions
        actions = []
        if certification_count < 2:
            actions.append({
                "type": "certification",
                "title": "Earn More Certifications",
                "description": "Complete 2-3 certifications in your target field",
                "priority": "medium"
            })
        if recent_learning_count == 0:
            actions.append({
                "type": "learning",
                "title": "Start Learning",
                "description": "Enroll in a course to demonstrate learning velocity",
                "priority": "high"
            })
        
        # Calculate confidence
        confidence = 0.5 + min(0.4, certification_count * 0.05)
        
        # Determine grade
        if education_score >= 0.8:
            grade = "A"
        elif education_score >= 0.65:
            grade = "B"
        elif education_score >= 0.5:
            grade = "C"
        elif education_score >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(education_score, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "degree_relevance": round(degree_relevance, 3),
                "certification_count": round(certification_score, 3),
                "recent_activity": round(recent_activity_score, 3),
            }
        )
    
    def calculate_portfolio_score(self) -> ScoreResult:
        """
        Calculate portfolio score based on:
        - GitHub activity (commits, repos, contributions)
        - Project quality (stars, completeness)
        - Technology diversity
        - Recency (active in last 90 days?)
        
        Returns:
            ScoreResult with portfolio score and explanation
        """
        github_data = self.github_data
        portfolio_url = self.profile.portfolio_url if self.profile else None
        
        # GitHub activity score
        github_activity_score = 0.0
        if github_data:
            repos = github_data.get('repositories', [])
            commits = github_data.get('total_commits', 0)
            contributions = github_data.get('contributions', 0)
            recent_activity = github_data.get('last_90_days', False)
            
            # Calculate activity score
            repo_score = min(1.0, len(repos) / 10)
            commit_score = min(1.0, commits / 500)
            contribution_score = min(1.0, contributions / 1000)
            
            github_activity_score = (
                repo_score * 0.3 +
                commit_score * 0.3 +
                contribution_score * 0.3 +
                (0.1 if recent_activity else 0)
            )
        
        # Project quality score
        project_quality_score = 0.0
        if github_data:
            repos = github_data.get('repositories', [])
            if repos:
                avg_stars = sum(r.get('stars', 0) for r in repos) / len(repos)
                project_quality_score = min(1.0, avg_stars / 50)
        
        # Technology diversity
        tech_diversity_score = 0.0
        if github_data:
            languages = github_data.get('languages', [])
            tech_diversity_score = min(1.0, len(languages) / 10)
        
        # Portfolio URL presence
        portfolio_score = 0.5 if portfolio_url else 0.0
        
        # Calculate weighted score
        portfolio_score = (
            github_activity_score * 0.35 +
            project_quality_score * 0.25 +
            tech_diversity_score * 0.25 +
            portfolio_score * 0.15
        )
        
        # Build evidence
        evidence = []
        if github_data:
            repos = github_data.get('repositories', [])
            evidence.append({
                "type": "github_repos",
                "count": len(repos),
                "description": f"{len(repos)} GitHub repositories"
            })
            commits = github_data.get('total_commits', 0)
            if commits > 100:
                evidence.append({
                    "type": "github_commits",
                    "count": commits,
                    "description": f"{commits} GitHub commits"
                })
        if portfolio_url:
            evidence.append({
                "type": "portfolio",
                "url": portfolio_url,
                "description": "Personal portfolio/website present"
            })
        
        # Build explanation
        if github_data:
            repos = github_data.get('repositories', [])
            commits = github_data.get('total_commits', 0)
            explanation = (
                f"GitHub profile shows {len(repos)} repositories with {commits} commits. "
                f"{'Active in last 90 days.' if github_data.get('last_90_days') else 'No recent activity detected.'}"
            )
        else:
            explanation = "No GitHub data available. Link your GitHub for portfolio scoring."
        
        # Build actions
        actions = []
        if not github_data:
            actions.append({
                "type": "github_link",
                "title": "Link GitHub Profile",
                "description": "Connect your GitHub for automatic portfolio analysis",
                "priority": "high"
            })
        if github_data and not github_data.get('last_90_days', False):
            actions.append({
                "type": "github_activity",
                "title": "Increase GitHub Activity",
                "description": "Make regular commits to demonstrate active development",
                "priority": "medium"
            })
        
        # Calculate confidence
        confidence = 0.5
        if github_data:
            confidence = min(0.9, 0.5 + len(github_data.get('repositories', [])) * 0.05)
        
        # Determine grade
        if portfolio_score >= 0.8:
            grade = "A"
        elif portfolio_score >= 0.65:
            grade = "B"
        elif portfolio_score >= 0.5:
            grade = "C"
        elif portfolio_score >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(portfolio_score, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "github_activity": round(github_activity_score, 3),
                "project_quality": round(project_quality_score, 3),
                "tech_diversity": round(tech_diversity_score, 3),
                "portfolio_url": round(portfolio_score * 0.15 / 0.15 if portfolio_score > 0 else 0, 3),
            }
        )
    
    def calculate_growth_score(self) -> ScoreResult:
        """
        Calculate growth score based on:
        - Learning velocity (courses/quarter)
        - Skill acquisition rate (new skills/month)
        - Certification progress
        - Goal completion rate
        
        Returns:
            ScoreResult with growth score and explanation
        """
        learning = self.learning
        completed_learning = learning.filter(completed_at__isnull=False)
        
        # Learning velocity (courses per quarter)
        # Calculate courses in last 365 days
        year_ago = timezone.now().date() - timedelta(days=365)
        recent_learning = completed_learning.filter(completed_at__gte=year_ago)
        courses_per_year = recent_learning.count()
        courses_per_quarter = courses_per_year / 4
        
        learning_velocity_score = min(1.0, courses_per_quarter / 3)
        
        # Skill acquisition rate
        # Calculate new skills added in last 365 days
        from apps.career.models import CareerUserSkill
        skills = CareerUserSkill.objects.filter(
            user=self.user,
            created_at__gte=year_ago
        )
        skills_per_month = skills.count() / 12
        skill_acquisition_score = min(1.0, skills_per_month / 2)
        
        # Certification progress
        completed_certifications = completed_learning.count()
        certification_progress_score = min(1.0, completed_certifications / 5)
        
        # Goal completion rate (placeholder - would need goal data)
        goal_completion_score = 0.5
        
        # Calculate weighted score
        growth_score = (
            learning_velocity_score * 0.35 +
            skill_acquisition_score * 0.30 +
            certification_progress_score * 0.20 +
            goal_completion_score * 0.15
        )
        
        # Build evidence
        evidence = []
        if courses_per_year > 0:
            evidence.append({
                "type": "learning_velocity",
                "courses": courses_per_year,
                "description": f"{courses_per_year} courses completed in the last year"
            })
        if skills.count() > 0:
            evidence.append({
                "type": "skill_acquisition",
                "count": skills.count(),
                "description": f"{skills.count()} new skills acquired in the last year"
            })
        
        # Build explanation
        explanation = (
            f"You've completed {courses_per_year} courses in the last year. "
            f"Learning velocity: {courses_per_quarter:.1f} courses per quarter."
        )
        
        # Build actions
        actions = []
        if courses_per_quarter < 1:
            actions.append({
                "type": "learning_velocity",
                "title": "Increase Learning Velocity",
                "description": "Aim for 3+ courses per quarter to improve your growth score",
                "priority": "high"
            })
        if skills.count() < 2:
            actions.append({
                "type": "skill_acquisition",
                "title": "Learn New Skills",
                "description": "Acquire 2+ new skills in the next month",
                "priority": "medium"
            })
        
        # Calculate confidence
        confidence = 0.5 + min(0.4, courses_per_year * 0.02)
        
        # Determine grade
        if growth_score >= 0.8:
            grade = "A"
        elif growth_score >= 0.65:
            grade = "B"
        elif growth_score >= 0.5:
            grade = "C"
        elif growth_score >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(growth_score, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "learning_velocity": round(learning_velocity_score, 3),
                "skill_acquisition": round(skill_acquisition_score, 3),
                "certification_progress": round(certification_progress_score, 3),
                "goal_completion": round(goal_completion_score, 3),
            }
        )
    
    def calculate_communication_score(self) -> ScoreResult:
        """
        Calculate communication score based on:
        - CV clarity and structure (Haiku evaluation)
        - Profile writing quality
        
        Returns:
            ScoreResult with communication score and explanation
        """
        if not self.profile:
            return ScoreResult(value=0.0, confidence=0.0, grade="F")
        
        cv_parsed_data = self.profile.cv_parsed_data or {}
        cv_text = cv_parsed_data.get('text', '') or ''
        
        # CV clarity score (placeholder - would need NLP analysis)
        cv_clarity_score = 0.5
        
        # Profile completeness
        profile_completeness = self.profile.completeness_score or 0.0
        
        # Calculate weighted score
        communication_score = (
            cv_clarity_score * 0.5 +
            profile_completeness * 0.5
        )
        
        # Build evidence
        evidence = []
        if cv_text:
            evidence.append({
                "type": "cv_parsed",
                "length": len(cv_text),
                "description": "CV text extracted and analyzed"
            })
        if profile_completeness > 0.5:
            evidence.append({
                "type": "profile_completeness",
                "score": round(profile_completeness, 2),
                "description": "Profile is well-completed"
            })
        
        # Build explanation
        explanation = (
            f"CV analysis complete. Profile completeness: {profile_completeness:.0%}."
        )
        
        # Build actions
        actions = []
        if profile_completeness < 0.5:
            actions.append({
                "type": "profile_completion",
                "title": "Complete Your Profile",
                "description": "Fill in missing profile information for better communication score",
                "priority": "high"
            })
        if not cv_text:
            actions.append({
                "type": "cv_upload",
                "title": "Upload CV",
                "description": "Upload your CV for automatic skill extraction and analysis",
                "priority": "medium"
            })
        
        # Calculate confidence
        confidence = 0.5 + min(0.4, profile_completeness * 0.5)
        
        # Determine grade
        if communication_score >= 0.8:
            grade = "A"
        elif communication_score >= 0.65:
            grade = "B"
        elif communication_score >= 0.5:
            grade = "C"
        elif communication_score >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(communication_score, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "cv_clarity": round(cv_clarity_score, 3),
                "profile_completeness": round(profile_completeness, 3),
            }
        )
    
    def calculate_interview_score(self) -> ScoreResult:
        """
        Calculate interview score based on:
        - Interview session performance
        - Answer quality
        - Technical proficiency
        
        Returns:
            ScoreResult with interview score and explanation
        """
        interviews = self.interviews
        completed_interviews = interviews.filter(overall_score__isnull=False)
        
        if not completed_interviews.exists():
            return ScoreResult(
                value=0.0,
                confidence=0.3,
                grade="F",
                evidence=[],
                explanation="No interview data available. Complete interviews to improve your score.",
                actions=[{
                    "type": "interview",
                    "title": "Complete Interviews",
                    "description": "Take interviews to build your interview score",
                    "priority": "high"
                }],
                breakdown={}
            )
        
        # Calculate average interview score
        avg_score = completed_interviews.aggregate(
            avg_score=Avg('overall_score')
        )['avg_score'] or 0.0
        
        # Calculate interview count score
        interview_count_score = min(1.0, completed_interviews.count() / 5)
        
        # Calculate score
        interview_score = (avg_score * 0.7 + interview_count_score * 0.3)
        
        # Build evidence
        evidence = []
        evidence.append({
            "type": "interview_count",
            "count": completed_interviews.count(),
            "description": f"{completed_interviews.count()} completed interviews"
        })
        evidence.append({
            "type": "average_score",
            "score": round(avg_score, 2),
            "description": f"Average interview score: {avg_score:.0%}"
        })
        
        # Build explanation
        explanation = (
            f"You have completed {completed_interviews.count()} interviews "
            f"with an average score of {avg_score:.0%}."
        )
        
        # Build actions
        actions = []
        if completed_interviews.count() < 3:
            actions.append({
                "type": "interview_practice",
                "title": "Practice More Interviews",
                "description": "Complete 2-3 more interviews to build confidence",
                "priority": "high"
            })
        
        # Calculate confidence
        confidence = 0.3 + min(0.6, completed_interviews.count() * 0.1)
        
        # Determine grade
        if interview_score >= 0.8:
            grade = "A"
        elif interview_score >= 0.65:
            grade = "B"
        elif interview_score >= 0.5:
            grade = "C"
        elif interview_score >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(interview_score, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "average_score": round(avg_score, 3),
                "interview_count": round(interview_count_score, 3),
            }
        )
    
    def calculate_ai_confidence(self) -> ScoreResult:
        """
        Calculate AI confidence score based on:
        - Data completeness
        - Verification level
        - Consistency (no contradictions)
        
        Returns:
            ScoreResult with AI confidence score and explanation
        """
        # Data completeness
        profile = self.profile
        if not profile:
            return ScoreResult(
                value=0.0,
                confidence=0.0,
                grade="F",
                evidence=[],
                explanation="No profile data available.",
                actions=[{
                    "type": "profile_creation",
                    "title": "Create Your Profile",
                    "description": "Complete your career profile for scoring",
                    "priority": "high"
                }],
                breakdown={}
            )
        
        # Calculate data completeness
        completeness = profile.completeness_score or 0.0
        
        # Verification level
        verified_skills = self.skills.filter(verified=True).count()
        total_skills = self.skills.count()
        verification_level = verified_skills / max(total_skills, 1)
        
        # Consistency check (placeholder - would need contradiction detection)
        consistency_score = 0.8  # Default high consistency
        
        # Calculate weighted score
        ai_confidence = (
            completeness * 0.4 +
            verification_level * 0.3 +
            consistency_score * 0.3
        )
        
        # Build evidence
        evidence = []
        evidence.append({
            "type": "data_completeness",
            "score": round(completeness, 2),
            "description": f"Profile completeness: {completeness:.0%}"
        })
        evidence.append({
            "type": "verification_level",
            "score": round(verification_level, 2),
            "description": f"{verified_skills}/{total_skills} skills verified"
        })
        
        # Build explanation
        explanation = (
            f"AI confidence based on {completeness:.0%} profile completeness "
            f"and {verification_level:.0%} skill verification."
        )
        
        # Build actions
        actions = []
        if completeness < 0.5:
            actions.append({
                "type": "profile_completion",
                "title": "Complete Your Profile",
                "description": "Fill in all profile fields for better AI confidence",
                "priority": "high"
            })
        if verification_level < 0.5:
            actions.append({
                "type": "skill_verification",
                "title": "Verify More Skills",
                "description": "Get skills verified through assessments or GitHub",
                "priority": "medium"
            })
        
        # Calculate confidence
        confidence = ai_confidence
        
        # Determine grade
        if ai_confidence >= 0.8:
            grade = "A"
        elif ai_confidence >= 0.65:
            grade = "B"
        elif ai_confidence >= 0.5:
            grade = "C"
        elif ai_confidence >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(ai_confidence, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "data_completeness": round(completeness, 3),
                "verification_level": round(verification_level, 3),
                "consistency": round(consistency_score, 3),
            }
        )
    
    # =========================================================================
    # Composite Score Calculation
    # =========================================================================
    
    def calculate_composite_score(self) -> ScoreResult:
        """
        Calculate composite career score as weighted average of all dimensions.
        
        Weights:
        - Skill: 25%
        - Experience: 20%
        - Portfolio: 15%
        - Interview: 15%
        - Growth: 15%
        - Communication: 10%
        
        Returns:
            ScoreResult with composite score and explanation
        """
        # Calculate all dimension scores
        skill_result = self.calculate_skill_score()
        experience_result = self.calculate_experience_score()
        portfolio_result = self.calculate_portfolio_score()
        interview_result = self.calculate_interview_score()
        growth_result = self.calculate_growth_score()
        communication_result = self.calculate_communication_score()
        
        # Weighted average
        composite_score = (
            skill_result.value * 0.25 +
            experience_result.value * 0.20 +
            portfolio_result.value * 0.15 +
            interview_result.value * 0.15 +
            growth_result.value * 0.15 +
            communication_result.value * 0.10
        )
        
        # Build evidence
        evidence = [
            skill_result.evidence,
            experience_result.evidence,
            portfolio_result.evidence,
            interview_result.evidence,
            growth_result.evidence,
            communication_result.evidence,
        ]
        
        # Build explanation
        explanation = (
            f"Your composite career score is {composite_score:.0%}. "
            f"Top dimensions: Skill ({skill_result.value:.0%}), "
            f"Experience ({experience_result.value:.0%}), "
            f"Portfolio ({portfolio_result.value:.0%})."
        )
        
        # Build actions
        actions = []
        actions.extend(skill_result.actions)
        actions.extend(experience_result.actions)
        actions.extend(portfolio_result.actions)
        
        # Calculate confidence
        confidence = (
            skill_result.confidence * 0.25 +
            experience_result.confidence * 0.20 +
            portfolio_result.confidence * 0.15 +
            interview_result.confidence * 0.15 +
            growth_result.confidence * 0.15 +
            communication_result.confidence * 0.10
        )
        
        # Determine grade
        if composite_score >= 0.8:
            grade = "A"
        elif composite_score >= 0.65:
            grade = "B"
        elif composite_score >= 0.5:
            grade = "C"
        elif composite_score >= 0.35:
            grade = "D"
        else:
            grade = "F"
        
        return ScoreResult(
            value=round(composite_score, 3),
            confidence=round(confidence, 3),
            grade=grade,
            evidence=evidence,
            explanation=explanation,
            actions=actions,
            breakdown={
                "skill_score": skill_result.to_dict(),
                "experience_score": experience_result.to_dict(),
                "portfolio_score": portfolio_result.to_dict(),
                "interview_score": interview_result.to_dict(),
                "growth_score": growth_result.to_dict(),
                "communication_score": communication_result.to_dict(),
            }
        )
    
    def calculate_all_scores(self) -> Dict[str, ScoreResult]:
        """
        Calculate all dimension scores at once.
        
        Returns:
            Dictionary mapping dimension names to ScoreResults
        """
        return {
            "skill_score": self.calculate_skill_score(),
            "experience_score": self.calculate_experience_score(),
            "education_score": self.calculate_education_score(),
            "portfolio_score": self.calculate_portfolio_score(),
            "growth_score": self.calculate_growth_score(),
            "communication_score": self.calculate_communication_score(),
            "interview_score": self.calculate_interview_score(),
            "ai_confidence": self.calculate_ai_confidence(),
        }
    
    def calculate_and_save(self) -> Dict[str, Any]:
        """
        Calculate all scores and save to the TalentScore model.
        
        Returns:
            Dictionary with all scores and explanations
        """
        from apps.career.models import TalentScore
        
        # Calculate all scores
        all_scores = self.calculate_all_scores()
        composite_result = self.calculate_composite_score()
        ai_confidence_result = self.calculate_ai_confidence()
        
        # Get or create talent score
        talent_score, created = TalentScore.objects.get_or_create(
            user=self.user,
            defaults={
                'overall_score': composite_result.value,
                'skill_score': all_scores['skill_score'].value,
                'experience_score': all_scores['experience_score'].value,
                'education_score': all_scores['education_score'].value,
                'portfolio_score': all_scores['portfolio_score'].value,
                'interview_score': all_scores['interview_score'].value,
                'growth_score': all_scores['growth_score'].value,
                'communication_score': all_scores['communication_score'].value,
                'ai_confidence': ai_confidence_result.value,
                'explanations': self._build_explanations(all_scores),
                'score_history': self._build_score_history(all_scores),
            }
        )
        
        if not created:
            # Update existing talent score
            talent_score.overall_score = composite_result.value
            talent_score.skill_score = all_scores['skill_score'].value
            talent_score.experience_score = all_scores['experience_score'].value
            talent_score.education_score = all_scores['education_score'].value
            talent_score.portfolio_score = all_scores['portfolio_score'].value
            talent_score.interview_score = all_scores['interview_score'].value
            talent_score.growth_score = all_scores['growth_score'].value
            talent_score.communication_score = all_scores['communication_score'].value
            talent_score.ai_confidence = ai_confidence_result.value
            talent_score.explanations = self._build_explanations(all_scores)
            talent_score.score_history = self._build_score_history(all_scores)
            talent_score.save()
        
        # Emit event
        from apps.events.emitter import emit_sync
        from apps.events.types import TALENT_SCORE_UPDATED
        emit_sync(
            event_type=TALENT_SCORE_UPDATED,
            category="system",
            user=self.user,
            target_type="talent_score",
            target_id=str(talent_score.id),
            data={
                "overall_score": composite_result.value,
                "dimensions": {k: v.value for k, v in all_scores.items()},
            }
        )
        
        return {
            "talent_score_id": str(talent_score.id),
            "overall_score": composite_result.value,
            "dimensions": {k: v.to_dict() for k, v in all_scores.items()},
            "explanations": self._build_explanations(all_scores),
            "actions": composite_result.actions,
        }
    
    def _build_explanations(self, all_scores: Dict[str, ScoreResult]) -> Dict[str, Any]:
        """Build explanations dictionary for all dimensions."""
        return {
            "skill_score": {
                "evidence": all_scores['skill_score'].evidence,
                "explanation": all_scores['skill_score'].explanation,
                "actions": all_scores['skill_score'].actions,
                "trend": all_scores['skill_score'].trend,
            },
            "experience_score": {
                "evidence": all_scores['experience_score'].evidence,
                "explanation": all_scores['experience_score'].explanation,
                "actions": all_scores['experience_score'].actions,
                "trend": all_scores['experience_score'].trend,
            },
            "education_score": {
                "evidence": all_scores['education_score'].evidence,
                "explanation": all_scores['education_score'].explanation,
                "actions": all_scores['education_score'].actions,
                "trend": all_scores['education_score'].trend,
            },
            "portfolio_score": {
                "evidence": all_scores['portfolio_score'].evidence,
                "explanation": all_scores['portfolio_score'].explanation,
                "actions": all_scores['portfolio_score'].actions,
                "trend": all_scores['portfolio_score'].trend,
            },
            "growth_score": {
                "evidence": all_scores['growth_score'].evidence,
                "explanation": all_scores['growth_score'].explanation,
                "actions": all_scores['growth_score'].actions,
                "trend": all_scores['growth_score'].trend,
            },
            "communication_score": {
                "evidence": all_scores['communication_score'].evidence,
                "explanation": all_scores['communication_score'].explanation,
                "actions": all_scores['communication_score'].actions,
                "trend": all_scores['communication_score'].trend,
            },
            "interview_score": {
                "evidence": all_scores['interview_score'].evidence,
                "explanation": all_scores['interview_score'].explanation,
                "actions": all_scores['interview_score'].actions,
                "trend": all_scores['interview_score'].trend,
            },
            "ai_confidence": {
                "evidence": all_scores['ai_confidence'].evidence,
                "explanation": all_scores['ai_confidence'].explanation,
                "actions": all_scores['ai_confidence'].actions,
                "trend": all_scores['ai_confidence'].trend,
            },
        }
    
    def _build_score_history(self, all_scores: Dict[str, ScoreResult]) -> List[Dict[str, Any]]:
        """Build score history entry."""
        return [{
            "date": timezone.now().isoformat(),
            "overall_score": all_scores['skill_score'].value * 0.25 +
                            all_scores['experience_score'].value * 0.20 +
                            all_scores['portfolio_score'].value * 0.15 +
                            all_scores['interview_score'].value * 0.15 +
                            all_scores['growth_score'].value * 0.15 +
                            all_scores['communication_score'].value * 0.10,
            "dimensions": {k: v.value for k, v in all_scores.items()},
        }]

    # =========================================================================
    # Explanation Generator (GAP 3 - Missing)
    # =========================================================================

    def generate_explanation(self, dimension: str, score_result: ScoreResult) -> Dict[str, Any]:
        """
        Generate natural language explanation for a score dimension.
        
        Args:
            dimension: The score dimension (e.g., 'skill_score', 'experience_score')
            score_result: The ScoreResult object with score data
            
        Returns:
            Dictionary with explanation, evidence, and recommendations
        """
        explanation_data = {
            "dimension": dimension,
            "score": score_result.value,
            "grade": score_result.grade,
            "confidence": score_result.confidence,
            "explanation": score_result.explanation,
            "evidence": score_result.evidence,
            "actions": score_result.actions,
            "trend": score_result.trend,
        }
        
        # Add dimension-specific context
        dimension_contexts = {
            "skill_score": {
                "importance": "Technical skills are crucial for demonstrating your ability to perform in a technical role",
                "benchmark": "Top 25% of candidates typically have skill scores above 0.75",
            },
            "experience_score": {
                "importance": "Experience shows your ability to apply skills in real-world scenarios",
                "benchmark": "Mid-level candidates typically have 3-7 years of experience",
            },
            "portfolio_score": {
                "importance": "Portfolio demonstrates your practical application of skills",
                "benchmark": "Strong portfolios show consistent activity over 6+ months",
            },
            "interview_score": {
                "importance": "Interview performance shows your communication and problem-solving skills",
                "benchmark": "Top candidates score above 0.8 on technical interviews",
            },
            "growth_score": {
                "importance": "Learning velocity indicates your ability to adapt and grow",
                "benchmark": "High growth candidates complete 3+ courses per quarter",
            },
            "communication_score": {
                "importance": "Communication skills are essential for collaboration and clarity",
                "benchmark": "Clear communication is expected at all levels",
            },
        }
        
        if dimension in dimension_contexts:
            explanation_data["context"] = dimension_contexts[dimension]
        
        return explanation_data

    # =========================================================================
    # Interview Simulation System (GAP 4 - Missing)
    # =========================================================================

    def generate_questions(self, interview_type: str, target_role: str, difficulty: str = "mid") -> List[Dict[str, Any]]:
        """
        Generate interview questions based on type, role, and difficulty.
        
        Args:
            interview_type: 'technical', 'behavioral', 'coding', 'system_design', 'case_study'
            target_role: The target job role (e.g., 'Software Engineer', 'Data Scientist')
            difficulty: 'junior', 'mid', 'senior', 'lead'
            
        Returns:
            List of question dictionaries with question text, type, and evaluation criteria
        """
        # Question templates by type and difficulty
        question_templates = {
            "technical": {
                "junior": [
                    {
                        "question": f"Can you describe a project where you used technical skills to solve a problem?",
                        "type": "behavioral",
                        "category": "technical_fundamentals",
                        "evaluation_criteria": ["problem_solving", "technical_implementation", "results"],
                        "expected_length": "2-3 minutes",
                    },
                    {
                        "question": f"What technical skills are you most confident in, and how have you applied them?",
                        "type": "self_assessment",
                        "category": "technical_skills",
                        "evaluation_criteria": ["self-awareness", "practical_application", "depth_of_knowledge"],
                        "expected_length": "1-2 minutes",
                    },
                ],
                "mid": [
                    {
                        "question": f"Describe a technical challenge you faced in your recent work and how you solved it.",
                        "type": "behavioral",
                        "category": "technical_problem_solving",
                        "evaluation_criteria": ["analysis", "solution_approach", "implementation", "results"],
                        "expected_length": "3-4 minutes",
                    },
                    {
                        "question": f"How do you stay current with new technologies in your field?",
                        "type": "behavioral",
                        "category": "learning_growth",
                        "evaluation_criteria": ["learning_methods", "time_management", "application"],
                        "expected_length": "2-3 minutes",
                    },
                ],
                "senior": [
                    {
                        "question": f"Describe a complex technical problem you solved that required collaboration across teams.",
                        "type": "behavioral",
                        "category": "technical_leadership",
                        "evaluation_criteria": ["technical_depth", "collaboration", "impact", "communication"],
                        "expected_length": "4-5 minutes",
                    },
                    {
                        "question": f"How do you approach technical debt in your projects?",
                        "type": "scenario",
                        "category": "software_engineering_practices",
                        "evaluation_criteria": ["awareness", "strategy", "tradeoffs", "communication"],
                        "expected_length": "3-4 minutes",
                    },
                ],
                "lead": [
                    {
                        "question": f"Describe a major technical decision you made that impacted your team or organization.",
                        "type": "behavioral",
                        "category": "technical_strategy",
                        "evaluation_criteria": ["strategic_thinking", "impact", "stakeholder_management", "execution"],
                        "expected_length": "5-6 minutes",
                    },
                ],
            },
            "behavioral": {
                "junior": [
                    {
                        "question": "Tell me about a time you faced a challenge in a team setting.",
                        "type": "behavioral",
                        "category": "teamwork",
                        "evaluation_criteria": ["communication", "collaboration", "conflict_resolution"],
                        "expected_length": "2-3 minutes",
                    },
                    {
                        "question": "Describe a time you received feedback and how you responded.",
                        "type": "behavioral",
                        "category": "growth_mindset",
                        "evaluation_criteria": ["receptiveness", "action", "results"],
                        "expected_length": "2-3 minutes",
                    },
                ],
                "mid": [
                    {
                        "question": "Tell me about a time you had to manage competing priorities.",
                        "type": "behavioral",
                        "category": "time_management",
                        "evaluation_criteria": ["prioritization", "planning", "execution"],
                        "expected_length": "3-4 minutes",
                    },
                    {
                        "question": "Describe a situation where you had to influence others without authority.",
                        "type": "behavioral",
                        "category": "influence",
                        "evaluation_criteria": ["approach", "communication", "results"],
                        "expected_length": "3-4 minutes",
                    },
                ],
                "senior": [
                    {
                        "question": "Describe a time you had to make a difficult decision with incomplete information.",
                        "type": "behavioral",
                        "category": "decision_making",
                        "evaluation_criteria": ["analysis", "judgment", "communication", "results"],
                        "expected_length": "4-5 minutes",
                    },
                ],
                "lead": [
                    {
                        "question": "Tell me about a time you had to lead through organizational change.",
                        "type": "behavioral",
                        "category": "leadership",
                        "evaluation_criteria": ["vision", "communication", "execution", "results"],
                        "expected_length": "5-6 minutes",
                    },
                ],
            },
            "coding": {
                "junior": [
                    {
                        "question": "Write a function to reverse a string.",
                        "type": "coding",
                        "category": "algorithms",
                        "evaluation_criteria": ["correctness", "efficiency", "readability"],
                        "expected_length": "10-15 minutes",
                        "difficulty": "easy",
                    },
                    {
                        "question": "Write a function to find the maximum value in an array.",
                        "type": "coding",
                        "category": "algorithms",
                        "evaluation_criteria": ["correctness", "efficiency", "edge_cases"],
                        "expected_length": "10-15 minutes",
                        "difficulty": "easy",
                    },
                ],
                "mid": [
                    {
                        "question": "Implement a function to check if a string has all unique characters.",
                        "type": "coding",
                        "category": "algorithms",
                        "evaluation_criteria": ["correctness", "efficiency", "space_complexity"],
                        "expected_length": "15-20 minutes",
                        "difficulty": "medium",
                    },
                    {
                        "question": f"Write a solution for a common problem in {target_role} work.",
                        "type": "coding",
                        "category": "domain_specific",
                        "evaluation_criteria": ["correctness", "domain_knowledge", "code_quality"],
                        "expected_length": "20-25 minutes",
                        "difficulty": "medium",
                    },
                ],
                "senior": [
                    {
                        "question": "Design a data structure for a cache with O(1) get and set operations.",
                        "type": "coding",
                        "category": "system_design",
                        "evaluation_criteria": ["efficiency", "scalability", "edge_cases"],
                        "expected_length": "25-30 minutes",
                        "difficulty": "hard",
                    },
                ],
                "lead": [
                    {
                        "question": "Design a scalable system for handling high-volume data processing.",
                        "type": "coding",
                        "category": "system_design",
                        "evaluation_criteria": ["architecture", "scalability", "reliability", "tradeoffs"],
                        "expected_length": "30-45 minutes",
                        "difficulty": "hard",
                    },
                ],
            },
            "system_design": {
                "mid": [],
                "senior": [
                    {
                        "question": "Design a URL shortening service like Bitly.",
                        "type": "system_design",
                        "category": "web_services",
                        "evaluation_criteria": ["scalability", "performance", "reliability", "storage"],
                        "expected_length": "30-40 minutes",
                    },
                ],
                "lead": [
                    {
                        "question": "Design a distributed system for real-time analytics processing.",
                        "type": "system_design",
                        "category": "distributed_systems",
                        "evaluation_criteria": ["architecture", "scalability", "fault_tolerance", "monitoring"],
                        "expected_length": "40-50 minutes",
                    },
                ],
            },
            "case_study": {
                "junior": [],
                "mid": [],
                "senior": [
                    {
                        "question": "How would you improve the user experience of a popular product?",
                        "type": "case_study",
                        "category": "product",
                        "evaluation_criteria": ["analysis", "solution", "tradeoffs", "communication"],
                        "expected_length": "20-25 minutes",
                    },
                ],
                "lead": [
                    {
                        "question": "How would you prioritize features for a product with limited resources?",
                        "type": "case_study",
                        "category": "strategy",
                        "evaluation_criteria": ["strategic_thinking", "prioritization", "stakeholder_management", "execution"],
                        "expected_length": "25-30 minutes",
                    },
                ],
            },
        }
        
        # Get questions for the specified type and difficulty
        type_questions = question_templates.get(interview_type, {})
        difficulty_questions = type_questions.get(difficulty, [])
        
        # If no questions for this difficulty, use mid as fallback
        if not difficulty_questions:
            difficulty_questions = type_questions.get("mid", [])
        
        # If still no questions, use junior as fallback
        if not difficulty_questions:
            difficulty_questions = type_questions.get("junior", [])
        
        # Add role-specific context to questions
        for question in difficulty_questions:
            question["target_role"] = target_role
            question["role_context"] = f"For a {target_role} position"
        
        return difficulty_questions[:5]  # Return up to 5 questions

    def evaluate_answer(self, question: str, answer: str, criteria: List[str] = None) -> Dict[str, Any]:
        """
        Evaluate a user's answer to an interview question.
        
        Args:
            question: The interview question
            answer: The user's answer
            criteria: List of evaluation criteria (optional)
            
        Returns:
            Dictionary with evaluation score, feedback, and recommendations
        """
        if criteria is None:
            criteria = ["relevance", "clarity", "depth", "structure", "examples"]
        
        # Calculate scores for each criterion
        scores = {}
        feedback = {}
        
        # Relevance (how well the answer addresses the question)
        relevance_keywords = ["because", "therefore", "so", "as a result"]
        has_relevance_indicators = any(kw in answer.lower() for kw in relevance_keywords)
        relevance_score = 0.5 + (0.3 if has_relevance_indicators else 0) + (0.2 if len(answer) > 50 else 0)
        scores["relevance"] = min(1.0, relevance_score)
        feedback["relevance"] = "Good relevance to the question" if scores["relevance"] >= 0.7 else "Try to stay focused on the question"
        
        # Clarity (how clear and understandable the answer is)
        clarity_words = len(answer.split())
        clarity_score = 0.5 + min(0.3, clarity_words / 100) + (0.2 if "." in answer else 0)
        scores["clarity"] = min(1.0, clarity_score)
        feedback["clarity"] = "Clear and well-expressed" if scores["clarity"] >= 0.7 else "Consider structuring your answer more clearly"
        
        # Depth (level of detail and insight)
        depth_indicators = ["because", "for example", "such as", "specifically", "detailed"]
        has_depth_indicators = any(ind in answer.lower() for ind in depth_indicators)
        depth_score = 0.4 + (0.3 if has_depth_indicators else 0) + (0.3 if len(answer) > 100 else 0)
        scores["depth"] = min(1.0, depth_score)
        feedback["depth"] = "Good depth and detail" if scores["depth"] >= 0.7 else "Add more specific details and examples"
        
        # Structure (organization and flow)
        structure_indicators = [". ", ", ", "first", "second", "finally", "in conclusion"]
        has_structure_indicators = any(ind in answer.lower() for ind in structure_indicators)
        structure_score = 0.4 + (0.3 if has_structure_indicators else 0) + (0.3 if answer.count(".") > 1 else 0)
        scores["structure"] = min(1.0, structure_score)
        feedback["structure"] = "Well-structured answer" if scores["structure"] >= 0.7 else "Consider using a structured approach (e.g., STAR method)"
        
        # Examples (use of specific examples)
        example_indicators = ["example", "such as", "for instance", "like", "when", "where"]
        has_example_indicators = any(ind in answer.lower() for ind in example_indicators)
        example_score = 0.5 + (0.3 if has_example_indicators else 0) + (0.2 if len(answer) > 150 else 0)
        scores["examples"] = min(1.0, example_score)
        feedback["examples"] = "Good use of examples" if scores["examples"] >= 0.7 else "Include specific examples to support your points"
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)
        
        # Generate recommendations
        recommendations = []
        for criterion, score in scores.items():
            if score < 0.7:
                recommendations.append({
                    "criterion": criterion,
                    "score": round(score, 2),
                    "feedback": feedback[criterion],
                    "improvement": f"Focus on improving {criterion} in your answers"
                })
        
        # Generate overall feedback
        if overall_score >= 0.8:
            overall_feedback = "Excellent answer! Your response was strong across all evaluation criteria."
        elif overall_score >= 0.6:
            overall_feedback = "Good answer. You covered the main points well, with room for improvement in some areas."
        elif overall_score >= 0.4:
            overall_feedback = "Fair answer. Consider adding more detail, examples, or structure to improve."
        else:
            overall_feedback = "Needs improvement. Focus on addressing the question directly with specific examples."
        
        return {
            "question": question,
            "answer_length": len(answer),
            "overall_score": round(overall_score, 3),
            "scores": {k: round(v, 3) for k, v in scores.items()},
            "feedback": feedback,
            "overall_feedback": overall_feedback,
            "recommendations": recommendations,
            "grade": "A" if overall_score >= 0.8 else "B" if overall_score >= 0.6 else "C" if overall_score >= 0.4 else "D" if overall_score >= 0.2 else "F",
        }
