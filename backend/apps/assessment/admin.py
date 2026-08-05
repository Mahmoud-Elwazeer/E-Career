"""
Assessment Platform Admin

This module contains Django admin configurations for assessments, questions, and results.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Assessment,
    AssessmentQuestion,
    AssessmentAttempt,
    SkillBadge,
    AssessmentTemplate,
    AssessmentResult,
)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """Admin for Assessment model."""
    
    list_display = ['title', 'assessment_type', 'difficulty', 'status', 'created_by_email', 'created_at']
    list_filter = ['assessment_type', 'difficulty', 'status', 'created_at']
    search_fields = ['title', 'description', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def created_by_email(self, obj):
        return obj.created_by.email
    created_by_email.admin_order_field = 'created_by__email'


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    """Admin for AssessmentQuestion model."""
    
    list_display = ['title', 'assessment_title', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'assessment']
    search_fields = ['title', 'description', 'assessment__title']
    readonly_fields = ['order']
    
    def assessment_title(self, obj):
        return obj.assessment.title
    assessment_title.admin_order_field = 'assessment__title'


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    """Admin for AssessmentAttempt model."""
    
    list_display = ['user_email', 'assessment_title', 'attempt_number', 'status', 'score', 'passed', 'submitted_at']
    list_filter = ['status', 'passed', 'submitted_at']
    search_fields = ['user__email', 'assessment__title']
    readonly_fields = ['started_at', 'submitted_at', 'time_spent_minutes']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'
    
    def assessment_title(self, obj):
        return obj.assessment.title
    assessment_title.admin_order_field = 'assessment__title'


@admin.register(SkillBadge)
class SkillBadgeAdmin(admin.ModelAdmin):
    """Admin for SkillBadge model."""
    
    list_display = ['user_email', 'skill_name', 'level', 'verification_method', 'score', 'earned_at']
    list_filter = ['level', 'verification_method', 'earned_at']
    search_fields = ['user__email', 'skill__name']
    readonly_fields = ['earned_at', 'verified_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'
    
    def skill_name(self, obj):
        return obj.skill.name
    skill_name.admin_order_field = 'skill__name'


@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    """Admin for AssessmentTemplate model."""
    
    list_display = ['title', 'target_role', 'difficulty', 'assessment_type', 'status', 'used_count']
    list_filter = ['difficulty', 'assessment_type', 'status']
    search_fields = ['title', 'description', 'target_role']


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    """Admin for AssessmentResult model."""
    
    list_display = ['attempt_info', 'total_score', 'max_score', 'passed']
    search_fields = ['attempt__user__email', 'attempt__assessment__title']
    
    def attempt_info(self, obj):
        return f"{obj.attempt.user.email} - {obj.attempt.assessment.title}"
    attempt_info.short_description = 'Attempt'
    
    def passed(self, obj):
        return obj.attempt.passed
    passed.boolean = True