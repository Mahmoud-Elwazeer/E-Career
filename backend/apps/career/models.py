"""
Career Intelligence Models

This module defines the models for career profiles, skills, learning history,
and talent intelligence features.
"""

import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import UUIDModel, TimeStampedModel
from apps.skills.models import Skill

logger = logging.getLogger(__name__)


class CareerProfile(UUIDModel):
    """
    User career profile (extended from existing UserProfile).
    
    This model provides a comprehensive career intelligence profile with
    CV data, skills, experience, goals, and preferences.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='career_profile',
        db_index=True
    )
    
    # CV data (structured extraction)
    cv_file = models.FileField(
        upload_to='cvs/%Y/%m/',
        null=True,
        blank=True,
        help_text="Uploaded CV/resume file"
    )
    cv_parsed_data = models.JSONField(
        default=dict,
        help_text="Full structured extraction from CV (skills, experience, education, etc.)"
    )
    cv_parse_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        db_index=True
    )
    cv_parsed_at = models.DateTimeField(null=True, blank=True)
    
    # Experience
    experience_years = models.IntegerField(default=0)
    current_role = models.CharField(max_length=200, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    
    # Goals
    target_roles = models.JSONField(
        default=list,
        help_text="[{role, priority, timeline}] - Target job titles"
    )
    target_locations = models.JSONField(
        default=list,
        help_text="[{city, country, priority}] - Target locations"
    )
    target_salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    target_salary_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="ISO 4217 currency code (e.g., USD, EUR, EGP)"
    )
    open_to_remote = models.BooleanField(default=True)
    
    # External signals
    github_username = models.CharField(
        max_length=100,
        blank=True,
        help_text="GitHub username for repository analysis"
    )
    github_data = models.JSONField(
        default=dict,
        help_text="Analyzed GitHub data (repos, languages, activity)"
    )
    portfolio_url = models.URLField(
        blank=True,
        help_text="Personal portfolio/website URL"
    )
    portfolio_analysis = models.JSONField(
        default=dict,
        help_text="AI-analyzed portfolio projects"
    )
    linkedin_data = models.JSONField(
        default=dict,
        help_text="User-provided LinkedIn export data"
    )
    
    # Preferences
    alert_frequency = models.CharField(
        max_length=20,
        default='instant',
        choices=[
            ('instant', 'Realtime'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ]
    )
    min_match_score = models.FloatField(
        default=0.6,
        help_text="Only alert for jobs scoring above this threshold (0-1)"
    )
    
    # Metadata
    completeness_score = models.FloatField(
        default=0.0,
        help_text="Profile completeness (0-1)"
    )
    last_active_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "career_profile"
        ordering = ["-last_active_at"]
        verbose_name = "Career Profile"
        verbose_name_plural = "Career Profiles"
    
    def __str__(self):
        return f"Career Profile: {self.user.email}"
    
    def save(self, *args, **kwargs):
        # Update last_active_at on save
        self.last_active_at = timezone.now()
        super().save(*args, **kwargs)
    
    def update_completeness(self):
        """
        Calculate and update profile completeness score.
        
        Each field contributes a percentage to the completeness_score.
        Returns a list of missing/incomplete fields for UI prompts.
        """
        fields = {
            'target_roles': 10,
            'target_locations': 10,
            'target_salary_min': 10,
            'open_to_remote': 5,
            'experience_years': 10,
            'current_role': 5,
            'current_company': 5,
            'github_username': 10,
            'portfolio_url': 5,
            'alert_frequency': 5,
            'min_match_score': 5,
            'cv_parsed_data': 20,
        }
        
        total_score = 0
        missing_fields = []
        
        for field, weight in fields.items():
            value = getattr(self, field, None)
            if value is None or (isinstance(value, (str, list, dict)) and not value):
                missing_fields.append(field)
            else:
                total_score += weight
        
        self.completeness_score = total_score / 100.0
        self.save(update_fields=['completeness_score'])
        
        return {
            'score': self.completeness_score,
            'missing_fields': missing_fields,
            'total_fields': len(fields),
            'completed_fields': len(fields) - len(missing_fields)
        }
    
    def get_profile_text(self):
        """
        Generate a text representation of the profile for embedding.
        
        Combines: skills + experience + target roles + bio
        """
        parts = []
        
        # Skills
        skills = self.career_userskill_set.filter(verified=True)[:20]
        if skills:
            skill_names = [s.skill.name for s in skills]
            parts.append(f"Skills: {', '.join(skill_names)}")
        
        # Experience
        if self.current_role:
            parts.append(f"Current Role: {self.current_role}")
        if self.current_company:
            parts.append(f"Current Company: {self.current_company}")
        if self.experience_years:
            parts.append(f"Experience: {self.experience_years} years")
        
        # Target roles
        if self.target_roles:
            roles = [r.get('role', '') for r in self.target_roles]
            parts.append(f"Target Roles: {', '.join(roles)}")
        
        # Target locations
        if self.target_locations:
            locations = [f"{l.get('city', '')}, {l.get('country', '')}" for l in self.target_locations if l.get('city') or l.get('country')]
            if locations:
                parts.append(f"Target Locations: {', '.join(locations)}")
        
        # Open to remote
        parts.append(f"Open to Remote: {'Yes' if self.open_to_remote else 'No'}")
        
        return '\n'.join(parts)


class CareerUserSkill(UUIDModel):
    """
    User skills (many-to-many with proficiency).
    
    Links users to skills with proficiency levels, verification status,
    and source information.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='career_userskills',
        db_index=True
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='career_users',
        db_index=True
    )
    
    # Proficiency levels
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    proficiency = models.CharField(
        max_length=20,
        choices=PROFICIENCY_CHOICES,
        default='intermediate',
        db_index=True
    )
    
    # Experience tracking
    years_experience = models.FloatField(default=0)
    last_used_at = models.DateField(null=True, blank=True)
    
    # Verification
    verified = models.BooleanField(default=False)
    verification_source = models.CharField(
        max_length=50,
        blank=True,
        help_text="'assessment', 'github', 'endorsement', 'cv'"
    )
    
    # Source of skill data
    SOURCE_CHOICES = [
        ('cv_extraction', 'CV Extraction'),
        ('self_reported', 'Self Reported'),
        ('assessment', 'Assessment'),
        ('github', 'GitHub Analysis'),
        ('inferred', 'Inferred'),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='cv_extraction',
        db_index=True
    )
    
    # Confidence score
    confidence = models.FloatField(
        default=0.5,
        help_text="Confidence in skill data accuracy (0-1)"
    )
    
    class Meta:
        db_table = "career_user_skill"
        unique_together = [("user", "skill")]
        verbose_name = "Career User Skill"
        verbose_name_plural = "Career User Skills"
    
    def __str__(self):
        return f"{self.user.email} - {self.skill.name} ({self.proficiency})"


