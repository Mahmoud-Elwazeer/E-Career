"""
Onboarding Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import OnboardingProgress
from .serializers_onboarding import OnboardingProgressSerializer, OnboardingStepSerializer


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def onboarding_progress(request):
    """
    GET: Retrieve user's onboarding progress
    PATCH: Update onboarding progress (mark step complete)

    Endpoint: /api/v1/career/onboarding/
    """
    # Get or create onboarding progress
    progress, created = OnboardingProgress.objects.get_or_create(
        user=request.user
    )

    if request.method == 'GET':
        serializer = OnboardingProgressSerializer(progress)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        step_serializer = OnboardingStepSerializer(data=request.data)
        step_serializer.is_valid(raise_exception=True)

        step_id = step_serializer.validated_data['step_id']

        # Update onboarding data if provided
        if 'career_stage' in step_serializer.validated_data:
            progress.career_stage = step_serializer.validated_data['career_stage']
        if 'primary_interest' in step_serializer.validated_data:
            progress.primary_interest = step_serializer.validated_data['primary_interest']

        # Mark step complete
        progress.mark_step_complete(step_id)

        # Return updated progress
        serializer = OnboardingProgressSerializer(progress)
        return Response(serializer.data)
