# PHASE 2B: Rashid AI Core

> **Dependencies:** Phase 2A complete, AWS Bedrock, django-channels configured  
> **Duration:** 5-7 hours  
> **Status:** Ready for GLM execution

---

## 🎯 Objectives

Implement Rashid - the Egyptian Arabic AI career mentor:
- AWS Bedrock integration (Claude Sonnet)
- WebSocket real-time chat
- Egyptian Arabic dialect
- Conversation management with encryption
- Onboarding flow
- Context-aware responses

---

## 📦 Dependencies

```bash
# Backend
pip install channels channels-redis
pip install cryptography django-encrypted-model-fields

# Redis (required for channels)
# Ensure Redis is running on localhost:6379
```

---

## 🔧 Backend Implementation

### Step 1: Django Channels Configuration

**File:** `backend/ecareer/asgi.py`

```python
"""
ASGI config for WebSocket support
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecareer.settings')

django_asgi_app = get_asgi_application()

import rashid.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                rashid.routing.websocket_urlpatterns
            )
        )
    ),
})
```

**Update:** `backend/ecareer/settings.py`

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'channels',
    'rashid',
]

# Channels configuration
ASGI_APPLICATION = 'ecareer.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(os.getenv('REDIS_HOST', 'localhost'), 6379)],
        },
    },
}

# Rashid Configuration
RASHID_CONFIG = {
    'dialect': 'egyptian_arabic',
    'personality': 'supportive_mentor',
    'max_conversation_history': 50,
    'course_platform_url': 'https://edu.usamif.com',
    'privacy_mode': True,  # Admin cannot read conversation content
}
```

### Step 2: Rashid Models

**File:** `backend/rashid/models.py`

```python
from django.db import models
from django.contrib.auth import get_user_model
from encrypted_model_fields.fields import EncryptedTextField
import uuid

User = get_user_model()

class RashidConfig(models.Model):
    """Global Rashid configuration (admin-editable)"""
    
    PERSONALITY_CHOICES = [
        ('supportive_mentor', 'Supportive Mentor'),
        ('professional', 'Professional Advisor'),
        ('friendly', 'Friendly Coach'),
    ]
    
    DIALECT_CHOICES = [
        ('egyptian_arabic', 'Egyptian Arabic'),
        ('formal_arabic', 'Formal Arabic'),
        ('english', 'English'),
    ]
    
    personality = models.CharField(
        max_length=50,
        choices=PERSONALITY_CHOICES,
        default='supportive_mentor'
    )
    dialect = models.CharField(
        max_length=50,
        choices=DIALECT_CHOICES,
        default='egyptian_arabic'
    )
    system_prompt_template = models.TextField(
        help_text="System prompt template with {variables}"
    )
    greeting_message = models.TextField(
        default="أهلاً! أنا رشيد، مستشارك المهني. إزاي أقدر أساعدك النهاردة؟"
    )
    max_tokens_per_response = models.IntegerField(default=1000)
    temperature = models.FloatField(default=0.7)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rashid Configuration"
        verbose_name_plural = "Rashid Configurations"
    
    def __str__(self):
        return f"Rashid Config ({self.dialect})"
    
    @classmethod
    def get_active_config(cls):
        """Get the active Rashid configuration"""
        return cls.objects.filter(is_active=True).first()


class Conversation(models.Model):
    """User conversation with Rashid"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rashid_conversations')
    title = models.CharField(max_length=255, blank=True)
    mode = models.CharField(
        max_length=50,
        default='general',
        choices=[
            ('general', 'General Chat'),
            ('cv_review', 'CV Review'),
            ('cover_letter', 'Cover Letter'),
            ('interview_prep', 'Interview Prep'),
            ('career_advice', 'Career Advice'),
            ('linkedin', 'LinkedIn Optimization'),
            ('course_advice', 'Course Recommendations'),
        ]
    )
    context_data = models.JSONField(
        default=dict,
        help_text="Additional context (e.g., job_id, cv_data)"
    )
    is_active = models.BooleanField(default=True)
    message_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title or self.mode}"


class Message(models.Model):
    """Individual message in a conversation (ENCRYPTED)"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Rashid'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # ENCRYPTED - Admin cannot read this
    content = EncryptedTextField()
    
    # Metadata (NOT encrypted)
    token_count = models.IntegerField(default=0)
    latency_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.role} message at {self.created_at}"


