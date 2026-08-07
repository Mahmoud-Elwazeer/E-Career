"""
Resume Builder URLs

This module defines URL patterns for the resume builder app.
"""

from django.urls import path
from . import views

app_name = 'resume'

urlpatterns = [
    # Templates
    path('templates/', views.get_resume_templates, name='get-resume-templates'),
    
    # Resumes
    path('resumes/', views.get_user_resumes, name='get-user-resumes'),
    path('resumes/<uuid:resume_id>/', views.get_resume, name='get-resume'),
    path('resumes/', views.create_resume, name='create-resume'),
    path('resumes/<uuid:resume_id>/', views.update_resume, name='update-resume'),
    path('resumes/<uuid:resume_id>/delete/', views.delete_resume, name='delete-resume'),
    path('export/', views.export_resume, name='export-resume'),
    
    # Profile sections
    path('profile-sections/', views.get_profile_sections, name='get-profile-sections'),
    path('profile-sections/', views.create_profile_section, name='create-profile-section'),
    
    # Skill verifications
    path('skill-verifications/', views.get_skill_verifications, name='get-skill-verifications'),
    path('skill-verifications/', views.create_skill_verification, name='create-skill-verification'),
]