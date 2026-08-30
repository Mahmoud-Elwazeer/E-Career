"""
Rashid AI service - handles conversation logic and AI integration
"""

import logging
import time
from django.conf import settings
from django.utils import timezone
from apps.intelligence.career_ai import career_ai_service as bedrock_service
from .models import RashidConfig, RashidConversation, RashidMessage, RashidProfile, RashidUsage

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.
    Uses ~4 characters per token approximation for Arabic/English text.
    This is more accurate than word-based estimation.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


class RashidService:
    """Core Rashid AI service"""

    def __init__(self):
        self._config = None

    @property
    def config(self):
        if self._config is None:
            self._config = self._get_config()
        return self._config

    def _get_config(self):
        """Get or create Rashid configuration"""
        config = RashidConfig.objects.first()
        if not config:
            config = RashidConfig.objects.create(pk=1)
        return config

    def get_system_prompt(self, user=None, conversation=None):
        """Build system prompt with context"""
        base_prompt = self.config.system_prompt
        
        # Add dialect configuration
        dialect_config = self.config.dialect_config
        
        # Build user context if available
        user_context = self._build_user_context(user) if user else "لا توجد معلومات عن المستخدم بعد."
        
        # Build conversation context
        conv_context = ""
        if conversation:
            conv_context = self._format_conversation_context(conversation)
        
        system_prompt = f"""{base_prompt}

{dialect_config}

---
معلومات المستخدم:
{user_context}
"""
        
        if conv_context:
            system_prompt += f"""
سياق المحادثة:
{conv_context}
"""
        
        return system_prompt

    def _build_user_context(self, user):
        """Build user context summary from their profile and Career Brain"""
        try:
            profile = getattr(user, 'rashid_profile', None)
            
            # Try to get Career Brain first (higher confidence data)
            career_brain = getattr(user, 'career_brain', None)
            
            context_parts = []
            
            # Use Career Brain if available and has good confidence
            if career_brain and career_brain.confidence_score >= 0.3:
                # Skills from Career Brain
                if career_brain.skills and career_brain.skills.get("items"):
                    skills = career_brain.skills["items"][:10]
                    skills_str = ', '.join([s.get("name", "") for s in skills if s.get("name")])
                    if skills_str:
                        context_parts.append(f"- المهارات: {skills_str}")
                
                # Goals from Career Brain
                if career_brain.goals:
                    active_goals = [g for g in career_brain.goals if g.get("status") == "active"][:3]
                    if active_goals:
                        goals_str = ', '.join([g.get("title", "") for g in active_goals])
                        context_parts.append(f"- الأهداف: {goals_str}")
                
                # Preferences from Career Brain
                if career_brain.preferences:
                    pref_parts = []
                    if career_brain.preferences.get("open_to_remote"):
                        pref_parts.append("عن بُعد")
                    if career_brain.preferences.get("target_locations"):
                        locs = career_brain.preferences["target_locations"][:2]
                        pref_parts.append(f"المواقع: {', '.join(locs)}")
                    if pref_parts:
                        context_parts.append(f"- التفضيلات: {', '.join(pref_parts)}")
                
                # AI Observations from Career Brain
                if career_brain.ai_observations and career_brain.ai_observations.get("key_insights"):
                    insights = career_brain.ai_observations["key_insights"][:2]
                    context_parts.append(f"- ملاحظات الذكاء الاصطناعي: {'؛ '.join(insights)}")
                
                # History Summary from Career Brain
                if career_brain.history_summary:
                    if career_brain.history_summary.get("experiences"):
                        exps = career_brain.history_summary["experiences"][:2]
                        if exps:
                            context_parts.append(f"- الخبرة: {len(exps)} سنوات")
                
                # Learning from Career Brain
                if career_brain.learning and career_brain.learning.get("completed"):
                    completed = career_brain.learning["completed"][:3]
                    if completed:
                        topics = [c.get("title", "") for c in completed]
                        context_parts.append(f"- التعلم الحديث: {', '.join(topics)}")
                
                return '\n'.join(context_parts) if context_parts else "لا توجد معلومات مفصلة عن المستخدم بعد."
            
            # Fallback to Rashid profile if Career Brain is not available or has low confidence
            if not profile:
                return "لا توجد معلومات مفصلة عن المستخدم بعد."
            
            if profile.current_role:
                context_parts.append(f"- الوظيفة الحالية: {profile.current_role}")
            
            if profile.experience_level:
                context_parts.append(f"- مستوى الخبرة: {profile.experience_level}")
            
            if profile.target_role:
                context_parts.append(f"- الوظيفة المستهدفة: {profile.target_role}")
            
            if profile.skills:
                skills_str = ', '.join(profile.skills[:5]) if isinstance(profile.skills, list) else str(profile.skills)[:200]
                context_parts.append(f"- المهارات: {skills_str}")
            
            if profile.current_situation:
                context_parts.append(f"- الوضع الحالي: {profile.current_situation}")
            
            return '\n'.join(context_parts) if context_parts else "لا توجد معلومات مفصلة عن المستخدم بعد."
        
        except Exception as e:
            logger.error(f"Error building user context: {e}")
            return "لا توجد معلومات مفصلة عن المستخدم بعد."

    def _format_conversation_context(self, conversation):
        """Format conversation context data"""
        mode_names = {
            'general': 'محادثة عامة',
            'career_path': 'تخطيط المسار المهني',
            'cv_review': 'مراجعة السيرة الذاتية',
            'linkedin': 'تحسين لينكد إن',
            'cover_letter': 'كتابة خطاب التقديم',
            'interview_prep': 'التحضير للمقابلة',
            'course_advisor': 'استشارة الدورات التدريبية',
            'salary_negotiation': 'التفاوض على الراتب',
        }
        
        context = f"نوع المحادثة: {mode_names.get(conversation.mode, conversation.mode)}"
        
        if conversation.job:
            context += f"\nالوظيفة قيد المناقشة: {conversation.job.title} في {conversation.job.company_name}"
        
        return context

    def get_conversation_history(self, conversation, limit=10):
        """Get recent conversation history for context"""
        messages = conversation.messages.all().order_by('-created_at')[:limit]
        messages = list(reversed(messages))
        
        history = []
        for msg in messages:
            history.append({
                'role': msg.role,
                'content': msg.content  # Decrypted automatically by encrypted field
            })
        
        return history

    def check_token_limit(self, user):
        """Check if user has exceeded daily token limit"""
        today = timezone.now().date()
        usage, _ = RashidUsage.objects.get_or_create(
            user=user,
            date=today,
            defaults={'tokens_used': 0}
        )
        
        return usage.tokens_used < self.config.daily_token_limit

    def record_token_usage(self, user, tokens_used):
        """Record token usage for rate limiting"""
        today = timezone.now().date()
        usage, _ = RashidUsage.objects.get_or_create(
            user=user,
            date=today,
            defaults={'tokens_used': 0}
        )
        usage.tokens_used += tokens_used
        usage.save()

    def generate_response(self, conversation, user_message):
        """
        Generate Rashid's response to user message
        
        Args:
            conversation: RashidConversation instance
            user_message: User's message text
        
        Returns:
            str: Rashid's response
        """
        start_time = time.time()
        
        # Check token limit
        if not self.check_token_limit(conversation.user):
            return "عذراً، استنفدت الحد اليومي للرسائل. حاول تاني بكرة."
        
        # Save user message
        user_msg = RashidMessage.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
            tokens_used=estimate_tokens(user_message)
        )
        
        # Build prompt
        system_prompt = self.get_system_prompt(
            user=conversation.user,
            conversation=conversation
        )
        conversation_history = self.get_conversation_history(conversation)
        
        # Build messages for Bedrock
        messages = []
        for hist_msg in conversation_history[:-1]:  # Exclude current message
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
            if bedrock_service.is_available:
                response = self._invoke_bedrock(system_prompt, messages, user=conversation.user)
            else:
                # Fallback response when Bedrock is not available
                response = self._get_fallback_response(user_message)
        
        except Exception as e:
            logger.error(f"Bedrock error: {e}")
            # Check if circuit breaker is open
            if "circuit breaker" in str(e).lower():
                response = "عذراً، الخادم مزدحم حالياً. حاول تاني بعد شوية."
            else:
                response = "عذراً، حصل خطأ تقني. جرب تاني بعد شوية."
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Estimate tokens used
        input_tokens = estimate_tokens(user_message)
        output_tokens = estimate_tokens(response)
        total_tokens = input_tokens + output_tokens
        
        # Save assistant message
        RashidMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=response,
            tokens_used=output_tokens
        )
        
        # Update conversation
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # Record token usage
        self.record_token_usage(conversation.user, total_tokens)
        
        return response

    def _invoke_bedrock(self, system_prompt, messages, user=None):
        """Invoke Bedrock via the pydantic-ai tool-calling agent, falling
        back to raw invoke_model if the agent layer is unavailable."""
        try:
            return self._invoke_via_agent(system_prompt, messages, user)
        except ImportError:
            logger.info("pydantic-ai agent unavailable, falling back to raw Bedrock")
        except Exception as e:
            logger.warning("Agent call failed (%s), falling back to raw Bedrock", e)

        return self._invoke_bedrock_raw(system_prompt, messages)

    def _invoke_via_agent(self, system_prompt, messages, user=None):
        """Call the pydantic-ai Rashid agent with tool-calling support."""
        import asyncio
        from apps.intelligence.agent import get_rashid_agent, PlatformDeps
        from pydantic_ai.messages import (
            ModelRequest, ModelResponse, UserPromptPart, TextPart,
        )

        agent = get_rashid_agent()

        deps = PlatformDeps(
            user_id=user.id if user else None,
            user_email=user.email if user else "",
            user_name=getattr(user, "full_name", "") if user else "",
        )

        history = []
        for msg in messages[:-1]:
            if msg["role"] == "user":
                history.append(ModelRequest(parts=[UserPromptPart(content=msg["content"])]))
            else:
                history.append(ModelResponse(parts=[TextPart(content=msg["content"])]))

        last_msg = messages[-1]["content"] if messages else ""

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                agent.run(
                    last_msg,
                    deps=deps,
                    message_history=history if history else None,
                    instructions=system_prompt,
                )
            )
        finally:
            loop.close()

        self._track_agent_usage(result, user)
        return result.output.strip()

    def _track_agent_usage(self, result, user):
        """Emit an EventLog entry for the agent call's cost."""
        try:
            from apps.events.emitter import emit
            from apps.events.types import AI_MODEL_CALLED
            from apps.intelligence.bedrock_plugin import MODEL_COSTS, MODEL_ALIASES
            from django.conf import settings

            usage = result.usage if hasattr(result, "usage") else None
            tokens_in = getattr(usage, "input_tokens", 0) if usage else 0
            tokens_out = getattr(usage, "output_tokens", 0) if usage else 0

            model_alias = getattr(settings, "RASHID_MODEL", "sonnet")
            model_id = MODEL_ALIASES.get(model_alias, "")
            rates = MODEL_COSTS.get(model_id, {"input_per_1k": 0.003, "output_per_1k": 0.015})
            cost = round(
                (tokens_in / 1000) * rates["input_per_1k"]
                + (tokens_out / 1000) * rates["output_per_1k"],
                6,
            )

            emit(
                event_type=AI_MODEL_CALLED,
                category="ai",
                user=user,
                target_type="model",
                target_id=model_id,
                data={
                    "model": model_id,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "cost_usd": cost,
                    "user_id": user.id if user else None,
                    "operation": "chat",
                    "agent": "rashid_pydantic_ai",
                },
            )
        except Exception:
            pass

    def _invoke_bedrock_raw(self, system_prompt, messages):
        """Raw Bedrock invoke_model fallback (no tool-calling)."""
        full_prompt = ""
        for msg in messages:
            if msg["role"] == "user":
                full_prompt += f"\n\nHuman: {msg['content']}"
            else:
                full_prompt += f"\n\nAssistant: {msg['content']}"

        response = bedrock_service.invoke_model(
            prompt=full_prompt,
            system_prompt=system_prompt,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        return response.strip()

    def _get_fallback_response(self, user_message):
        """Fallback response when Bedrock is not available"""
        # Simple pattern matching for common queries
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ['أهلاً', 'مرحبا', 'السلام', 'hi', 'hello']):
            return "أهلاً بيك! أنا رشيد، مستشارك المهني. إزاي أقدر أساعدك النهاردة؟"
        
        if any(word in user_lower for word in ['سيرة', 'cv', 'resume', 'الذاتية']):
            return "أقدر أساعدك في تحسين سيرتك الذاتية. ارفعها وهأعملك مراجعة مفصلة."
        
        if any(word in user_lower for word in ['مقابلة', 'interview', 'انترفيو']):
            return "التحضير للمقابلة مهم جداً. قولي نوع الوظيفة والشركة وهأديك نصايح مخصصة."
        
        if any(word in user_lower for word in ['وظيفة', 'job', 'شغل']):
            return "أقدر أساعدك تلاقي وظيفة مناسبة. قولي مجالك وخبراتك."
        
        return "أنا هنا لمساعدتك في أي سؤال مهني. قولي إيه اللي تشتغل عليه؟"

    def create_or_get_profile(self, user):
        """Get or create Rashid profile for user"""
        profile, created = RashidProfile.objects.get_or_create(
            user=user,
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

    def start_conversation(self, user, mode='general', job=None):
        """Start a new conversation"""
        conversation = RashidConversation.objects.create(
            user=user,
            mode=mode,
            job=job
        )
        return conversation

    def get_greeting(self, user):
        """Get personalized greeting based on user profile"""
        profile = self.create_or_get_profile(user)
        
        if profile.onboarding_complete:
            return f"أهلاً بيك تاني! إزاي أقدر أساعدك النهاردة؟"
        else:
            return "أهلاً! أنا رشيد، مستشارك المهني. خليني أعرفك أكتر عشان أقدر أساعدك بشكل أفضل. إيه هي وظيفتك الحالية أو مجالك؟"


# Singleton instance
rashid_service = RashidService()