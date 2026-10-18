"""
CV Parser Views — status and delete endpoints.

CV upload is handled by /profile/upload_cv/ (profiles app).
Text extraction: profiles/cv_parser.py (canonical).
AI parsing: intelligence/career_ai.py (canonical).
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.storage import default_storage

from .models import CareerProfile

logger = logging.getLogger(__name__)


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
            # Directive item 16 fix: use .name (storage-relative) instead of
            # .path (filesystem-only — raises NotImplementedError on a
            # non-local storage backend such as S3), and check existence
            # first in a try/finally so the DB field is always cleared even
            # if the underlying file is already missing — matches the
            # safer pattern already used by the retention engine's
            # _enforce_cv_documents handler (apps/legal/retention_service.py).
            try:
                if default_storage.exists(career_profile.cv_file.name):
                    default_storage.delete(career_profile.cv_file.name)
            finally:
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