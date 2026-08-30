"""
API Views for Rashid AI Assistant
"""

import logging
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings

from apps.jobs.models import Job
from apps.core.utils import success_response, error_response
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
from .service import rashid_service, estimate_tokens
from .tools import execute_tool, get_available_tools
from apps.events.emitter import emit
from apps.events.types import AI_CONVERSATION_STARTED, AI_MESSAGE_SENT

logger = logging.getLogger(__name__)


class MessageRateThrottle(UserRateThrottle):
    rate = "20/minute"
    scope = "rashid_message"


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Rashid conversations

    list: Get all user conversations
    retrieve: Get single conversation with messages
    create: Start a new conversation
    destroy: Delete a conversation
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [MessageRateThrottle]

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

        # Emit AI_CONVERSATION_STARTED event
        try:
            emit(
                event_type=AI_CONVERSATION_STARTED,
                category="ai",
                user=request.user,
                target_type="conversation",
                target_id=str(conversation.id),
                data={"mode": mode, "job_id": job_id},
                request=request,
            )
        except Exception:
            pass

        # Get greeting message
        greeting = rashid_service.get_greeting(request.user)

        # Save greeting as first message
        RashidMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=greeting,
            tokens_used=estimate_tokens(greeting)
        )

        data = {
            'id': conversation.id,
            'mode': conversation.mode,
            'title': conversation.title,
            'greeting': greeting,
            'websocket_url': f'/ws/rashid/{conversation.id}/'
        }
        return Response(
            success_response(data=data),
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single conversation with messages"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(success_response(data=serializer.data))

    def destroy(self, request, *args, **kwargs):
        """Delete a conversation"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            success_response(message="Conversation deleted."),
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        """Get or create conversation messages"""
        conversation = self.get_object()

        if request.method == 'GET':
            messages = conversation.messages.all().order_by('created_at')
            serializer = RashidMessageSerializer(messages, many=True)
            return Response(success_response(data=serializer.data))

        # POST: create a new message
        role = request.data.get('role', 'user')
        content = request.data.get('content', '')

        msg = RashidMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            tokens_used=estimate_tokens(content),
        )

        serializer = RashidMessageSerializer(msg)
        return Response(
            success_response(data=serializer.data),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message via REST API (alternative to WebSocket)"""
        conversation = self.get_object()
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data['message']

        # Emit AI_MESSAGE_SENT event
        try:
            emit(
                event_type=AI_MESSAGE_SENT,
                category="ai",
                user=request.user,
                target_type="conversation",
                target_id=str(conversation.id),
                data={"message": message},
                request=request,
            )
        except Exception:
            pass

        # Generate response
        response = rashid_service.generate_response(conversation, message)

        return Response(success_response(data={
            'user_message': message,
            'assistant_response': response,
            'timestamp': str(timezone.now())
        }))

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active conversations"""
        conversations = self.get_queryset().filter(is_active=True)
        serializer = RashidConversationListSerializer(conversations, many=True)
        return Response(success_response(data=serializer.data))


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
        return Response(success_response(data=serializer.data))

    def create(self, request, *args, **kwargs):
        """Create or update the user profile."""
        profile, created = RashidProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'experience_level': '',
                'current_role': '',
                'target_role': '',
                'skills': [],
                'onboarding_complete': False,
                'onboarding_step': 0,
            }
        )
        serializer = RashidProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        out = RashidProfileSerializer(profile).data
        resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            success_response(data=out),
            status=resp_status,
        )

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = RashidProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            success_response(data=RashidProfileSerializer(profile).data)
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def complete_onboarding(self, request):
        """Mark onboarding as complete"""
        profile = self.get_object()
        profile.onboarding_complete = True
        profile.save()
        return Response(success_response(data={
            'status': 'success',
            'onboarding_complete': True
        }))


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            success_response(data=serializer.data),
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(success_response(data=serializer.data))

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(success_response(data=serializer.data))

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            success_response(message="Story deleted."),
            status=status.HTTP_200_OK,
        )


@api_view(['GET', 'PATCH'])
@permission_classes([AllowAny])
def get_config(request):
    """Get or update Rashid configuration."""
    config = RashidConfig.objects.first()
    if config is None:
        config = RashidConfig.objects.create()

    if request.method == 'GET':
        serializer = RashidConfigSerializer(config)
        return Response(success_response(data=serializer.data))

    # PATCH requires authenticated admin
    if not (request.user and request.user.is_authenticated and request.user.is_staff):
        return Response(
            error_response("Admin access required."),
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = RashidConfigSerializer(config, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(success_response(data=serializer.data))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_usage_stats(request):
    """Get user's token usage statistics"""
    today = timezone.now().date()
    base_qs = RashidUsage.objects.filter(user=request.user)
    usage = base_qs.order_by('-date')[:30]

    # Calculate today's usage from the unsliced queryset
    today_usage_obj = base_qs.filter(date=today).first()
    today_tokens = today_usage_obj.tokens_used if today_usage_obj else 0

    data = {
        'daily_usage': [
            {
                'date': str(u.date),
                'tokens_used': u.tokens_used
            }
            for u in usage
        ],
        'limit': rashid_service.config.daily_token_limit,
        'remaining_today': max(0, rashid_service.config.daily_token_limit - today_tokens)
    }
    return Response(success_response(data=data))


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
        return Response(
            error_response("Tool name required."),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Add user to context
    context['user'] = request.user

    # Execute tool
    result = execute_tool(tool_name, context)

    return Response(success_response(data={
        'tool': tool_name,
        'result': result
    }))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_job(request, job_slug):
    """
    Analyze a job posting with Rashid AI.
    """
    job = get_object_or_404(Job, slug=job_slug)
    question = request.data.get('question', '')

    context = {
        'user': request.user,
        'job': job,
        'question': question,
    }

    try:
        result = execute_tool('job_analysis', context)
    except Exception:
        result = None

    if result:
        data = {'analysis': result}
    else:
        data = {'message': 'Analysis for {} is being processed.'.format(job.title)}

    return Response(success_response(data=data))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tools(request):
    """List available Rashid tools"""
    tools = get_available_tools()
    return Response(success_response(data={'tools': tools}))
