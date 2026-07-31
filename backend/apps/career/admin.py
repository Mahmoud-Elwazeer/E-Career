"""
Career Intelligence Admin

This module defines Django admin configurations for career intelligence models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CareerProfile,
    CareerUserSkill,
    CareerLearning,
    TalentScore,
    InterviewSession,
)


@admin.register(CareerProfile)
class CareerProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'completeness_score',
        'experience_years',
        'current_role',
        'open_to_remote',
        'cv_parse_status',
        'last_active_at',
    ]
    list_filter = [
        'cv_parse_status',
        'open_to_remote',
        'alert_frequency',
    ]
    search_fields = [
        'user__email',
        'current_role',
        'current_company',
    ]
    readonly_fields = [
        'completeness_score',
        'last_active_at',
        'cv_parsed_at',
    ]
    raw_id_fields = ['user']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'


@admin.register(CareerUserSkill)
class CareerUserSkillAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'skill_name',
        'proficiency',
        'verified',
        'source',
        'confidence',
    ]
    list_filter = [
        'proficiency',
        'verified',
        'source',
    ]
    search_fields = [
        'user__email',
        'skill__name',
    ]
    raw_id_fields = ['user', 'skill']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def skill_name(self, obj):
        return obj.skill.name
    skill_name.short_description = 'Skill'


@admin.register(CareerLearning)
class CareerLearningAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'title',
        'platform',
        'completed_at',
        'difficulty_level',
    ]
    list_filter = [
        'platform',
        'difficulty_level',
    ]
    search_fields = [
        'user__email',
        'title',
        'platform',
    ]
    raw_id_fields = ['user']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


@admin.register(TalentScore)
class TalentScoreAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'overall_score',
        'skill_score',
        'experience_score',
        'education_score',
        'portfolio_score',
        'interview_score',
        'growth_score',
        'communication_score',
        'ai_confidence',
        'last_calculated_at',
    ]
    list_filter = [
        'last_calculated_at',
    ]
    search_fields = [
        'user__email',
    ]
    readonly_fields = ['last_calculated_at']
    raw_id_fields = ['user']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'interview_type',
        'target_role',
        'mode',
        'difficulty',
        'overall_score',
        'duration_seconds',
        'started_at',
    ]
    list_filter = [
        'interview_type',
        'mode',
        'difficulty',
    ]
    search_fields = [
        'user__email',
        'target_role',
        'target_company',
    ]
    raw_id_fields = ['user']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'