class UserOnboarding(models.Model):
    """Track user onboarding progress with Rashid"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rashid_onboarding')
    has_completed_intro = models.BooleanField(default=False)
    has_uploaded_cv = models.BooleanField(default=False)
    has_asked_question = models.BooleanField(default=False)
    has_used_tool = models.BooleanField(default=False)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - Onboarding"
    
    @property
    def is_complete(self):
        return all([
            self.has_completed_intro,
            self.has_uploaded_cv,
            self.has_asked_question,
        ])
```

### Step 3: Rashid Service (Core AI Logic)

**File:** `backend/rashid/service.py`

```python
"""
Rashid AI service - handles conversation logic and AI integration
"""

import logging
from django.conf import settings
from ai.bedrock_service import bedrock_service
from .models import Conversation, Message, RashidConfig

logger = logging.getLogger(__name__)

class RashidService:
    """Core Rashid AI service"""
    
    def __init__(self):
        self.config = RashidConfig.get_active_config()
        if not self.config:
            # Create default config
            self.config = self._create_default_config()
    
    def _create_default_config(self):
        """Create default Rashid configuration"""
        system_prompt = """أنت رشيد، مستشار مهني مصري متخصص في مساعدة الباحثين عن عمل.

شخصيتك:
- متفهم وداعم ومشجع
- تتكلم بالعامية المصرية بشكل طبيعي
- خبير في سوق العمل المصري والعربي
- صبور وتشرح الأمور بوضوح

مسؤولياتك:
1. مساعدة الباحثين عن عمل في تحسين سيرتهم الذاتية
2. كتابة خطابات التوظيف (cover letters)
3. التحضير للمقابلات الوظيفية
4. تقديم نصائح مهنية
5. ترشيح دورات تدريبية من {course_platform_url}
6. تحليل عروض العمل

قواعد مهمة:
- لا تخترع معلومات - اعتمد على البيانات المتاحة فقط
- الدورات من {course_platform_url} فقط
- احترم خصوصية المستخدم
- كن إيجابياً ومشجعاً
- استخدم أمثلة واقعية من السوق المصري

الإجابات:
- واضحة ومختصرة (200-300 كلمة)
- منظمة بنقاط أو فقرات
- عملية وقابلة للتطبيق
- بالعامية المصرية الطبيعية
"""
        
        config = RashidConfig.objects.create(
            personality='supportive_mentor',
            dialect='egyptian_arabic',
            system_prompt_template=system_prompt,
            greeting_message="أهلاً! أنا رشيد، مستشارك المهني. إزاي أقدر أساعدك النهاردة؟",
            max_tokens_per_response=1000,
            temperature=0.7,
            is_active=True
        )
        
        return config
    
    def get_system_prompt(self, conversation):
        """Build system prompt with context"""
        template = self.config.system_prompt_template
        
        # Add user context
        user_context = self._build_user_context(conversation.user)
        
        # Add conversation context
        if conversation.context_data:
            context_str = self._format_context_data(conversation.context_data)
        else:
            context_str = "لا يوجد سياق إضافي."
        
        system_prompt = template.format(
            course_platform_url=settings.RASHID_CONFIG['course_platform_url']
        )
        
        system_prompt += f"\n\n**معلومات المستخدم:**\n{user_context}\n"
        system_prompt += f"\n**سياق المحادثة:**\n{context_str}\n"
        
        return system_prompt
    
    def _build_user_context(self, user):
        """Build user context summary"""
        try:
            profile = user.userprofile
            
            context_parts = []
            
            if profile.current_position:
                context_parts.append(f"- الوظيفة الحالية: {profile.current_position}")
            
            if profile.years_of_experience:
                context_parts.append(f"- سنوات الخبرة: {profile.years_of_experience}")
            
            if profile.skills:
                skills_str = ', '.join(profile.skills[:5])
                context_parts.append(f"- المهارات الأساسية: {skills_str}")
            
            if profile.preferred_job_titles:
                titles_str = ', '.join(profile.preferred_job_titles)
                context_parts.append(f"- الوظائف المهتم بها: {titles_str}")
            
            if profile.education.exists():
                last_edu = profile.education.first()
                context_parts.append(f"- التعليم: {last_edu.degree}")
            
            if context_parts:
                return '\n'.join(context_parts)
            else:
                return "لا يوجد معلومات مفصلة عن المستخدم بعد."
        
        except:
            return "لا يوجد معلومات مفصلة عن المستخدم بعد."
    
    def _format_context_data(self, context_data):
        """Format conversation context data"""
        formatted = []
        
        if context_data.get('mode') == 'cv_review':
            formatted.append("**الوضع:** مراجعة السيرة الذاتية")
        
        elif context_data.get('mode') == 'cover_letter':
            if context_data.get('job_title'):
                formatted.append(f"**كتابة cover letter لوظيفة:** {context_data['job_title']}")
        
        elif context_data.get('mode') == 'interview_prep':
            if context_data.get('company'):
                formatted.append(f"**التحضير لمقابلة مع:** {context_data['company']}")
        
        elif context_data.get('job_id'):
            # Job-specific conversation
            formatted.append(f"**المحادثة عن وظيفة محددة** (ID: {context_data['job_id']})")
        
        if not formatted:
            return "محادثة عامة"
        
        return '\n'.join(formatted)
    
    def get_conversation_history(self, conversation, limit=10):
        """Get recent conversation history"""
        messages = conversation.messages.all().order_by('-created_at')[:limit]
        messages = list(reversed(messages))
        
        history = []
        for msg in messages:
            history.append({
                'role': msg.role,
                'content': msg.content  # Decrypted automatically
            })
        
        return history
    
    async def generate_response(self, conversation, user_message):
        """
        Generate Rashid's response to user message
        
        Args:
            conversation: Conversation instance
            user_message: User's message text
        
        Returns:
            str: Rashid's response
        """
        import time
        start_time = time.time()
        
        # Save user message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
            token_count=len(user_message.split())
        )
        
        # Build prompt
        system_prompt = self.get_system_prompt(conversation)
        conversation_history = self.get_conversation_history(conversation)
        
        # Build messages for Bedrock
        messages = []
        for hist_msg in conversation_history:
            messages.append({
                'role': hist_msg['role'],
                'content': hist_msg['content']
            })
        
        # Current user message
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        # Call Bedrock
        try:
            response = bedrock_service.invoke_model(
                prompt=user_message,
                system_prompt=system_prompt,
                max_tokens=self.config.max_tokens_per_response,
                temperature=self.config.temperature
            )
        except Exception as e:
            logger.error(f"Bedrock error: {e}")
            response = "عذراً، حصل خطأ تقني. جرب تاني بعد شوية."
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Save assistant message
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response,
            token_count=len(response.split()),
            latency_ms=latency_ms
        )
        
        # Update conversation
        conversation.message_count += 2
        conversation.save()
        
        return response


# Singleton instance
rashid_service = RashidService()
```

### Step 4: WebSocket Consumer

**File:** `backend/rashid/consumers.py`

```python
"""
WebSocket consumer for real-time Rashid chat
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .service import rashid_service