class CareerLearning(UUIDModel):
    """
    Learning history model.
    
    Tracks courses, certifications, and learning activities.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='career_learning',
        db_index=True
    )
    
    title = models.CharField(max_length=300)
    platform = models.CharField(
        max_length=100,
        help_text="Coursera, Udemy, LinkedIn Learning, etc."
    )
    
    skills_gained = models.JSONField(
        default=list,
        help_text="[{skill_id, skill_name, level_delta}]"
    )
    
    completed_at = models.DateField(null=True, blank=True)
    certificate_url = models.URLField(
        blank=True,
        help_text="URL to certificate (if available)"
    )
    
    # Course metadata
    course_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Platform-specific course ID"
    )
    duration_hours = models.IntegerField(null=True, blank=True)
    difficulty_level = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "career_learning"
        ordering = ["-completed_at"]
        verbose_name = "Career Learning"
        verbose_name_plural = "Career Learning"
    
    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.platform})"


class TalentScore(UUIDModel):
    """
    Multi-dimensional talent scores.
    
    Provides comprehensive scoring across multiple dimensions with
    explainability and historical tracking.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='talent_score',
        db_index=True
    )
    
    # Composite score
    overall_score = models.FloatField(
        default=0.0,
        help_text="Overall talent score (0-1)"
    )
    
    # Individual dimensions
    skill_score = models.FloatField(default=0.0)
    experience_score = models.FloatField(default=0.0)
    education_score = models.FloatField(default=0.0)
    portfolio_score = models.FloatField(default=0.0)
    interview_score = models.FloatField(default=0.0)
    growth_score = models.FloatField(default=0.0)
    communication_score = models.FloatField(default=0.0)
    
    # AI confidence
    ai_confidence = models.FloatField(
        default=0.5,
        help_text="Confidence in the scoring (0-1)"
    )
    
    # Explainability
    explanations = models.JSONField(
        default=dict,
        help_text="{dimension: {evidence, explanation, actions, trend}}"
    )
    
    # Historical scores
    score_history = models.JSONField(
        default=list,
        help_text="[{date, scores...}] for trend analysis"
    )
    
    last_calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "career_talent_score"
        verbose_name = "Talent Score"
        verbose_name_plural = "Talent Scores"
    
    def __str__(self):
        return f"{self.user.email} - Overall: {self.overall_score:.2f}"
    
    def get_dimension_breakdown(self):
        """Get a breakdown of scores by dimension."""
        return {
            'skill_score': self.skill_score,
            'experience_score': self.experience_score,
            'education_score': self.education_score,
            'portfolio_score': self.portfolio_score,
            'interview_score': self.interview_score,
            'growth_score': self.growth_score,
            'communication_score': self.communication_score,
        }


class InterviewSession(UUIDModel):
    """
    Interview session model.
    
    Tracks interview sessions with questions, answers, and AI feedback.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_sessions',
        db_index=True
    )
    
    # Configuration
    INTERVIEW_TYPE_CHOICES = [
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('coding', 'Coding'),
        ('system_design', 'System Design'),
        ('case_study', 'Case Study'),
    ]
    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPE_CHOICES,
        db_index=True
    )
    
    target_role = models.CharField(max_length=200, blank=True)
    target_company = models.CharField(max_length=200, blank=True)
    
    MODE_CHOICES = [
        ('text', 'Text'),
        ('voice', 'Voice'),
        ('coding', 'Coding'),
    ]
    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default='text',
        db_index=True
    )
    
    DIFFICULTY_CHOICES = [
        ('junior', 'Junior'),
        ('mid', 'Mid'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
    ]
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='mid',
        db_index=True
    )
    
    # Content
    questions = models.JSONField(
        default=list,
        help_text="[{question, user_answer, ai_feedback, score_breakdown}]"
    )
    
    # Scoring
    overall_score = models.FloatField(null=True, blank=True)
    dimension_scores = models.JSONField(
        default=dict,
        help_text="{relevance, depth, structure, technical, communication}"
    )
    
    # Media (voice mode)
    recording_url = models.URLField(
        blank=True,
        help_text="S3 URL for recording (if available)"
    )
    transcript = models.TextField(blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = "career_interview_session"
        ordering = ["-started_at"]
        verbose_name = "Interview Session"
        verbose_name_plural = "Interview Sessions"
    
    def __str__(self):
        return f"{self.user.email} - {self.interview_type} ({self.started_at})"