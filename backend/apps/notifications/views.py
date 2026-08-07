"""
Notification Preferences Views

This module contains Django REST Framework views for notification management.
"""

import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    NotificationPreference,
    UserNotification,
    NotificationBatch,
)
from .serializers import (
    NotificationPreferenceSerializer,
    UserNotificationSerializer,
    NotificationBatchSerializer,
    NotificationUpdateSerializer,
    NotificationBulkUpdateSerializer,
    DigestSettingsSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def notification_preferences(request):
    """
    Get or update notification preferences for the authenticated user.
    """
    try:
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        if request.method == 'GET':
            return Response({
                'success': True,
                'data': NotificationPreferenceSerializer(preference).data,
            })
        
        elif request.method == 'PUT':
            serializer = NotificationPreferenceSerializer(
                preference, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'success': True,
                'data': NotificationPreferenceSerializer(preference).data,
            })
    except Exception as e:
        logger.error("notification_preferences_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_notifications(request):
    """
    Get or create notifications for the authenticated user.
    """
    try:
        if request.method == 'GET':
            notifications = UserNotification.objects.filter(
                user=request.user
            ).order_by('-sent_at')
            
            # Filter by status if provided
            status_param = request.query_params.get('status')
            if status_param:
                notifications = notifications.filter(status=status_param)
            
            # Filter by type if provided
            type_param = request.query_params.get('type')
            if type_param:
                notifications = notifications.filter(notification_type=type_param)
            
            return Response({
                'success': True,
                'data': UserNotificationSerializer(notifications, many=True).data,
            })
        
        elif request.method == 'POST':
            serializer = UserNotificationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            notification = UserNotification.objects.create(
                user=request.user,
                **serializer.validated_data
            )
            
            return Response({
                'success': True,
                'data': UserNotificationSerializer(notification).data,
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error("user_notifications_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_notification_detail(request, notification_id):
    """
    Get, update, or delete a specific notification.
    """
    try:
        notification = UserNotification.objects.get(
            id=notification_id,
            user=request.user
        )
        
        if request.method == 'GET':
            return Response({
                'success': True,
                'data': UserNotificationSerializer(notification).data,
            })
        
        elif request.method == 'PUT':
            serializer = NotificationUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            notification.status = serializer.validated_data['status']
            if notification.status == 'read' and notification.status != 'read':
                notification.read_at = timezone.now()
            notification.save()
            
            return Response({
                'success': True,
                'data': UserNotificationSerializer(notification).data,
            })
        
        elif request.method == 'DELETE':
            notification.delete()
            return Response({
                'success': True,
                'message': 'Notification deleted',
            })
    except UserNotification.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Notification not found',
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("user_notification_detail_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_notifications(request):
    """
    Bulk update notification status.
    """
    try:
        serializer = NotificationBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data['notification_ids']
        status_value = serializer.validated_data['status']
        
        updated = UserNotification.objects.filter(
            id__in=notification_ids,
            user=request.user
        ).update(
            status=status_value,
            read_at=timezone.now() if status_value == 'read' else None
        )
        
        return Response({
            'success': True,
            'message': f'Updated {updated} notifications',
        })
    except Exception as e:
        logger.error("bulk_update_notifications_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    """
    Mark all notifications as read.
    """
    try:
        updated = UserNotification.objects.filter(
            user=request.user,
            status='unread'
        ).update(
            status='read',
            read_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'Marked {updated} notifications as read',
        })
    except Exception as e:
        logger.error("mark_all_as_read_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_summary(request):
    """
    Get notification summary with counts.
    """
    try:
        summary = UserNotification.objects.filter(user=request.user).aggregate(
            total=models.Count('id'),
            unread=models.Count('id', filter=models.Q(status='unread')),
            read=models.Count('id', filter=models.Q(status='read')),
            archived=models.Count('id', filter=models.Q(status='archived')),
        )
        
        # Count by type
        by_type = UserNotification.objects.filter(user=request.user).values(
            'notification_type'
        ).annotate(count=models.Count('id'))
        
        return Response({
            'success': True,
            'data': {
                'total': summary['total'],
                'unread': summary['unread'],
                'read': summary['read'],
                'archived': summary['archived'],
                'by_type': {item['notification_type']: item['count'] for item in by_type},
            },
        })
    except Exception as e:
        logger.error("get_notification_summary_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_batches(request):
    """
    Get notification batches for the authenticated user.
    """
    try:
        batches = NotificationBatch.objects.all().order_by('-started_at')
        return Response({
            'success': True,
            'data': NotificationBatchSerializer(batches, many=True).data,
        })
    except Exception as e:
        logger.error("get_notification_batches_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_digest_settings(request):
    """
    Get digest settings (public endpoint for demo).
    """
    return Response({
        'success': True,
        'data': {
            'email_digest_enabled': True,
            'email_digest_time': '09:00',
            'alert_frequency': 'instant',
        },
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_digest_settings(request):
    """
    Update digest settings for the authenticated user.
    """
    try:
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        serializer = DigestSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        if 'email_digest_enabled' in serializer.validated_data:
            preference.email_digest_enabled = serializer.validated_data['email_digest_enabled']
        if 'email_digest_time' in serializer.validated_data:
            preference.email_digest_time = serializer.validated_data['email_digest_time']
        if 'alert_frequency' in serializer.validated_data:
            preference.alert_frequency = serializer.validated_data['alert_frequency']
        
        preference.save()
        
        return Response({
            'success': True,
            'data': NotificationPreferenceSerializer(preference).data,
        })
    except Exception as e:
        logger.error("update_digest_settings_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationPreferenceViewSet(APIView):
    """Viewset for NotificationPreference model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get notification preferences."""
        try:
            preference, created = NotificationPreference.objects.get_or_create(
                user=request.user
            )
            return Response({
                'success': True,
                'data': NotificationPreferenceSerializer(preference).data,
            })
        except Exception as e:
            logger.error("get_preferences_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """Update notification preferences."""
        try:
            preference, created = NotificationPreference.objects.get_or_create(
                user=request.user
            )
            serializer = NotificationPreferenceSerializer(
                preference, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'success': True,
                'data': NotificationPreferenceSerializer(preference).data,
            })
        except Exception as e:
            logger.error("update_preferences_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserNotificationViewSet(APIView):
    """Viewset for UserNotification model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user notifications."""
        try:
            notifications = UserNotification.objects.filter(
                user=request.user
            ).order_by('-sent_at')
            return Response({
                'success': True,
                'data': UserNotificationSerializer(notifications, many=True).data,
            })
        except Exception as e:
            logger.error("get_notifications_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)