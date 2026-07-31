"""
WebSocket consumer for real-time Rashid chat
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import RashidConversation, RashidMessage
from .service import rashid_service, estimate_tokens
from .tools import execute_tool

logger = logging.getLogger(__name__)
User = get_user_model()


class RashidConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for Rashid chat"""

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            logger.warning("Unauthenticated WebSocket connection attempt")
            await self.close()
            return

        # Get or create conversation
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        self.conversation = None

        if self.conversation_id:
            self.conversation = await self.get_conversation(self.conversation_id)
            if not self.conversation or self.conversation.user != self.user:
                await self.close()
                return
        else:
            self.conversation = await self.create_conversation()

        await self.accept()
        
        # Send greeting if new conversation
        message_count = await self.get_message_count()
        if message_count == 0:
            await self.send_greeting()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.info(f"WebSocket disconnected: {close_code}")

    async def receive(self, text_data):
        """Handle incoming message"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')

            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'tool':
                await self.handle_tool(data)
            elif message_type == 'typing':
                # Handle typing indicator (broadcast to other users if needed)
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

    async def handle_tool(self, data):
        """Handle tool execution request"""
        tool_name = data.get('tool')
        context = data.get('context', {})

        if not tool_name:
            await self.send_error("Tool name required")
            return

        # Send processing indicator
        await self.send(text_data=json.dumps({
            'type': 'tool_processing',
            'tool': tool_name
        }))

        # Execute tool
        try:
            context['user'] = self.user
            result = await database_sync_to_async(execute_tool)(tool_name, context)

            # Send result
            await self.send(text_data=json.dumps({
                'type': 'tool_result',
                'tool': tool_name,
                'result': result,
                'timestamp': str(timezone.now())
            }))

            # Save as message
            await database_sync_to_async(RashidMessage.objects.create)(
                conversation=self.conversation,
                role='assistant',
                content=f"[Tool: {tool_name}]\n\n{result}"
            )

        except Exception as e:
            logger.error(f"Error executing tool: {e}")
            await self.send_error(f"Failed to execute tool: {str(e)}")

    async def send_greeting(self):
        """Send greeting message"""
        greeting = await database_sync_to_async(
            rashid_service.get_greeting
        )(self.user)

        # Save greeting message
        await database_sync_to_async(RashidMessage.objects.create)(
            conversation=self.conversation,
            role='assistant',
            content=greeting,
            tokens_used=estimate_tokens(greeting)
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
            return RashidConversation.objects.get(id=conversation_id)
        except RashidConversation.DoesNotExist:
            return None

    @database_sync_to_async
    def create_conversation(self):
        """Create new conversation"""
        return RashidConversation.objects.create(
            user=self.user,
            mode='general'
        )

    @database_sync_to_async
    def get_message_count(self):
        """Get message count for conversation"""
        return self.conversation.messages.count()