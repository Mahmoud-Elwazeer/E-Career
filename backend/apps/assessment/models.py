"""
Assessment Platform Models

This module defines models for skill assessments, coding challenges, and verification.
"""

import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import UUIDModel, TimeStampedModel
from apps.skills.models import Skill

logger = logging.getLogger(__name__)


class Assessment(UUIDModel):
    """
    Skill assessment template.
    
    This model defines assessment templates that can be assigned to users
    or used for self-assessment.
    """
    
    # Creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessments_created',
        db_index=True
    )
    
    # Assessment type
    TYPE_CHOICES = [
        ('coding', 'Coding Challenge'),
        ('multiple_choice', 'Multiple Choice Quiz'),
        ('essay', 'Essay/Text Response'),
        ('practical', 'Practical Task'),
    ]
    assessment_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True
    )
    
    # Content
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Skills assessed
    skills = models.ManyToManyField(
        Skill,
        related_name='assessments',
        blank=True
    )
    
    # Difficulty
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='intermediate',
        db_index=True
    )
    
    # Configuration
    time_limit_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time limit in minutes (null = no limit)"
    )
    max_attempts = models.IntegerField(
        default=3,
        help_text="Maximum number of attempts allowed"
    )
    passing_score = models.IntegerField(
        default=70,
        help_text="Minimum score to pass (0-100)"
    )
    
    # Scoring
    total_points = models.IntegerField(default=100)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "assessment"
        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"
    
    def __str__(self):
        return f"{self.title} ({self.assessment_type})"


class AssessmentQuestion(UUIDModel):
    """
    Question within an assessment.
    
    This model stores individual questions for assessments.
    """
    
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='questions',
        db_index=True
    )
    
    # Question type
    TYPE_CHOICES = [
        ('coding', 'Coding Challenge'),
        ('multiple_choice', 'Multiple Choice'),
        ('single_choice', 'Single Choice'),
        ('essay', 'Essay/Text Response'),
    ]
    question_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True
    )
    
    # Content
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Coding-specific fields
    starter_code = models.TextField(
        blank=True,
        help_text="Starter code for coding questions"
    )
    test_cases = models.JSONField(
        default=list,
        help_text="Test cases for coding questions"
    )
    
    # Multiple choice fields
    options = models.JSONField(
        default=list,
        help_text="Answer options for multiple choice"
    )
    correct_answer = models.JSONField(
        help_text="Correct answer(s)"
    )
    
    # Points
    points = models.IntegerField(default=10)
    
    # Order
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = "assessment_question"
        ordering = ['order']
        verbose_name = "Assessment Question"
        verbose_name_plural = "Assessment Questions"
    
    def __str__(self):
        return f"{self.assessment.title}: {self.title}"


class AssessmentAttempt(UUIDModel):
    """
    User's attempt at an assessment.
    
    This model tracks individual assessment attempts with answers and scores.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessment_attempts',
        db_index=True
    )
    
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='attempts',
        db_index=True
    )
    
    # Attempt number
    attempt_number = models.IntegerField()
    
    # Status
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        db_index=True
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.IntegerField(null=True, blank=True)
    
    # Scoring
    score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Score (0-100)"
    )
    passed = models.BooleanField(default=False)
    
    # Answers
    answers = models.JSONField(
        default=dict,
        help_text="User's answers"
    )
    
    # Feedback
    feedback = models.JSONField(
        default=dict,
        help_text="AI-generated feedback"
    )
    
    class Meta:
        db_table = "assessment_attempt"
        unique_together = [("user", "assessment", "attempt_number")]
        verbose_name = "Assessment Attempt"
        verbose_name_plural = "Assessment Attempts"
    
    def __str__(self):
        return f"{self.user.email} - {self.assessment.title} (Attempt {self.attempt_number})"


class SkillBadge(UUIDModel):
    """
    Verified skill badge for users.
    
    This model tracks skill verifications and badges earned by users.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_badges',
        db_index=True
    )
    
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='badges',
        db_index=True
    )
    
    # Badge level
    LEVEL_CHOICES = [
        ('verified', 'Verified'),
        ('proficient', 'Proficient'),
        ('expert', 'Expert'),
    ]
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='verified',
        db_index=True
    )
    
    # Verification method
    VERIFICATION_METHOD_CHOICES = [
        ('assessment', 'Assessment passed'),
        ('github', 'GitHub analysis'),
        ('endorsement', 'Endorsement'),
        ('cv', 'CV extraction'),
    ]
    verification_method = models.CharField(
        max_length=20,
        choices=VERIFICATION_METHOD_CHOICES,
        default='assessment',
        db_index=True
    )
    
    # Score
    score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Score from assessment (0-100)"
    )
    
    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Badge expiration date (null = never expires)"
    )
    
    # Metadata
    earned_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "skill_badge"
        unique_together = [("user", "skill")]
        verbose_name = "Skill Badge"
        verbose_name_plural = "Skill Badges"
    
    def __str__(self):
        return f"{self.user.email} - {self.skill.name} ({self.level})"


class AssessmentTemplate(UUIDModel):
    """
    Pre-built assessment templates for common roles.
    
    This model stores templates that employers can use to quickly create assessments.
    """
    
    # Template info
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Target role
    target_role = models.CharField(max_length=100)
    
    # Skills covered
    skills = models.ManyToManyField(
        Skill,
        related_name='assessment_templates',
        blank=True
    )
    
    # Configuration
    time_limit_minutes = models.IntegerField(default=30)
    max_attempts = models.IntegerField(default=3)
    passing_score = models.IntegerField(default=70)
    
    # Difficulty
    difficulty = models.CharField(
        max_length=20,
        choices=Assessment.DIFFICULTY_CHOICES,
        default='intermediate'
    )
    
    # Type
    assessment_type = models.CharField(
        max_length=20,
        choices=Assessment.TYPE_CHOICES,
        default='coding'
    )
    
    # Status
    STATUS_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('featured', 'Featured'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='public',
        db_index=True
    )
    
    # Usage
    used_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = "assessment_template"
        verbose_name = "Assessment Template"
        verbose_name_plural = "Assessment Templates"
    
    def __str__(self):
        return f"{self.title} ({self.target_role})"


class AssessmentResult(UUIDModel):
    """
    Detailed assessment result with breakdown.
    
    This model stores detailed results for assessments.
    """
    
    attempt = models.OneToOneField(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name='result',
        db_index=True
    )
    
    # Score breakdown
    total_score = models.IntegerField()
    max_score = models.IntegerField()
    
    # Per-question scores
    question_scores = models.JSONField(
        default=dict,
        help_text="Scores per question"
    )
    
    # Time breakdown
    time_per_question = models.JSONField(
        default=dict,
        help_text="Time spent per question"
    )
    
    # AI analysis
    ai_analysis = models.JSONField(
        default=dict,
        help_text="AI-generated analysis"
    )
    
    # Strengths and weaknesses
    strengths = models.JSONField(
        default=list,
        help_text="Identified strengths"
    )
    weaknesses = models.JSONField(
        default=list,
        help_text="Identified weaknesses"
    )
    
    # Recommendations
    recommendations = models.JSONField(
        default=list,
        help_text="Improvement recommendations"
    )
    
    class Meta:
        db_table = "assessment_result"
        verbose_name = "Assessment Result"
        verbose_name_plural = "Assessment Results"
    
    def __str__(self):
        return f"Result for {self.attempt}"