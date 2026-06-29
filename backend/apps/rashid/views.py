"""
API Views for Rashid AI Assistant
"""

import logging
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404

from apps.jobs.models import Job
from .models import (
    RashidConfig,
    RashidProfile,
    RashidConversation,
    RashidMessage,
    RashidStoryBank,
    RashidUsage
)
from .serializers import (
    RashidConversationSerializer,
    RashidConversationListSerializer,
    RashidMessageSerializer,
    RashidProfileSerializer,
    RashidProfileUpdateSerializer,
    RashidStoryBankSerializer,
    StartConversationSerializer,
    SendMessageSerializer,
    RashidConfigSerializer
)
from .service import rashid_service
from .tools import execute_tool, get_available_tools

logger = logging.getLogger(__name__)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Rashid conversations

    list: Get all user conversations
    retrieve: Get single conversation with messages
    create: Start a new conversation
    destroy: Delete a conversation
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RashidConversation.objects.filter(
            user=self.request.user
        ).prefetch_related('messages').order_by('-updated_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return RashidConversationListSerializer
        return RashidConversationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Start a new conversation"""
        serializer = StartConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mode = serializer.validated_data.get('mode', 'general')
        job_id = serializer.validated_data.get('job_id')

        job = None
        if job_id:
            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                pass

        conversation = rashid_service.start_conversation(
            user=request.user,
            mode=mode,
            job=job
        )

        # Get greeting message
        greeting = rashid_service.get_greeting(request.user)

        # Save greeting as first message
        RashidMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=greeting,
            tokens_used=len(greeting.split())
        )

        return Response({
            'id': conversation.id,
            'mode': conversation.mode,
            'title': conversation.title,
            'greeting': greeting,
            'websocket_url': f'/ws/rashid/{conversation.id}/'
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get conversation messages"""
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('created_at')
        serializer = RashidMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message via REST API (alternative to WebSocket)"""
        conversation = self.get_object()
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data['message']

        # Generate response
        response = rashid_service.generate_response(conversation, message)

        return Response({
            'user_message': message,
            'assistant_response': response,
            'timestamp': str(timezone.now())
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active conversations"""
        conversations = self.get_queryset().filter(is_active=True)
        serializer = RashidConversationListSerializer(conversations, many=True)
        return Response(serializer.data)


class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Rashid user profile
    """

    permission_classes = [IsAuthenticated]
    serializer_class = RashidProfileSerializer

    def get_queryset(self):
        return RashidProfile.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create profile for user"""
        profile, created = RashidProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'experience_level': '',
                'current_role': '',
                'target_role': '',
                'skills': [],
                'onboarding_complete': False,
                'onboarding_step': 0
            }
        )
        return profile

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = RashidProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return full profile
        return Response(RashidProfileSerializer(profile).data)

    @action(detail=False, methods=['post'])
    def complete_onboarding(self, request):
        """Mark onboarding as complete"""
        profile = self.get_object()
        profile.onboarding_complete = True
        profile.save()
        return Response({
            'status': 'success',
            'onboarding_complete': True
        })


class StoryBankViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing STAR stories
    """

    permission_classes = [IsAuthenticated]
    serializer_class = RashidStoryBankSerializer

    def get_queryset(self):
        return RashidStoryBank.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_usage_stats(request):
    """Get user's token usage statistics"""
    today = timezone.now().date()
    usage = RashidUsage.objects.filter(user=request.user).order_by('-date')[:30]

    return Response({
        'daily_usage': [
            {
                'date': str(u.date),
                'tokens_used': u.tokens_used
            }
            for u in usage
        ],
        'limit': rashid_service.config.daily_token_limit,
        'remaining_today': max(0, rashid_service.config.daily_token_limit - (
            usage.filter(date=today).first().tokens_used if usage.filter(date=today).exists() else 0
        ))
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_config(request):
    """Get Rashid configuration (public info only)"""
    config = rashid_service.config
    return Response({
        'modes': dict(RashidConversation.MODES),
        'max_tokens_per_response': config.max_tokens,
        'daily_token_limit': config.daily_token_limit,
        'course_platform_url': getattr(settings, 'RASHID_CONFIG', {}).get('course_platform_url', '')
    })


# Import settings for the config view
from django.conf import settings


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_tool_endpoint(request):
    """
    Execute a Rashid tool
    
    POST /api/rashid/tools/execute/
    {
        "tool": "cv_review",
        "context": {...}
    }
    """
    tool_name = request.data.get('tool')
    context = request.data.get('context', {})
    
    if not tool_name:
        return Response({'error': 'Tool name required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Add user to context
    context['user'] = request.user
    
    # Execute tool
    result = execute_tool(tool_name, context)
    
    return Response({
        'tool': tool_name,
        'result': result
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tools(request):
    """List available Rashid tools"""
    tools = get_available_tools()
    return Response({'tools': tools})
