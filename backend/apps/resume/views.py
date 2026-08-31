"""
Resume Builder Views

This module contains Django REST Framework views for resume management.
"""

import logging
from django.utils import timezone
from rest_framework import status, serializers as drf_serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    ResumeTemplate,
    Resume,
    ResumeExport,
    ProfileSection,
    SkillVerification,
)
from .serializers import (
    ResumeTemplateSerializer,
    ResumeSerializer,
    ResumeExportSerializer,
    ProfileSectionSerializer,
    SkillVerificationSerializer,
    ResumeCreateSerializer,
    ResumeUpdateSerializer,
    ResumeExportRequestSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_resume_templates(request):
    """
    Get available resume templates.
    """
    try:
        templates = ResumeTemplate.objects.filter(is_active=True)
        return Response({
            'success': True,
            'data': ResumeTemplateSerializer(templates, many=True).data,
        })
    except Exception as e:
        logger.error("get_resume_templates_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def resumes_list_create(request):
    """
    GET: Get resumes for the authenticated user.
    POST: Create a new resume.
    """
    if request.method == 'POST':
        return _create_resume(request)
    try:
        resumes = Resume.objects.filter(user=request.user).order_by('-updated_at')
        return Response({
            'success': True,
            'data': ResumeSerializer(resumes, many=True).data,
        })
    except Exception as e:
        logger.error("get_user_resumes_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume(request, resume_id):
    """
    Get a specific resume by ID.
    """
    try:
        resume = Resume.objects.get(uuid=resume_id, user=request.user)
        resume.last_viewed_at = timezone.now()
        resume.save()
        return Response({
            'success': True,
            'data': ResumeSerializer(resume).data,
        })
    except Resume.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Resume not found',
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("get_resume_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _create_resume(request):
    """
    Create a new resume for the authenticated user.
    """
    try:
        serializer = ResumeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        resume = Resume.objects.create(
            user=request.user,
            title=serializer.validated_data.get('title', 'My Resume'),
            personal_info=serializer.validated_data.get('personal_info', {}),
            summary=serializer.validated_data.get('summary', ''),
            experience=serializer.validated_data.get('experience', []),
            education=serializer.validated_data.get('education', []),
            skills=serializer.validated_data.get('skills', []),
            projects=serializer.validated_data.get('projects', []),
            certifications=serializer.validated_data.get('certifications', []),
            languages=serializer.validated_data.get('languages', []),
            interests=serializer.validated_data.get('interests', []),
            is_public=serializer.validated_data.get('is_public', False),
            privacy_settings=serializer.validated_data.get('privacy_settings', {}),
        )
        
        # Set template if provided
        template_id = serializer.validated_data.get('template_id')
        if template_id:
            try:
                from apps.resume.models import ResumeTemplate
                resume.template = ResumeTemplate.objects.get(id=template_id)
                resume.save()
            except ResumeTemplate.DoesNotExist:
                pass
        
        return Response({
            'success': True,
            'data': ResumeSerializer(resume).data,
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error("create_resume_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_resume(request, resume_id):
    """
    Update a resume.
    """
    try:
        resume = Resume.objects.get(uuid=resume_id, user=request.user)
        
        serializer = ResumeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Update fields
        if 'title' in serializer.validated_data:
            resume.title = serializer.validated_data['title']
        if 'personal_info' in serializer.validated_data:
            resume.personal_info = serializer.validated_data['personal_info']
        if 'summary' in serializer.validated_data:
            resume.summary = serializer.validated_data['summary']
        if 'experience' in serializer.validated_data:
            resume.experience = serializer.validated_data['experience']
        if 'education' in serializer.validated_data:
            resume.education = serializer.validated_data['education']
        if 'skills' in serializer.validated_data:
            resume.skills = serializer.validated_data['skills']
        if 'projects' in serializer.validated_data:
            resume.projects = serializer.validated_data['projects']
        if 'certifications' in serializer.validated_data:
            resume.certifications = serializer.validated_data['certifications']
        if 'languages' in serializer.validated_data:
            resume.languages = serializer.validated_data['languages']
        if 'interests' in serializer.validated_data:
            resume.interests = serializer.validated_data['interests']
        if 'is_public' in serializer.validated_data:
            resume.is_public = serializer.validated_data['is_public']
        if 'privacy_settings' in serializer.validated_data:
            resume.privacy_settings = serializer.validated_data['privacy_settings']
        
        resume.save()
        
        return Response({
            'success': True,
            'data': ResumeSerializer(resume).data,
        })
    except Resume.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Resume not found',
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("update_resume_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_resume(request, resume_id):
    """
    Delete a resume.
    """
    try:
        resume = Resume.objects.get(uuid=resume_id, user=request.user)
        resume.delete()
        return Response({
            'success': True,
            'message': 'Resume deleted successfully',
        })
    except Resume.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Resume not found',
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("delete_resume_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_resume(request):
    """
    Export a resume to a specific format. Returns the file directly.
    """
    from django.http import HttpResponse
    from .export_service import resume_export_service

    try:
        serializer = ResumeExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume_id = request.data.get('resume_id')
        resume = Resume.objects.get(uuid=resume_id, user=request.user)
        export_format = serializer.validated_data['format']

        format_handlers = {
            'pdf': ('application/pdf', '.pdf', resume_export_service.export_pdf),
            'html': ('text/html', '.html', resume_export_service.export_html),
            'json': ('application/json', '.json', resume_export_service.export_json),
            'docx': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx', resume_export_service.export_docx),
        }

        handler = format_handlers.get(export_format)
        if not handler:
            return Response({'success': False, 'error': f'Unsupported format: {export_format}'}, status=400)

        content_type, ext, export_fn = handler
        content = export_fn(resume)

        if content is None:
            return Response({'success': False, 'error': f'{export_format.upper()} generation failed'}, status=500)

        if isinstance(content, str):
            content = content.encode('utf-8')

        ResumeExport.objects.create(
            resume=resume,
            format=export_format,
            status='completed',
            completed_at=timezone.now(),
        )

        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{resume.title}{ext}"'
        return response
    except Resume.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Resume not found',
        }, status=status.HTTP_404_NOT_FOUND)
    except drf_serializers.ValidationError as e:
        return Response({
            'success': False,
            'error': str(e.detail if hasattr(e, 'detail') else e),
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error("export_resume_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile_sections_list_create(request):
    """
    GET: Get profile sections for the authenticated user.
    POST: Create a profile section.
    """
    if request.method == 'POST':
        return _create_profile_section(request)
    try:
        sections = ProfileSection.objects.filter(user=request.user).order_by('order')
        return Response({
            'success': True,
            'data': ProfileSectionSerializer(sections, many=True).data,
        })
    except Exception as e:
        logger.error("get_profile_sections_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _create_profile_section(request):
    """
    Create a profile section.
    """
    try:
        serializer = ProfileSectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        section = ProfileSection.objects.create(
            user=request.user,
            section_type=serializer.validated_data['section_type'],
            title=serializer.validated_data.get('title', ''),
            content=serializer.validated_data.get('content', {}),
            order=serializer.validated_data.get('order', 0),
            is_visible=serializer.validated_data.get('is_visible', True),
        )
        
        return Response({
            'success': True,
            'data': ProfileSectionSerializer(section).data,
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error("create_profile_section_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def skill_verifications_list_create(request):
    """
    GET: Get skill verifications for the authenticated user.
    POST: Create a skill verification.
    """
    if request.method == 'POST':
        return _create_skill_verification(request)
    try:
        verifications = SkillVerification.objects.filter(user=request.user)
        return Response({
            'success': True,
            'data': SkillVerificationSerializer(verifications, many=True).data,
        })
    except Exception as e:
        logger.error("get_skill_verifications_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _create_skill_verification(request):
    """
    Create a skill verification.
    """
    try:
        serializer = SkillVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        verification = SkillVerification.objects.create(
            user=request.user,
            skill_name=serializer.validated_data['skill_name'],
            skill_category=serializer.validated_data.get('skill_category', ''),
            verification_method=serializer.validated_data.get('verification_method', 'cv'),
            evidence_url=serializer.validated_data.get('evidence_url', ''),
            evidence_text=serializer.validated_data.get('evidence_text', ''),
            score=serializer.validated_data.get('score', 50),
            level=serializer.validated_data.get('level', 'intermediate'),
        )
        
        return Response({
            'success': True,
            'data': SkillVerificationSerializer(verification).data,
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error("create_skill_verification_failed: %s", e)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeViewSet(APIView):
    """Viewset for Resume model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user resumes."""
        try:
            resumes = Resume.objects.filter(user=request.user)
            return Response({
                'success': True,
                'data': ResumeSerializer(resumes, many=True).data,
            })
        except Exception as e:
            logger.error("get_resumes_failed: %s", e)
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create resume."""
        try:
            serializer = ResumeCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            resume = Resume.objects.create(
                user=request.user,
                **serializer.validated_data
            )
            
            return Response({
                'success': True,
                'data': ResumeSerializer(resume).data,
            })
        except Exception as e:
            logger.error("create_resume_failed: %s", e)
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeTemplateViewSet(APIView):
    """Viewset for ResumeTemplate model."""
    
    def get(self, request):
        """Get resume templates."""
        try:
            templates = ResumeTemplate.objects.filter(is_active=True)
            return Response({
                'success': True,
                'data': ResumeTemplateSerializer(templates, many=True).data,
            })
        except Exception as e:
            logger.error("get_templates_failed: %s", e)
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)