"""CV Tailoring API"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.jobs.models import Job
from .cv_tailor_service import cv_tailor_service

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cv_tailor_suggestions(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    result = cv_tailor_service.analyze(request.user, job)
    return Response(result)
