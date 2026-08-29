"""
Proactive Rashid Service

This module provides proactive notification generation from Rashid AI
based on user triggers and events.
"""

import logging
from datetime import timedelta
from typing import Dict, Any, List
from django.db import models
from django.utils import timezone
from django.conf import settings

from apps.career.models import CareerBrain, CareerGoal
from apps.jobs.models import JobSave, JobSearch
from apps.interviews.models import InterviewSession
from apps.notifications.models import UserNotification
from apps.intelligence.career_ai import career_ai_service as bedrock_service

logger = logging.getLogger(__name__)


class ProactiveRashidService:
    """
    Service for generating proactive notifications from Rashid AI.
    
    Checks for notification-worthy events and generates personalized
    messages using AI.
    """
    
    def __init__(self):
        self.bedrock = bedrock_service
    
    def check_user_triggers(self, user_id: int) -> List[Dict]:
        """
        Check for notification-worthy events for a user.
        
        Triggers checked:
        - New jobs matching saved searches (daily)
        - Career goal deadlines approaching (3 days before)
        - Skills trending in target industry
        - Interview practice reminder (if none in 2 weeks)
        - Profile completeness < 80% reminder
        
        Args:
            user_id: User ID to check
            
        Returns:
            List of trigger notifications to send
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return []
        
        triggers = []
        
        # 1. New jobs matching saved searches
        new_jobs = self._check_new_matching_jobs(user)
        if new_jobs:
            triggers.append({
                'type': 'new_jobs',
                'context': {'job_count': len(new_jobs)},
                'message': self._generate_new_jobs_message(user, new_jobs),
            })
        
        # 2. Career goal deadlines approaching
        approaching_goals = self._check_approaching_deadlines(user)
        if approaching_goals:
            triggers.append({
                'type': 'goal_deadline',
                'context': {'goal_count': len(approaching_goals)},
                'message': self._generate_goal_deadline_message(user, approaching_goals),
            })
        
        # 3. Skills trending in target industry
        trending_skills = self._check_trending_skills(user)
        if trending_skills:
            triggers.append({
                'type': 'trending_skills',
                'context': {'skills': trending_skills},
                'message': self._generate_trending_skills_message(user, trending_skills),
            })
        
        # 4. Interview practice reminder
        interview_reminder = self._check_interview_reminder(user)
        if interview_reminder:
            triggers.append({
                'type': 'interview_reminder',
                'context': {'days_since': interview_reminder},
                'message': self._generate_interview_reminder_message(user, interview_reminder),
            })
        
        # 5. Profile completeness reminder
        completeness_reminder = self._check_completeness_reminder(user)
        if completeness_reminder:
            triggers.append({
                'type': 'completeness_reminder',
                'context': {'completeness': completeness_reminder},
                'message': self._generate_completeness_message(user, completeness_reminder),
            })
        
        return triggers
    
    def _check_new_matching_jobs(self, user) -> List[Dict]:
        """Check for new jobs matching user's saved searches."""
        from apps.jobs.models import Job
        
        # Get jobs saved in last 24 hours
        recent_saves = JobSave.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=1)
        ).select_related('job')
        
        return [s.job for s in recent_saves]
    
    def _check_approaching_deadlines(self, user) -> List[CareerGoal]:
        """Check for goals with deadlines approaching (within 3 days)."""
        from datetime import date
        
        today = date.today()
        three_days_later = today + timedelta(days=3)
        
        return CareerGoal.objects.filter(
            user=user,
            target_date__gte=today,
            target_date__lte=three_days_later,
            status='active'
        )
    
    def _check_trending_skills(self, user) -> List[str]:
        """Check for trending skills in user's target field."""
        # This is a placeholder - would integrate with market data API
        # For now, return some common trending skills
        return ['Python', 'AI/ML', 'Cloud Computing']
    
    def _check_interview_reminder(self, user) -> int:
        """Check days since last interview practice."""
        last_interview = InterviewSession.objects.filter(
            user=user
        ).order_by('-started_at').first()
        
        if not last_interview:
            return 30  # No interviews ever
        
        days_since = (timezone.now().date() - last_interview.started_at.date()).days
        return days_since if days_since >= 14 else 0
    
    def _check_completeness_reminder(self, user) -> float:
        """Check profile completeness score."""
        try:
            career_brain = user.career_brain
            if career_brain.confidence_score < 0.8:
                return career_brain.confidence_score
        except Exception:
            pass
        return 0.0
    
    def generate_notification(self, user_id: int, trigger_type: str, context: Dict) -> str:
        """
        Generate personalized notification message using AI.
        
        Args:
            user_id: User ID
            trigger_type: Type of trigger
            context: Trigger context data
            
        Returns:
            AI-generated notification message
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return "عذراً، لم أتمكن من إنشاء رسالة مناسبة."
        
        # Build user context
        try:
            career_brain = user.career_brain
            user_context = career_brain.to_prompt_context(max_tokens=300)
        except Exception:
            user_context = "لا توجد معلومات مفصلة عن المستخدم."
        
        # Build prompt based on trigger type
        prompts = {
            'new_jobs': f"""أنت مستشار مهني رشيد. أرسل رسالة ودية للمستخدم تخبره بوجود وظائف جديدة تطابق اهتماماته.

