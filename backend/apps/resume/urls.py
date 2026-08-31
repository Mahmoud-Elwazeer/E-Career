"""
Resume Builder URLs
"""

from django.urls import path
from . import views

app_name = 'resume'

urlpatterns = [
    # Templates
    path('templates/', views.get_resume_templates, name='get-resume-templates'),

    # Resumes (list + create on same path)
    path('resumes/', views.resumes_list_create, name='resumes-list-create'),
    path('resumes/<uuid:resume_id>/', views.get_resume, name='get-resume'),
    path('resumes/<uuid:resume_id>/update/', views.update_resume, name='update-resume'),
    path('resumes/<uuid:resume_id>/delete/', views.delete_resume, name='delete-resume'),
    path('export/', views.export_resume, name='export-resume'),

    # Profile sections (list + create on same path)
    path('profile-sections/', views.profile_sections_list_create, name='profile-sections-list-create'),

    # Skill verifications (list + create on same path)
    path('skill-verifications/', views.skill_verifications_list_create, name='skill-verifications-list-create'),
]
