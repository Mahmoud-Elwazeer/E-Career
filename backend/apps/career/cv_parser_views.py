"""
CV Parser Views

This module contains Django REST Framework views for CV parsing functionality.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .cv_parser import cv_parser_service
from .models import CareerProfile

logger = logging.getLogger(__name__)

# File size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}


def validate_file_extension(file_name: str) -> bool:
    """Check if file has an allowed extension."""
    ext = Path(file_name).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """Check if file size is within limit."""
    return file_size <= MAX_FILE_SIZE


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cv_upload(request):
    """
    Upload and parse CV file.
    
    Accepts PDF, DOCX, and image files.
    Extracts structured data and updates user's career profile.
    """
    if 'cv_file' not in request.FILES:
        return Response({
            'success': False,
            'error': 'No file uploaded',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    cv_file = request.FILES['cv_file']
    
    # Validate file extension
    if not validate_file_extension(cv_file.name):
        return Response({
            'success': False,
            'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate file size
    if not validate_file_size(cv_file.size):
        return Response({
            'success': False,
            'error': f'File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Save file temporarily
        temp_path = Path('temp_cvs') / f"{request.user.id}_{cv_file.name}"
        temp_full_path = default_storage.path(str(temp_path))
        
        # Ensure directory exists
        Path(temp_full_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with default_storage.open(str(temp_path), 'wb+') as destination:
            for chunk in cv_file.chunks():
                destination.write(chunk)
        
        # Parse the file based on extension
        ext = Path(cv_file.name).suffix.lower()
        
        if ext == '.pdf':
            parsed = cv_parser_service.parse_pdf(temp_full_path)
        elif ext in {'.docx', '.doc'}:
            parsed = cv_parser_service.parse_docx(temp_full_path)
        elif ext in {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}:
            parsed = cv_parser_service.parse_image(temp_full_path)
        else:
            return Response({
                'success': False,
                'error': 'Unsupported file type',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract structured data
        structured_data = cv_parser_service.extract_structured_data(parsed['text'])
        
        # Map skills to ESCO
        matched_skills = cv_parser_service.map_skills_to_esco(structured_data.get('skills', []))
        
        # Update user's career profile
        career_profile, created = CareerProfile.objects.get_or_create(user=request.user)
        
        # Update profile with parsed data
        career_profile.cv_file = cv_file
        career_profile.cv_parsed_data = structured_data
        career_profile.cv_parse_status = 'completed'
        career_profile.cv_parsed_at = None  # Will be set on save
        
        # Update profile fields from parsed data
        if structured_data.get('name'):
            career_profile.cv_parsed_data['name'] = structured_data['name']
        if structured_data.get('email'):
            career_profile.cv_parsed_data['email'] = structured_data['email']
        if structured_data.get('phone'):
            career_profile.cv_parsed_data['phone'] = structured_data['phone']
        if structured_data.get('location'):
            career_profile.cv_parsed_data['location'] = structured_data['location']
        
        career_profile.save()
        
        # Update user skills from matched skills
        updated_count = cv_parser_service.update_user_skills(request.user, matched_skills)
        
        # Clean up temp file
        try:
            default_storage.delete(str(temp_path))
        except Exception:
            pass
        
        return Response({
            'success': True,
            'data': {
                'profile_id': career_profile.id,
                'parse_status': 'completed',
                'extracted_data': structured_data,
                'matched_skills': matched_skills,
                'skills_updated': updated_count,
            },
        })
        
    except Exception as e:
        logger.error(f"Error parsing CV: {e}")
        
        # Clean up temp file on error
        try:
            default_storage.delete(str(temp_path))
        except Exception:
            pass
        
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cv_status(request):
    """
    Get CV parsing status for the authenticated user.
    """
    try:
        career_profile = CareerProfile.objects.get(user=request.user)
        
        return Response({
            'success': True,
            'data': {
                'parse_status': career_profile.cv_parse_status,
                'cv_parsed_at': career_profile.cv_parsed_at,
                'cv_parsed_data': career_profile.cv_parsed_data,
            },
        })
        
    except CareerProfile.DoesNotExist:
        return Response({
            'success': True,
            'data': {
                'parse_status': 'not_found',
                'cv_parsed_at': None,
                'cv_parsed_data': {},
            },
        })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cv_delete(request):
    """
    Delete the user's CV file.
    """
    try:
        career_profile = CareerProfile.objects.get(user=request.user)
        
        if career_profile.cv_file:
            # Delete the file
            default_storage.delete(career_profile.cv_file.path)
            career_profile.cv_file = None
            career_profile.cv_parse_status = 'pending'
            career_profile.cv_parsed_data = {}
            career_profile.save()
        
        return Response({
            'success': True,
            'message': 'CV file deleted',
        })
        
    except CareerProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': 'No CV file found',
        }, status=status.HTTP_404_NOT_FOUND)