السياق:
- عدد الوظائف الجديدة: {context.get('job_count', 0)}
- السيرة الذاتية للمستخدم: {user_context}

أعد رسالة بالعربية تشمل:
1. تحية ودية
2. إخبار بالوظائف الجديدة
3. تشجيع على مراجعة الوظائف
4. دعوة للتفاعل مع الوظائف المفضلة

الرسالة يجب أن تكون مختصرة (3-4 جمل) وودية.""",
            
            'goal_deadline': f"""أنت مستشار مهني رشيد. أرسل رسالة تذكير ودية للمستخدم بموعد انتهاء أهدافه المهنية.

السياق:
- عدد الأهداف القريبة: {context.get('goal_count', 0)}
- السيرة الذاتية للمستخدم: {user_context}

أعد رسالة بالعربية تشمل:
1. تحية ودية
2. تذكير بالأهداف القريبة
3. تشجيع على اتخاذ خطوة صغيرة نحو الهدف
4. دعوة للتحدث عن التحديات

الرسالة يجب أن تكون ملهمة وداعمة.""",
            
            'trending_skills': f"""أنت مستشار مهني رشيد. أرسل رسالة تخبر المستخدم بالمهارات المتداولة في مجاله.

السياق:
- المهارات المتداولة: {', '.join(context.get('skills', []))}
- السيرة الذاتية للمستخدم: {user_context}

أعد رسالة بالعربية تشمل:
1. تحية ودية
2. إخبار بالمهارات المتداولة
3. نصيحة حول أهمية تعلم هذه المهارات
4. دعوة للتحدث عن خطة التعلم

الرسالة يجب أن تكون مفيدة وتشجيعية.""",
            
            'interview_reminder': f"""أنت مستشار مهني رشيد. أرسل رسالة تذكير ودية للمستخدم بممارسة المقابلات.

السياق:
- عدد الأيام منذ آخر مقابلة: {context.get('days_since', 0)}
- السيرة الذاتية للمستخدم: {user_context}

أعد رسالة بالعربية تشمل:
1. تحية ودية
2. تذكير بأهمية التدريب المستمر
3. عرض مساعدة في إعداد مقابلة
4. دعوة لاختيار نوع المقابلة

الرسالة يجب أن تكون محفزة وداعمة.""",
            
            'completeness_reminder': f"""أنت مستشار مهني رشيد. أرسل رسالة ودية لتحديث الملف الشخصي.

السياق:
- درجة الإكمال: {context.get('completeness', 0):.0%}
- السيرة الذاتية للمستخدم: {user_context}

أعد رسالة بالعربية تشمل:
1. تحية ودية
2. إخبار بدرجة الإكمال الحالية
3. إشارة إلى ما يمكن إضافته لتحسين الملف
4. دعوة لتحديث المعلومات

الرسالة يجب أن تكون محفزة وتشجيعية.""",
        }
        
        prompt = prompts.get(trigger_type, prompts['new_jobs'])
        
        try:
            if self.bedrock.is_available:
                response = self.bedrock.invoke_model(
                    prompt=prompt,
                    max_tokens=300,
                    temperature=0.7
                )
                return response.strip()
            
            return self._get_fallback_message(trigger_type, context)
            
        except Exception as e:
            logger.error(f"Error generating notification: {e}")
            return self._get_fallback_message(trigger_type, context)
    
    def _get_fallback_message(self, trigger_type: str, context: Dict) -> str:
        """Get fallback message when AI is unavailable."""
        messages = {
            'new_jobs': "لديك وظائف جديدة تطابق اهتماماتك! تحقق من الوظائف المحفوظة الآن.",
            'goal_deadline': "أنت قريب من تحقيق أهدافك المهنية! استمر في التقدم.",
            'trending_skills': "هذه المهارات متداولة حالياً في سوق العمل. فكر في تعلمها.",
            'interview_reminder': "من المهم ممارسة المقابلات باستمرار. هل تريد التدريب الآن؟",
            'completeness_reminder': "يمكنك تحسين ملفك الشخصي لزيادة فرصك. جرب إضافة المزيد من المعلومات.",
        }
        return messages.get(trigger_type, "هل هناك شيء أستطيع مساعدتك به اليوم؟")
    
    def create_notification_record(
        self, user_id: int, trigger_type: str, message: str, context: Dict
    ) -> UserNotification:
        """
        Create a notification record in the database.

        Args:
            user_id: User ID
            trigger_type: Type of trigger
            message: Notification message
            context: Trigger context data

        Returns:
            Created UserNotification instance
        """
        notification = UserNotification.objects.create(
            user_id=user_id,
            notification_type='system',
            title=self._get_notification_title(trigger_type),
            message=message,
            related_type='rashid_proactive',
            related_id=trigger_type,
            status='unread',
        )
        return notification
    
    def _get_notification_title(self, trigger_type: str) -> str:
        """Get notification title based on trigger type."""
        titles = {
            'new_jobs': 'وظائف جديدة لك!',
            'goal_deadline': 'تذكير بالهدف',
            'trending_skills': 'مهارات متداولة',
            'interview_reminder': 'تدريب على المقابلات',
            'completeness_reminder': 'تحديث الملف الشخصي',
        }
        return titles.get(trigger_type, 'رسالة من رشيد')


# Singleton instance
proactive_rashid_service = ProactiveRashidService()