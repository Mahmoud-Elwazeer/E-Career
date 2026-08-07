"""
Career Brain Service

This module provides services for building and updating Career Brain context
for users, which is used by Rashid AI and other AI-powered features.
"""

import logging
from datetime import timedelta
from typing import Dict, Any, List
from django.db import models
from django.utils import timezone
from django.conf import settings

from apps.career.models import CareerBrain, CareerUserSkill, CareerLearning, CareerGoal
from apps.jobs.models import JobSave, JobSearch
from apps.interviews.models import InterviewSession
from apps.ai.bedrock import bedrock_service

logger = logging.getLogger(__name__)


class CareerBrainService:
    """
    Service for building and updating Career Brain context.
    
    Provides:
    - Context building for AI prompts
    - Daily updates for all active users
    - Event-driven updates on user data changes
    """
    
    def __init__(self):
        self.bedrock = bedrock_service
    
    def build_context(self, user_id: int) -> str:
        """
        Build comprehensive career context for a user.
        
        Collects:
        - Current role and experience
        - Skills (with proficiency levels)
        - Career goals and progress
        - Recent job searches and saves
        - Interview performance trends
        - Skill gaps identified
        - Market trends relevant to their field
        
        Args:
            user_id: User ID to build context for
            
        Returns:
            Formatted context string for AI prompts
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return "لا توجد معلومات عن المستخدم."
        
        context_parts = []
        
        # 1. Current role and experience
        try:
            career_profile = user.career_profile
            if career_profile.current_role:
                context_parts.append(f"الوظيفة الحالية: {career_profile.current_role}")
            if career_profile.current_company:
                context_parts.append(f"الشركة الحالية: {career_profile.current_company}")
            if career_profile.experience_years:
                context_parts.append(f"سنوات الخبرة: {career_profile.experience_years}")
        except Exception:
            pass
        
        # 2. Skills with proficiency levels
        user_skills = CareerUserSkill.objects.filter(user=user, verified=True)[:15]
        if user_skills:
            skills_info = []
            for us in user_skills:
                level = us.get_proficiency_display()
                verified = " (متحقق)" if us.verified else ""
                skills_info.append(f"{us.skill.name} ({level}){verified}")
            context_parts.append(f"المهارات: {', '.join(skills_info)}")
        
        # 3. Career goals and progress
        active_goals = CareerGoal.objects.filter(
            user=user,
            status__in=['active', 'in_progress']
        )[:5]
        if active_goals:
            goals_info = []
            for goal in active_goals:
                progress = f" ({goal.progress}%)" if goal.progress else ""
                goals_info.append(f"{goal.title}{progress}")
            context_parts.append(f"الأهداف الحالية: {', '.join(goals_info)}")
        
        # 4. Recent job searches and saves
        recent_searches = JobSearch.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:5]
        if recent_searches:
            search_terms = [s.search_query[:50] for s in recent_searches if s.search_query]
            if search_terms:
                context_parts.append(f"البحث الأخير: {', '.join(search_terms)}")
        
        recent_saves = JobSave.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:5]
        if recent_saves:
            saved_jobs = [s.job.title for s in recent_saves if s.job]
            if saved_jobs:
                context_parts.append(f"الوظائف المحفوظة: {', '.join(saved_jobs[:3])}")
        
        # 5. Interview performance trends
        recent_interviews = InterviewSession.objects.filter(
            user=user,
            started_at__gte=timezone.now() - timedelta(days=90)
        ).order_by('-started_at')[:5]
        if recent_interviews:
            avg_score = sum(i.overall_score or 0 for i in recent_interviews) / max(len(recent_interviews), 1)
            context_parts.append(f"متوسط درجات المقابلات (3 أشهر): {avg_score:.0%}")
        
        # 6. Skill gaps identified
        try:
            career_brain = user.career_brain
            if career_brain.ai_observations and career_brain.ai_observations.get('skill_gaps'):
                gaps = career_brain.ai_observations['skill_gaps'][:3]
                context_parts.append(f"المهارات المطلوبة: {', '.join(gaps)}")
        except Exception:
            pass
        
        # 7. Market trends relevant to their field
        try:
            career_brain = user.career_brain
            if career_brain.ai_observations and career_brain.ai_observations.get('market_trends'):
                trends = career_brain.ai_observations['market_trends'][:2]
                context_parts.append(f"اتجاهات السوق: {', '.join(trends)}")
        except Exception:
            pass
        
        # Combine all parts
        full_context = '\n'.join(context_parts)
        
        # Truncate if needed (max ~500 tokens)
        if len(full_context) > 2000:
            full_context = full_context[:2000] + "\n... (تم تقصير السياق)"
        
        return full_context
    
    def update_brain(self, user_id: int) -> Dict[str, Any]:
        """
        Update Career Brain with latest aggregated data.
        
        Called by event consumers when user data changes.
        
        Args:
            user_id: User ID to update
            
        Returns:
            Update results with confidence score
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return {'error': 'User not found'}
        
        # Get or create Career Brain
        career_brain, created = CareerBrain.objects.get_or_create(user=user)
        
        # Build updated context
        context = self.build_context(user_id)
        
        # Generate AI observations if Bedrock is available
        ai_observations = self._generate_ai_observations(user, context)
        
        # Update the brain
        career_brain.skills = self._build_skills_data(user)
        career_brain.goals = self._build_goals_data(user)
        career_brain.preferences = self._build_preferences_data(user)
        career_brain.learning = self._build_learning_data(user)
        career_brain.history_summary = self._generate_history_summary(user)
        career_brain.ai_observations = ai_observations
        career_brain.confidence_score = self._calculate_confidence(career_brain)
        career_brain.last_updated_at = timezone.now()
        career_brain.save()
        
        return {
            'user_id': user_id,
            'created': created,
            'confidence_score': career_brain.confidence_score,
            'updated_at': career_brain.last_updated_at.isoformat(),
        }
    
    def _build_skills_data(self, user) -> Dict[str, Any]:
        """Build skills data for Career Brain."""
        user_skills = CareerUserSkill.objects.filter(user=user)
        
        skills = {}
        for us in user_skills:
            skills[us.skill.name] = {
                'level': us.proficiency,
                'verified': us.verified,
                'years': us.years_experience,
                'source': us.source,
            }
        
        return skills
    
    def _build_goals_data(self, user) -> List[Dict]:
        """Build goals data for Career Brain."""
        goals = CareerGoal.objects.filter(user=user).values(
            'title', 'goal_type', 'status', 'priority', 'progress', 'target_date'
        )
        
        return list(goals)
    
    def _build_preferences_data(self, user) -> Dict[str, Any]:
        """Build preferences data for Career Brain."""
        try:
            career_profile = user.career_profile
            return {
                'target_roles': [r.get('role') for r in career_profile.target_roles if r.get('role')],
                'target_locations': [l.get('city') for l in career_profile.target_locations if l.get('city')],
                'salary_min': str(career_profile.target_salary_min) if career_profile.target_salary_min else None,
                'work_style': 'Remote' if career_profile.open_to_remote else 'On-site',
                'alert_frequency': career_profile.alert_frequency,
            }
        except Exception:
            return {}
    
    def _build_learning_data(self, user) -> Dict[str, Any]:
        """Build learning data for Career Brain."""
        recent_learning = CareerLearning.objects.filter(
            user=user,
            completed_at__gte=timezone.now().date() - timedelta(days=180)
        )
        
        return {
            'recent_courses': recent_learning.count(),
            'platforms': list(set(l.platform for l in recent_learning))[:5],
            'skills_gained': list(set(
                skill for l in recent_learning
                for skill in l.skills_gained
            ))[:10],
        }
    
    def _generate_history_summary(self, user) -> str:
        """Generate AI-generated career history summary."""
        try:
            career_profile = user.career_profile
            
            # Build summary from CV parsed data
            cv_data = career_profile.cv_parsed_data
            if cv_data.get('summary'):
                return cv_data['summary']
            
            # Fallback summary
            parts = []
            if career_profile.current_role:
                parts.append(f"يعمل حالياً كـ {career_profile.current_role}")
            if career_profile.experience_years:
                parts.append(f"لديه {career_profile.experience_years} سنوات خبرة")
            if career_profile.target_roles:
                roles = [r.get('role') for r in career_profile.target_roles]
                parts.append(f"يهدف للعمل كـ {', '.join(roles[:2])}")
            
            return '، '.join(parts) if parts else "لا توجد معلومات كافية عن السيرة الذاتية."
            
        except Exception:
            return "لا توجد معلومات كافية عن السيرة الذاتية."
    
    def _generate_ai_observations(self, user, context: str) -> Dict[str, Any]:
        """Generate AI observations about the user using Bedrock."""
        if not self.bedrock.is_available:
            return {
                'strengths': [],
                'growth_areas': [],
                'skill_gaps': [],
                'market_trends': [],
                'key_insights': [],
            }
        
        # Build prompt for AI analysis
        prompt = f"""أنت مستشار مهني خبير. قم بتحليل السيرة الذاتية والبيانات التالية عن المرشح:

{context}

قم بإنشاء تحليل مختصر بالعربية يحتوي على:
1. نقاط القوة الرئيسية (3-4 نقاط)
2. مجالات النمو المطلوبة (2-3 نقاط)
3. المهارات المطلوبة للتطور (2-3 نقاط)
4. اتجاهات السوق المناسبة (2 نقطة)
5. رؤى رئيسية (2-3 نقاط)

أعد النتيجة بصيغة JSON فقط بدون أي نص إضافي:
{{
    "strengths": ["نقطة قوة 1", "نقطة قوة 2", "نقطة قوة 3"],
    "growth_areas": ["مجال النمو 1", "مجال النمو 2"],
    "skill_gaps": ["المهارة المطلوبة 1", "المهارة المطلوبة 2"],
    "market_trends": ["اتجاه السوق 1", "اتجاه السوق 2"],
    "key_insights": ["رؤيّة رئيسية 1", "رؤيّة رئيسية 2"]
}}"""

        try:
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
            
            return self._get_fallback_observations()
            
        except Exception as e:
            logger.error(f"Error generating AI observations: {e}")
            return self._get_fallback_observations()
    
    def _get_fallback_observations(self) -> Dict[str, Any]:
        """Get fallback observations when AI is unavailable."""
        return {
            'strengths': ['قادر على التعلم السريع'],
            'growth_areas': ['تطوير مهارات القيادة'],
            'skill_gaps': ['الخبرة العملية', 'المهارات التقنية المتقدمة'],
            'market_trends': ['العمل عن بُعد', 'الذكاء الاصطناعي'],
            'key_insights': ['المرشح لديه إمكانات عالية للنمو'],
        }
    
    def _calculate_confidence(self, career_brain: CareerBrain) -> float:
        """Calculate confidence score for Career Brain."""
        score = 0.0
        weight = 0.0
        
        # Skills (30%)
        if career_brain.skills:
            verified_count = sum(1 for s in career_brain.skills.values() if s.get('verified'))
            total = len(career_brain.skills)
            if total > 0:
                score += (verified_count / total) * 0.3
                weight += 0.3
        
        # Goals (20%)
        if career_brain.goals:
            score += 0.2
            weight += 0.2
        
        # Preferences (20%)
        if career_brain.preferences:
            pref_count = len([k for k, v in career_brain.preferences.items() if v])
            if pref_count > 0:
                score += (pref_count / 4) * 0.2
                weight += 0.2
        
        # Learning (15%)
        if career_brain.learning and career_brain.learning.get('recent_courses', 0) > 0:
            score += 0.15
            weight += 0.15
        
        # History summary (15%)
        if career_brain.history_summary:
            score += 0.15
            weight += 0.15
        
        return round(score / max(weight, 0.01), 3)


# Singleton instance
career_brain_service = CareerBrainService()