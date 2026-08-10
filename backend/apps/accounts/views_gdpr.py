"""
GDPR Compliance API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.core.files.storage import default_storage

from .models_gdpr import DataExportRequest, AccountDeletionRequest
from .tasks_gdpr import generate_data_export, process_account_deletion


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_data_export(request):
    """
    GDPR Article 15 - Right to Access

    User requests export of all their personal data.
    Returns immediately with request ID; export processed asynchronously.

    POST /api/v1/auth/data-export/
    """
    user = request.user

    # Check for existing pending/processing requests
    existing = DataExportRequest.objects.filter(
        user=user,
        status__in=['pending', 'processing']
    ).first()

    if existing:
        return Response({
            'message': 'You already have a pending data export request.',
            'request_id': str(existing.id),
            'status': existing.status,
            'requested_at': existing.requested_at,
        }, status=status.HTTP_200_OK)

    # Create new request
    export_request = DataExportRequest.objects.create(
        user=user,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    # Trigger async task
    generate_data_export.delay(str(export_request.id))

    return Response({
        'message': 'Data export request created. You will receive a download link once processing is complete.',
        'request_id': str(export_request.id),
        'estimated_time': '5-10 minutes',
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_export_status(request, request_id):
    """
    Check status of data export request and get download URL if ready.

    GET /api/v1/auth/data-export/<request_id>/
    """
    try:
        export_request = DataExportRequest.objects.get(
            id=request_id,
            user=request.user
        )
    except DataExportRequest.DoesNotExist:
        return Response({
            'error': 'Export request not found'
        }, status=status.HTTP_404_NOT_FOUND)

    response_data = {
        'request_id': str(export_request.id),
        'status': export_request.status,
        'requested_at': export_request.requested_at,
    }

    if export_request.status == 'completed':
        # Generate download URL
        if export_request.file_path and default_storage.exists(export_request.file_path):
            download_url = default_storage.url(export_request.file_path)
            response_data['download_url'] = download_url
            response_data['file_size'] = export_request.file_size_bytes
            response_data['expires_at'] = export_request.expires_at
        else:
            response_data['error'] = 'Export file not found'

    elif export_request.status == 'failed':
        response_data['error'] = export_request.error_message

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_export_requests(request):
    """
    List all data export requests for current user.

    GET /api/v1/auth/data-exports/
    """
    exports = DataExportRequest.objects.filter(user=request.user)

    data = [
        {
            'request_id': str(exp.id),
            'status': exp.status,
            'requested_at': exp.requested_at,
            'completed_at': exp.completed_at,
            'expires_at': exp.expires_at,
            'file_size': exp.file_size_bytes if exp.status == 'completed' else None,
        }
        for exp in exports
    ]

    return Response({'exports': data})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def request_account_deletion(request):
    """
    GDPR Article 17 - Right to Erasure

    User requests account deletion. 30-day grace period before execution.
    User can cancel during grace period.

    DELETE /api/v1/auth/account/
    Body: { "reason": "optional reason" }
    """
    user = request.user

    # Check for existing deletion request
    existing = AccountDeletionRequest.objects.filter(
        user=user,
        status='pending'
    ).first()

    if existing:
        return Response({
            'message': 'You already have a pending account deletion request.',
            'request_id': str(existing.id),
            'scheduled_for': existing.scheduled_for,
            'can_cancel_until': existing.scheduled_for,
        }, status=status.HTTP_200_OK)

    # Create deletion request
    scheduled_for = timezone.now() + timedelta(days=30)

    deletion_request = AccountDeletionRequest.objects.create(
        user=user,
        reason=request.data.get('reason', ''),
        scheduled_for=scheduled_for,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return Response({
        'message': 'Account deletion scheduled. You have 30 days to cancel.',
        'request_id': str(deletion_request.id),
        'scheduled_for': scheduled_for,
        'grace_period_days': 30,
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_account_deletion(request):
    """
    Cancel a pending account deletion request.

    POST /api/v1/auth/account/cancel-deletion/
    """
    try:
        deletion_request = AccountDeletionRequest.objects.get(
            user=request.user,
            status='pending'
        )
    except AccountDeletionRequest.DoesNotExist:
        return Response({
            'error': 'No pending deletion request found'
        }, status=status.HTTP_404_NOT_FOUND)

    deletion_request.status = 'cancelled'
    deletion_request.save()

    return Response({
        'message': 'Account deletion cancelled successfully.'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deletion_status(request):
    """
    Check if user has pending deletion request.

    GET /api/v1/auth/account/deletion-status/
    """
    try:
        deletion_request = AccountDeletionRequest.objects.get(
            user=request.user,
            status='pending'
        )
        return Response({
            'pending': True,
            'scheduled_for': deletion_request.scheduled_for,
            'request_id': str(deletion_request.id),
            'days_remaining': (deletion_request.scheduled_for - timezone.now()).days,
        })
    except AccountDeletionRequest.DoesNotExist:
        return Response({'pending': False})
