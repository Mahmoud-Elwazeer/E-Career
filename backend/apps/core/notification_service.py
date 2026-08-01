"""
Notification Intelligence Service for E-Career.

Generates intelligent notifications based on rules and events.
"""

import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone

logger = structlog.get_logger()


class NotificationService:
    """Service for generating intelligent notifications."""
    
    def __init__(self, user):
        self.user = user
    
    def generate_notifications(self, event_type: str, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate notifications based on event type and data.
        
        Args:
            event_type: Type of event that triggered notification
            event_data: Data associated with the event
            
        Returns:
            List of notification objects
        """
        notifications = []
        
        # Route to appropriate notification generator
        handlers = {
            'job_match': self._notify_job_match,
            'interview_score_improvement': self._notify_interview_improvement,
            'profile_views': self._notify_profile_views,
            'new_certification': self._notify_new_certification,
            'score_improvement': self._notify_score_improvement,
            'job_applied': self._notify_job_applied,
            'interview_completed': self._notify_interview_completed,
        }
        
        handler = handlers.get(event_type)
        if handler:
            notifications = handler(event_data)
        
        return notifications
    
    def _notify_job_match(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate notification for new job match."""
        job = data.get('job', {})
        match_score = data.get('match_score', 0)
        
        if match_score >= 0.95:
            severity = 'high'
            title = 'New job 95% match your profile!'
            message = f"We found an exceptional match: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown Company')}. Apply now!"
        elif match_score >= 0.85:
            severity = 'medium'
            title = 'New job 85%+ match!'
            message = f"Great match: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown Company')}. Apply now!"
        else:
            severity = 'low'
            title = 'New job match'
            message = f"New opportunity: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown Company')}."
        
        return [{
            'type': 'job_match',
            'title': title,
            'message': message,
            'severity': severity,
            'job_id': job.get('id'),
            'job_title': job.get('title'),
            'company': job.get('company'),
            'match_score': match_score,
            'timestamp': timezone.now().isoformat(),
        }]
    
    def _notify_interview_improvement(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate notification for interview score improvement."""
        improvement = data.get('improvement', 0)
        previous_score = data.get('previous_score', 0)
        current_score = data.get('current_score', 0)
        
        if improvement >= 0.15:
            emoji = '🚀'
            title = 'Interview score improved by 15%+!'
        elif improvement >= 0.10:
            emoji = '🔥'
            title = 'Interview score improved by 12 points!'
        elif improvement >= 0.05:
            emoji = '📈'
            title = 'Interview score improved!'
        else:
            emoji = '👍'
            title = 'Interview score updated'
        
        return [{
            'type': 'interview_improvement',
            'title': f'{emoji} {title}',
            'message': f"Your interview score improved from {previous_score:.0%} to {current_score:.0%} ({improvement:.0%} increase). Keep it up!",
            'severity': 'high' if improvement >= 0.10 else 'medium',
            'previous_score': previous_score,
            'current_score': current_score,
            'improvement': improvement,
            'timestamp': timezone.now().isoformat(),
        }]
    
    def _notify_profile_views(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate notification for profile views."""
        views = data.get('views', 0)
        employers = data.get('employers', [])
        
        if views >= 10:
            title = '10+ profile views this week!'
            message = f"Your profile has been viewed {views} times by {len(employers)} employers. Keep optimizing!"
        elif views >= 5:
            title = '5+ profile views this week!'
            message = f"Your profile has been viewed {views} times by {len(employers)} employers. Good traction!"
        else:
            title = 'Profile views'
            message = f"Your profile has been viewed {views} times by {len(employers)} employers."
        
        return [{
            'type': 'profile_views',
            'title': title,
            'message': message,
            'severity': 'medium' if views >= 5 else 'low',
            'views': views,
            'employers': employers,
            'timestamp': timezone.now().isoformat(),
        }]
    
    def _notify_new_certification(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate notification for new certification."""
        certification = data.get('certification', {})
        
        return [{
            'type': 'certification',
            'title': '🎉 New Certification Earned!',
            'message': f"Congratulations on earning {certification.get('name', 'a certification')} from {certification.get('issuer', 'an issuer')}!",
            'severity': 'high',
            'certification': certification,
            'timestamp': timezone.now().isoformat(),
        }]
    
    def _notify_score_improvement(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate notification for career score improvement."""
        improvement = data.get('improvement', 0)
        previous_score = data.get('previous_score', 0)
        current_score = data.get('current_score', 0)
        
        return [{
            'type': 'score_improvement',
            'title': '🚀 Career Score Improved!',
            'message': f"Your career score improved from {previous_score:.0%} to {current_score:.0%} ({improvement:.0%} increase). You're making progress!",
            'severity': 'high' if improvement >= 0.10 else 'medium',
            'previous_score': previous_score,
            'current_score': current_score,
            'improvement': improvement,
            'timestamp': timezone.now().isoformat(),
        }]
    
    def _notify_job_applied(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate notification for job application."""
        job = data.get('job', {})
        
        return [{
            'type': 'job_applied',
            'title': '✅ Application Submitted!',
            'message': f"You've applied for {job.get('title', 'a position')} at {job.get('company', 'a company')}. Good luck!",
            'severity': 'medium',
            'job_id': job.get('id'),
            'job_title': job.get('title'),
            'company': job.get('company'),
            'timestamp': timezone.now().isoformat(),
        }]
    
    def _notify_interview_completed(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate notification for completed interview."""
        interview = data.get('interview', {})
        score = interview.get('score', 0)
        
        if score >= 0.85:
            emoji = '🌟'
            feedback = 'Excellent performance!'
        elif score >= 0.70:
            emoji = '👍'
            feedback = 'Good job!'
        else:
            emoji = '📚'
            feedback = 'Keep practicing!'
        
        return [{
            'type': 'interview_completed',
            'title': f'{emoji} Interview Completed!',
            'message': f"You completed a {interview.get('type', 'technical')} interview with a score of {score:.0%}. {feedback}",
            'severity': 'medium',
            'interview': interview,
            'score': score,
            'feedback': feedback,
            'timestamp': timezone.now().isoformat(),
        }]
    
    def send_notification(self, notification: Dict[str, Any], user=None) -> Dict[str, Any]:
        """
        Send a notification to the user.
        
        Respects user's alert_frequency preference.
        Sends to both in-app and email channels.
        
        Args:
            notification: Notification object to send
            user: User to send to (defaults to self.user)
            
        Returns:
            Send result
        """
        user = user or self.user
        
        # Get user's alert preferences
        alert_frequency = getattr(user, 'alert_frequency', 'instant')
        
        # Check if notification should be sent based on frequency
        if alert_frequency == 'daily':
            return {'status': 'queued', 'reason': 'Daily digest mode'}
        elif alert_frequency == 'weekly':
            return {'status': 'queued', 'reason': 'Weekly digest mode'}
        
        # Send to in-app channel
        in_app_result = self._send_in_app(notification)
        
        # Send to email channel (respecting preferences)
        email_result = self._send_email(notification) if alert_frequency == 'instant' else {'status': 'skipped', 'reason': 'Email only in instant mode'}
        
        return {
            'status': 'sent',
            'in_app': in_app_result,
            'email': email_result,
            'notification': notification,
        }
    
    def _send_in_app(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to in-app channel."""
        # In production, this would save to database and push to frontend
        return {
            'status': 'sent',
            'channel': 'in_app',
            'notification_id': notification.get('type', 'unknown'),
        }
    
    def _send_email(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to email channel."""
        # In production, this would send email via SES or similar
        return {
            'status': 'sent',
            'channel': 'email',
            'notification_id': notification.get('type', 'unknown'),
        }


def generate_notification_summary(user, period: str = 'week') -> Dict[str, Any]:
    """
    Generate a summary of notifications for a user.
    
    Args:
        user: User to generate summary for
        period: Time period ('day', 'week', 'month')
        
    Returns:
        Summary dictionary
    """
    return {
        'period': period,
        'total_notifications': 0,  # Would query database
        'by_type': {},
        'by_severity': {
            'high': 0,
            'medium': 0,
            'low': 0,
        },
        'read_count': 0,
        'unread_count': 0,
        'generated_at': timezone.now().isoformat(),
    }