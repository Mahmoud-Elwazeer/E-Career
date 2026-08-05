"""
GDPR Compliance Service

This module provides GDPR-compliant data export and deletion functionality.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from io import StringIO
import csv

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone

from apps.career.models import CareerProfile, CareerUserSkill, CareerLearning, TalentScore, InterviewSession, CareerBrain
from apps.jobs.models import JobApplication
from apps.profiles.models import CVAnalysis
from apps.accounts.models import PasswordReset, EmailVerification
from apps.verification.models import VerificationRequest
from apps.events.models import Event

logger = logging.getLogger(__name__)
User = get_user_model()


class GDPRService:
    """
    Service for GDPR-compliant data export and deletion.
    """
    
    def __init__(self, user):
        """
        Initialize the GDPR service for a specific user.
        
        Args:
            user: Django User instance
        """
        self.user = user
    
    # =========================================================================
    # Data Export Methods
    # =========================================================================
    
    def export_user_data(self) -> Dict[str, Any]:
        """
        Export all user data in a GDPR-compliant format.
        
        Returns:
            Dictionary with all user data organized by category
        """
        export_data = {
            'export_date': timezone.now().isoformat(),
            'user_id': str(self.user.id),
            'email': self.user.email,
            'created_at': self.user.date_joined.isoformat(),
            'last_login': self.user.last_login.isoformat() if self.user.last_login else None,
            'data_categories': {}
        }
        
        # Career profile
        try:
            career_profile = CareerProfile.objects.get(user=self.user)
            export_data['data_categories']['career_profile'] = {
                'cv_parsed_data': career_profile.cv_parsed_data,
                'experience_years': career_profile.experience_years,
                'current_role': career_profile.current_role,
                'current_company': career_profile.current_company,
                'target_roles': career_profile.target_roles,
                'target_locations': career_profile.target_locations,
                'target_salary_min': str(career_profile.target_salary_min) if career_profile.target_salary_min else None,
                'target_salary_currency': career_profile.target_salary_currency,
                'open_to_remote': career_profile.open_to_remote,
                'github_username': career_profile.github_username,
                'github_data': career_profile.github_data,
                'portfolio_url': career_profile.portfolio_url,
                'portfolio_analysis': career_profile.portfolio_analysis,
                'linkedin_data': career_profile.linkedin_data,
                'alert_frequency': career_profile.alert_frequency,
                'min_match_score': career_profile.min_match_score,
                'completeness_score': career_profile.completeness_score,
            }
        except CareerProfile.DoesNotExist:
            export_data['data_categories']['career_profile'] = None
        
        # User skills
        user_skills = CareerUserSkill.objects.filter(user=self.user).select_related('skill')
        export_data['data_categories']['user_skills'] = [
            {
                'skill_name': skill.skill.name,
                'skill_id': str(skill.skill.id),
                'proficiency': skill.proficiency,
                'years_experience': skill.years_experience,
                'last_used_at': skill.last_used_at.isoformat() if skill.last_used_at else None,
                'verified': skill.verified,
                'verification_source': skill.verification_source,
                'source': skill.source,
                'confidence': skill.confidence,
            }
            for skill in user_skills
        ]
        
        # Learning history
        learning = CareerLearning.objects.filter(user=self.user)
        export_data['data_categories']['learning_history'] = [
            {
                'title': l.title,
                'platform': l.platform,
                'skills_gained': l.skills_gained,
                'completed_at': l.completed_at.isoformat() if l.completed_at else None,
                'certificate_url': l.certificate_url,
                'course_id': l.course_id,
                'duration_hours': l.duration_hours,
                'difficulty_level': l.difficulty_level,
            }
            for l in learning
        ]
        
        # Talent scores
        try:
            talent_score = TalentScore.objects.get(user=self.user)
            export_data['data_categories']['talent_scores'] = {
                'overall_score': talent_score.overall_score,
                'skill_score': talent_score.skill_score,
                'experience_score': talent_score.experience_score,
                'education_score': talent_score.education_score,
                'portfolio_score': talent_score.portfolio_score,
                'interview_score': talent_score.interview_score,
                'growth_score': talent_score.growth_score,
                'communication_score': talent_score.communication_score,
                'ai_confidence': talent_score.ai_confidence,
                'explanations': talent_score.explanations,
                'score_history': talent_score.score_history,
                'last_calculated_at': talent_score.last_calculated_at.isoformat(),
            }
        except TalentScore.DoesNotExist:
            export_data['data_categories']['talent_scores'] = None
        
        # Interview sessions
        interviews = InterviewSession.objects.filter(user=self.user)
        export_data['data_categories']['interview_sessions'] = [
            {
                'interview_type': i.interview_type,
                'target_role': i.target_role,
                'target_company': i.target_company,
                'mode': i.mode,
                'difficulty': i.difficulty,
                'questions': i.questions,
                'overall_score': i.overall_score,
                'dimension_scores': i.dimension_scores,
                'recording_url': i.recording_url,
                'transcript': i.transcript,
                'started_at': i.started_at.isoformat() if i.started_at else None,
                'completed_at': i.completed_at.isoformat() if i.completed_at else None,
                'duration_seconds': i.duration_seconds,
            }
            for i in interviews
        ]
        
        # Job applications
        applications = JobApplication.objects.filter(user=self.user)
        export_data['data_categories']['job_applications'] = [
            {
                'job_title': app.job.title if app.job else None,
                'job_id': str(app.job.uuid) if app.job else None,
                'company_name': app.job.company.name if app.job and app.job.company else None,
                'status': app.status,
                'cover_letter': app.cover_letter,
                'resume': app.resume,
                'applied_at': app.created_at.isoformat(),
                'updated_at': app.updated_at.isoformat(),
            }
            for app in applications
        ]
        
        # Career brain
        try:
            career_brain = CareerBrain.objects.get(user=self.user)
            export_data['data_categories']['career_brain'] = {
                'identity': career_brain.identity,
                'skills': career_brain.skills,
                'goals': career_brain.goals,
                'preferences': career_brain.preferences,
                'learning': career_brain.learning,
                'history_summary': career_brain.history_summary,
                'ai_observations': career_brain.ai_observations,
                'confidence_score': career_brain.confidence_score,
                'last_updated_at': career_brain.last_updated_at.isoformat(),
            }
        except CareerBrain.DoesNotExist:
            export_data['data_categories']['career_brain'] = None
        
        return export_data
    
    def export_user_data_csv(self) -> HttpResponse:
        """
        Export user data as CSV files for download.
        
        Returns:
            HttpResponse with ZIP file containing CSV exports
        """
        export_data = self.export_user_data()
        
        # Create CSV for each category
        csv_files = {}
        
        # User skills CSV
        if export_data['data_categories']['user_skills']:
            skills_buffer = StringIO()
            writer = csv.DictWriter(skills_buffer, fieldnames=[
                'skill_name', 'skill_id', 'proficiency', 'years_experience',
                'last_used_at', 'verified', 'verification_source', 'source', 'confidence'
            ])
            writer.writeheader()
            writer.writerows(export_data['data_categories']['user_skills'])
            csv_files['user_skills.csv'] = skills_buffer.getvalue()
        
        # Learning history CSV
        if export_data['data_categories']['learning_history']:
            learning_buffer = StringIO()
            writer = csv.DictWriter(learning_buffer, fieldnames=[
                'title', 'platform', 'skills_gained', 'completed_at',
                'certificate_url', 'course_id', 'duration_hours', 'difficulty_level'
            ])
            writer.writeheader()
            writer.writerows(export_data['data_categories']['learning_history'])
            csv_files['learning_history.csv'] = learning_buffer.getvalue()
        
        # Job applications CSV
        if export_data['data_categories']['job_applications']:
            apps_buffer = StringIO()
            writer = csv.DictWriter(apps_buffer, fieldnames=[
                'job_title', 'job_id', 'company_name', 'status',
                'cover_letter', 'resume', 'applied_at', 'updated_at'
            ])
            writer.writeheader()
            writer.writerows(export_data['data_categories']['job_applications'])
            csv_files['job_applications.csv'] = apps_buffer.getvalue()
        
        return csv_files
    
    def export_user_data_json(self) -> str:
        """
        Export user data as JSON string.
        
        Returns:
            JSON string with all user data
        """
        export_data = self.export_user_data()
        return json.dumps(export_data, indent=2, default=str)
    
    # =========================================================================
    # Data Deletion Methods
    # =========================================================================
    
    def delete_user_data(self) -> Dict[str, Any]:
        """
        Delete all user data in a GDPR-compliant manner.
        
        Returns:
            Dictionary with deletion results
        """
        deletion_results = {
            'deleted_at': timezone.now().isoformat(),
            'user_id': str(self.user.id),
            'deleted_categories': {},
            'errors': []
        }
        
        try:
            # Delete career profile
            try:
                career_profile = CareerProfile.objects.get(user=self.user)
                career_profile.delete()
                deletion_results['deleted_categories']['career_profile'] = True
            except CareerProfile.DoesNotExist:
                deletion_results['deleted_categories']['career_profile'] = False
            
            # Delete user skills
            deleted_skills, _ = CareerUserSkill.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['user_skills'] = deleted_skills
            
            # Delete learning history
            deleted_learning, _ = CareerLearning.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['learning_history'] = deleted_learning
            
            # Delete talent scores
            try:
                talent_score = TalentScore.objects.get(user=self.user)
                talent_score.delete()
                deletion_results['deleted_categories']['talent_scores'] = True
            except TalentScore.DoesNotExist:
                deletion_results['deleted_categories']['talent_scores'] = False
            
            # Delete interview sessions
            deleted_interviews, _ = InterviewSession.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['interview_sessions'] = deleted_interviews
            
            # Delete job applications
            deleted_apps, _ = JobApplication.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['job_applications'] = deleted_apps
            
            # Delete career brain
            try:
                career_brain = CareerBrain.objects.get(user=self.user)
                career_brain.delete()
                deletion_results['deleted_categories']['career_brain'] = True
            except CareerBrain.DoesNotExist:
                deletion_results['deleted_categories']['career_brain'] = False
            
            # Delete CV analyses
            deleted_cv_analyses, _ = CVAnalysis.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['cv_analyses'] = deleted_cv_analyses
            
            # Delete verification requests
            deleted_verifications, _ = VerificationRequest.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['verification_requests'] = deleted_verifications
            
            # Delete events
            deleted_events, _ = Event.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['events'] = deleted_events
            
            # Delete password resets
            deleted_password_resets, _ = PasswordReset.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['password_resets'] = deleted_password_resets
            
            # Delete email verifications
            deleted_email_verifications, _ = EmailVerification.objects.filter(user=self.user).delete()
            deletion_results['deleted_categories']['email_verifications'] = deleted_email_verifications
            
            # Mark user as deleted
            self.user.is_active = False
            self.user.email = f"deleted_{self.user.id}@deleted.local"
            self.user.save()
            deletion_results['user_account'] = {
                'is_active': False,
                'email_masked': True,
            }
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            deletion_results['errors'].append(str(e))
        
        return deletion_results
    
    def delete_user_data_anonymized(self) -> Dict[str, Any]:
        """
        Anonymize user data instead of deleting it (for analytics retention).
        
        Returns:
            Dictionary with anonymization results
        """
        anonymization_results = {
            'anonymized_at': timezone.now().isoformat(),
            'user_id': str(self.user.id),
            'anonymized_categories': {},
            'errors': []
        }
        
        try:
            # Anonymize career profile
            try:
                career_profile = CareerProfile.objects.get(user=self.user)
                career_profile.cv_parsed_data = {}
                career_profile.github_data = {}
                career_profile.portfolio_analysis = {}
                career_profile.linkedin_data = {}
                career_profile.save()
                anonymization_results['anonymized_categories']['career_profile'] = True
            except CareerProfile.DoesNotExist:
                anonymization_results['anonymized_categories']['career_profile'] = False
            
            # Anonymize user skills
            CareerUserSkill.objects.filter(user=self.user).update(
                verified=False,
                verification_source='',
                confidence=0.0,
            )
            anonymization_results['anonymized_categories']['user_skills'] = True
            
            # Anonymize learning history
            CareerLearning.objects.filter(user=self.user).update(
                skills_gained=[],
                certificate_url='',
            )
            anonymization_results['anonymized_categories']['learning_history'] = True
            
            # Anonymize talent scores
            try:
                talent_score = TalentScore.objects.get(user=self.user)
                talent_score.explanations = {}
                talent_score.score_history = []
                talent_score.save()
                anonymization_results['anonymized_categories']['talent_scores'] = True
            except TalentScore.DoesNotExist:
                anonymization_results['anonymized_categories']['talent_scores'] = False
            
            # Anonymize interview sessions
            InterviewSession.objects.filter(user=self.user).update(
                questions=[],
                transcript='',
                recording_url='',
            )
            anonymization_results['anonymized_categories']['interview_sessions'] = True
            
            # Anonymize job applications
            JobApplication.objects.filter(user=self.user).update(
                cover_letter='',
                resume='',
            )
            anonymization_results['anonymized_categories']['job_applications'] = True
            
            # Anonymize career brain
            try:
                career_brain = CareerBrain.objects.get(user=self.user)
                career_brain.identity = {}
                career_brain.skills = {}
                career_brain.goals = []
                career_brain.preferences = {}
                career_brain.learning = {}
                career_brain.history_summary = ''
                career_brain.ai_observations = {}
                career_brain.save()
                anonymization_results['anonymized_categories']['career_brain'] = True
            except CareerBrain.DoesNotExist:
                anonymization_results['anonymized_categories']['career_brain'] = False
            
            # Anonymize user account
            self.user.first_name = 'Deleted'
            self.user.last_name = 'User'
            self.user.email = f"deleted_{self.user.id}@deleted.local"
            self.user.is_active = False
            self.user.save()
            anonymization_results['user_account'] = {
                'is_active': False,
                'email_masked': True,
            }
            
        except Exception as e:
            logger.error(f"Error anonymizing user data: {e}")
            anonymization_results['errors'].append(str(e))
        
        return anonymization_results


def export_user_data_for_user(user_id: int) -> str:
    """
    Export user data for a specific user ID.
    
    Args:
        user_id: User ID to export
        
    Returns:
        JSON string with user data
    """
    try:
        user = User.objects.get(id=user_id)
        service = GDPRService(user)
        return service.export_user_data_json()
    except User.DoesNotExist:
        return json.dumps({'error': 'User not found'})


def delete_user_data_for_user(user_id: int) -> Dict[str, Any]:
    """
    Delete user data for a specific user ID.
    
    Args:
        user_id: User ID to delete
        
    Returns:
        Dictionary with deletion results
    """
    try:
        user = User.objects.get(id=user_id)
        service = GDPRService(user)
        return service.delete_user_data()
    except User.DoesNotExist:
        return {'error': 'User not found'}