"""
Resume Builder Models

This module defines models for resume building, templates, and profile management.
"""

import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import UUIDModel, TimeStampedModel

logger = logging.getLogger(__name__)


class ResumeTemplate(UUIDModel):
    """
    Resume template for different career stages and industries.
    
    This model stores various resume templates that users can choose from.
    """
    
    # Template info
    title = models.CharField(max_length=100)
    description = models.TextField()
    
    # Category
    CATEGORY_CHOICES = [
        ('modern', 'Modern'),
        ('professional', 'Professional'),
        ('creative', 'Creative'),
        ('academic', 'Academic'),
        ('minimalist', 'Minimalist'),
        ('technical', 'Technical'),
    ]
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        db_index=True
    )
    
    # Preview image
    preview_image = models.URLField(
        blank=True,
        help_text="URL to template preview image"
    )
    
    # Features
    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Usage stats
    used_count = models.IntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=4.5
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "resume_template"
        verbose_name = "Resume Template"
        verbose_name_plural = "Resume Templates"
    
    def __str__(self):
        return f"{self.title} ({self.category})"


class Resume(UUIDModel):
    """
    User's resume with content and settings.
    
    This model stores user resumes with their content and template selection.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes',
        db_index=True
    )
    
    # Template
    template = models.ForeignKey(
        ResumeTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resumes',
        db_index=True
    )
    
    # Title
    title = models.CharField(max_length=200, default="My Resume")
    
    # Content sections
    personal_info = models.JSONField(
        default=dict,
        help_text="Personal information (name, email, phone, etc.)"
    )
    summary = models.TextField(
        blank=True,
        help_text="Professional summary"
    )
    experience = models.JSONField(
        default=list,
        help_text="Work experience list"
    )
    education = models.JSONField(
        default=list,
        help_text="Education list"
    )
    skills = models.JSONField(
        default=list,
        help_text="Skills list"
    )
    projects = models.JSONField(
        default=list,
        help_text="Projects list"
    )
    certifications = models.JSONField(
        default=list,
        help_text="Certifications list"
    )
    languages = models.JSONField(
        default=list,
        help_text="Languages list"
    )
    interests = models.JSONField(
        default=list,
        help_text="Interests list"
    )
    
    # Settings
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Privacy
    privacy_settings = models.JSONField(
        default=dict,
        help_text="Privacy settings for resume sections"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "resume"
        verbose_name = "Resume"
        verbose_name_plural = "Resumes"
    
    def __str__(self):
        return f"{self.title} ({self.user.email})"


class ResumeExport(UUIDModel):
    """
    Exported resume file.
    
    This model tracks resume exports in various formats.
    """
    
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='exports',
        db_index=True
    )
    
    # Export type
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('html', 'HTML'),
        ('json', 'JSON'),
    ]
    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        db_index=True
    )
    
    # File info
    file_url = models.URLField(
        blank=True,
        help_text="URL to exported file"
    )
    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Error message (if failed)
    error_message = models.TextField(
        blank=True,
        help_text="Error message if export failed"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "resume_export"
        verbose_name = "Resume Export"
        verbose_name_plural = "Resume Exports"
    
    def __str__(self):
        return f"{self.resume.title} - {self.format}"


class ProfileSection(UUIDModel):
    """
    Profile section with custom content.
    
    This model stores customizable profile sections.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile_sections',
        db_index=True
    )
    
    # Section type
    SECTION_CHOICES = [
        ('summary', 'Summary'),
        ('experience', 'Experience'),
        ('education', 'Education'),
        ('skills', 'Skills'),
        ('projects', 'Projects'),
        ('certifications', 'Certifications'),
        ('languages', 'Languages'),
        ('interests', 'Interests'),
    ]
    section_type = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        db_index=True
    )
    
    # Content
    title = models.CharField(max_length=200, blank=True)
    content = models.JSONField(
        default=dict,
        help_text="Section content"
    )
    
    # Order
    order = models.IntegerField(default=0)
    
    # Visibility
    is_visible = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "profile_section"
        ordering = ['order']
        verbose_name = "Profile Section"
        verbose_name_plural = "Profile Sections"
    
    def __str__(self):
        return f"{self.user.email} - {self.section_type}"


class SkillVerification(UUIDModel):
    """
    Verified skill with evidence.
    
    This model tracks skill verifications from various sources.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_verifications',
        db_index=True
    )
    
    # Skill info
    skill_name = models.CharField(max_length=100)
    skill_category = models.CharField(max_length=50, blank=True)
    
    # Verification method
    METHOD_CHOICES = [
        ('assessment', 'Assessment passed'),
        ('github', 'GitHub analysis'),
        ('project', 'Project evidence'),
        ('endorsement', 'Endorsement'),
        ('certification', 'Certification'),
        ('cv', 'CV extraction'),
    ]
    verification_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        db_index=True
    )
    
    # Evidence
    evidence_url = models.URLField(
        blank=True,
        help_text="URL to evidence (GitHub, portfolio, etc.)"
    )
    evidence_text = models.TextField(
        blank=True,
        help_text="Evidence text (for CV extraction)"
    )
    
    # Score
    score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Skill score (0-100)"
    )
    
    # Level
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='intermediate',
        db_index=True
    )
    
    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Verification expiration date"
    )
    
    # Metadata
    verified_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications_issued',
        db_index=True
    )
    
    class Meta:
        db_table = "skill_verification"
        unique_together = [("user", "skill_name")]
        verbose_name = "Skill Verification"
        verbose_name_plural = "Skill Verifications"
    
    def __str__(self):
        return f"{self.user.email} - {self.skill_name} ({self.level})"