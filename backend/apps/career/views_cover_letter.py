"""
Cover Letter API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.jobs.models import Job
from .models import CoverLetter
from .cover_letter_service import cover_letter_service


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_cover_letter(request, job_id):
    """
    Generate a cover letter for a specific job.

    POST /api/v1/career/cover-letter/<job_id>/

    Body (optional):
    {
        "tone": "professional" | "enthusiastic" | "formal",
        "regenerate": false  // Set to true to create new version
    }
    """
    job = get_object_or_404(Job, uuid=job_id, status='active')

    tone = request.data.get('tone', 'professional')
    regenerate = request.data.get('regenerate', False)

    # Check if user already has a cover letter for this job
    existing = CoverLetter.objects.filter(user=request.user, job=job).first()

    if existing and not regenerate:
        # Return existing
        return Response({
            'id': str(existing.id),
            'content': existing.content,
            'tone': existing.tone,
            'confidence': existing.confidence,
            'word_count': existing.word_count,
            'version': existing.version,
            'is_edited': existing.is_edited,
            'created_at': existing.created_at,
            'message': 'Existing cover letter returned. Set "regenerate": true to create a new version.'
        })

    # Generate new cover letter
    result = cover_letter_service.generate_cover_letter(
        user=request.user,
        job=job,
        tone=tone
    )

    # Determine version number
    version = (existing.version + 1) if existing else 1

    # Save to database
    cover_letter = CoverLetter.objects.create(
        user=request.user,
        job=job,
        content=result['content'],
        tone=tone,
        confidence=result.get('confidence', 0.0),
        word_count=result.get('word_count', 0),
        version=version
    )

    return Response({
        'id': str(cover_letter.id),
        'content': cover_letter.content,
        'tone': cover_letter.tone,
        'confidence': cover_letter.confidence,
        'word_count': cover_letter.word_count,
        'version': cover_letter.version,
        'created_at': cover_letter.created_at,
        'message': 'Cover letter generated successfully.'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def cover_letter_detail(request, cover_letter_id):
    """
    Retrieve, update, or delete a cover letter.

    GET /api/v1/career/cover-letter/<id>/
    PATCH /api/v1/career/cover-letter/<id>/  (update content, mark as edited)
    DELETE /api/v1/career/cover-letter/<id>/
    """
    cover_letter = get_object_or_404(
        CoverLetter,
        id=cover_letter_id,
        user=request.user
    )

    if request.method == 'GET':
        return Response({
            'id': str(cover_letter.id),
            'job_id': str(cover_letter.job.id),
            'job_title': cover_letter.job.title,
            'company': cover_letter.job.company.name,
            'content': cover_letter.content,
            'tone': cover_letter.tone,
            'confidence': cover_letter.confidence,
            'word_count': cover_letter.word_count,
            'version': cover_letter.version,
            'is_edited': cover_letter.is_edited,
            'created_at': cover_letter.created_at,
            'updated_at': cover_letter.updated_at,
        })

    elif request.method == 'PATCH':
        # Update content (user editing)
        if 'content' in request.data:
            cover_letter.content = request.data['content']
            cover_letter.word_count = len(request.data['content'].split())
            cover_letter.is_edited = True
            cover_letter.save()

        return Response({
            'id': str(cover_letter.id),
            'content': cover_letter.content,
            'word_count': cover_letter.word_count,
            'is_edited': cover_letter.is_edited,
            'message': 'Cover letter updated.'
        })

    elif request.method == 'DELETE':
        cover_letter.delete()
        return Response({
            'message': 'Cover letter deleted.'
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_cover_letters(request):
    """
    List all cover letters for the authenticated user.

    GET /api/v1/career/cover-letters/
    """
    cover_letters = CoverLetter.objects.filter(user=request.user).select_related('job', 'job__company')

    data = [
        {
            'id': str(cl.id),
            'job_id': str(cl.job.id),
            'job_title': cl.job.title,
            'company': cl.job.company.name,
            'tone': cl.tone,
            'word_count': cl.word_count,
            'version': cl.version,
            'is_edited': cl.is_edited,
            'created_at': cl.created_at,
        }
        for cl in cover_letters
    ]

    return Response({
        'cover_letters': data,
        'total': len(data)
    })