logger = logging.getLogger(__name__)
User = get_user_model()

class RashidConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for Rashid chat"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get or create conversation
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        
        if self.conversation_id:
            self.conversation = await self.get_conversation(self.conversation_id)
            if not self.conversation or self.conversation.user != self.user:
                await self.close()
                return
        else:
            self.conversation = await self.create_conversation()
        
        await self.accept()
        
        # Send greeting if new conversation
        if self.conversation.message_count == 0:
            await self.send_greeting()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        pass
    
    async def receive(self, text_data):
        """Handle incoming message"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                # Handle typing indicator (future feature)
                pass
        
        except json.JSONDecodeError:
            await self.send_error("Invalid message format")
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {e}")
            await self.send_error("An error occurred")
    
    async def handle_message(self, data):
        """Handle user message"""
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return
        
        # Send acknowledgment
        await self.send(text_data=json.dumps({
            'type': 'message_received',
            'status': 'processing'
        }))
        
        # Generate response
        try:
            response = await database_sync_to_async(
                rashid_service.generate_response
            )(self.conversation, user_message)
            
            # Send response
            await self.send(text_data=json.dumps({
                'type': 'message',
                'role': 'assistant',
                'content': response,
                'timestamp': str(timezone.now())
            }))
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await self.send_error("Failed to generate response")
    
    async def send_greeting(self):
        """Send greeting message"""
        config = await database_sync_to_async(
            lambda: rashid_service.config
        )()
        
        greeting = config.greeting_message
        
        # Save greeting message
        await database_sync_to_async(Message.objects.create)(
            conversation=self.conversation,
            role='assistant',
            content=greeting
        )
        
        # Send to client
        await self.send(text_data=json.dumps({
            'type': 'message',
            'role': 'assistant',
            'content': greeting,
            'timestamp': str(timezone.now())
        }))
    
    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    @database_sync_to_async
    def get_conversation(self, conversation_id):
        """Get conversation by ID"""
        try:
            return Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_conversation(self):
        """Create new conversation"""
        return Conversation.objects.create(
            user=self.user,
            title="New Conversation",
            mode='general'
        )
```

### Step 5: WebSocket Routing

**File:** `backend/rashid/routing.py`

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/rashid/$', consumers.RashidConsumer.as_asgi()),
    re_path(r'ws/rashid/(?P<conversation_id>[0-9a-f-]+)/$', consumers.RashidConsumer.as_asgi()),
]
```

### Step 6: REST API Views

**File:** `backend/rashid/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Conversation, Message, UserOnboarding
from .serializers import ConversationSerializer, MessageSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    """
    Conversation management
    
    GET /api/rashid/conversations/ - List user conversations
    POST /api/rashid/conversations/ - Create new conversation
    GET /api/rashid/conversations/{id}/ - Get conversation with messages
    DELETE /api/rashid/conversations/{id}/ - Delete conversation
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        ).prefetch_related('messages')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get conversation messages"""
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def onboarding_status(self, request):
        """Get user onboarding status"""
        onboarding, created = UserOnboarding.objects.get_or_create(
            user=request.user
        )
        
        return Response({
            'is_complete': onboarding.is_complete,
            'has_completed_intro': onboarding.has_completed_intro,
            'has_uploaded_cv': onboarding.has_uploaded_cv,
            'has_asked_question': onboarding.has_asked_question,
            'has_used_tool': onboarding.has_used_tool
        })
```

### Step 7: Serializers

**File:** `backend/rashid/serializers.py`

```python
from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'mode', 'context_data', 'is_active',
            'message_count', 'created_at', 'updated_at',
            'messages', 'message_preview'
        ]
        read_only_fields = ['id', 'message_count', 'created_at', 'updated_at']
    
    def get_message_preview(self, obj):
        """Get last message preview"""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'role': last_message.role,
                'content': last_message.content[:100],
                'timestamp': last_message.created_at
            }
        return None
```

### Step 8: URLs

**File:** `backend/rashid/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Update:** `backend/ecareer/urls.py`

```python
urlpatterns = [
    # ... existing
    path('api/rashid/', include('rashid.urls')),
]
```

---

## 🎨 Frontend Implementation

### Step 9: Rashid Chat Component

**File:** `frontend/src/pages/RashidChatPage.jsx`

```jsx
import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Send, Loader } from 'lucide-react';
import useWebSocket from 'react-use-websocket';

const RashidChatPage = () => {
  const { conversationId } = useParams();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);
  
  const WS_URL = conversationId
    ? `ws://localhost:8000/ws/rashid/${conversationId}/`
    : `ws://localhost:8000/ws/rashid/`;
  
  const { sendMessage, lastMessage, readyState } = useWebSocket(WS_URL, {
    onOpen: () => setIsConnected(true),
    onClose: () => setIsConnected(false),
    shouldReconnect: () => true,
  });

  useEffect(() => {
    if (lastMessage !== null) {
      const data = JSON.parse(lastMessage.data);
      
      if (data.type === 'message') {
        setMessages(prev => [...prev, {
          role: data.role,
          content: data.content,
          timestamp: data.timestamp
        }]);
      }
    }
  }, [lastMessage]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!inputMessage.trim()) return;
    
    // Add user message to UI
    setMessages(prev => [...prev, {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }]);
    
    // Send to WebSocket
    sendMessage(JSON.stringify({
      type: 'message',
      message: inputMessage
    }));
    
    setInputMessage('');
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">رشيد - مستشارك المهني</h1>
          <p className="text-sm text-gray-600">
            {isConnected ? (
              <span className="text-green-600">● متصل</span>
            ) : (
              <span className="text-red-600">● غير متصل</span>
            )}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl px-6 py-3 rounded-2xl ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-900 border'
              }`}
              dir="rtl"
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t px-6 py-4">
        <div className="max-w-4xl mx-auto flex gap-4">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="اكتب رسالتك..."
            className="flex-1 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
            dir="rtl"
          />
          <button
            onClick={handleSend}
            disabled={!isConnected || !inputMessage.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default RashidChatPage;
```

---

## ✅ Phase 2B Verification

### Backend Tests

```bash
# Run Channels development server
python manage.py runserver

# In another terminal, start Celery worker
celery -A ecareer worker -l info

# Test WebSocket connection
# Use browser console or wscat:
wscat -c "ws://localhost:8000/ws/rashid/"
```

### Success Criteria

- [ ] WebSocket connects successfully
- [ ] Greeting message appears
- [ ] User can send messages
- [ ] Rashid responds in Egyptian Arabic
- [ ] Messages are encrypted in database
- [ ] Conversation history persists
- [ ] Multiple conversations supported

---

**Phase 2B Complete! ✅**
Proceed to Phase 2C: Rashid Tools
