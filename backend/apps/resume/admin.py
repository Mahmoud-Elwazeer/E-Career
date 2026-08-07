"""
Resume Builder Admin

This module defines Django admin configurations for resume models.
"""

from django.contrib import admin
from .models import (
    ResumeTemplate,
    Resume,
    ResumeExport,
    ProfileSection,
    SkillVerification,
)


@admin.register(ResumeTemplate)
class ResumeTemplateAdmin(admin.ModelAdmin):
    """Admin for ResumeTemplate model."""
    
    list_display = ['title', 'category', 'is_premium', 'is_active', 'used_count', 'rating']
    list_filter = ['category', 'is_premium', 'is_active']
    search_fields = ['title', 'description']
    readonly_fields = ['used_count', 'rating']


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    """Admin for Resume model."""
    
    list_display = ['title', 'user', 'is_public', 'is_active', 'created_at']
    list_filter = ['is_public', 'is_active', 'created_at']
    search_fields = ['title', 'user__email']
    readonly_fields = ['last_viewed_at']


@admin.register(ResumeExport)
class ResumeExportAdmin(admin.ModelAdmin):
    """Admin for ResumeExport model."""
    
    list_display = ['resume', 'format', 'status', 'created_at', 'completed_at']
    list_filter = ['format', 'status', 'created_at']
    search_fields = ['resume__title', 'resume__user__email']


@admin.register(ProfileSection)
class ProfileSectionAdmin(admin.ModelAdmin):
    """Admin for ProfileSection model."""
    
    list_display = ['user', 'section_type', 'title', 'order', 'is_visible']
    list_filter = ['section_type', 'is_visible', 'order']
    search_fields = ['user__email', 'title']


@admin.register(SkillVerification)
class SkillVerificationAdmin(admin.ModelAdmin):
    """Admin for SkillVerification model."""
    
    list_display = ['user', 'skill_name', 'level', 'verification_method', 'score', 'verified_at']
    list_filter = ['level', 'verification_method', 'verified_at']
    search_fields = ['user__email', 'skill_name']