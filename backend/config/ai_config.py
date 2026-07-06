"""
AI Model Configuration for E-Career Platform
Optimized for cost-effectiveness while maintaining quality
"""
from decouple import config

# ═══════════════════════════════════════════════════════════════
# AI MODEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Primary AI Model (RECOMMENDED: Meta Llama 3.3 70B)
# Cost: $0.99 per 1M tokens (input & output)
# Savings: 89% vs Claude Sonnet ($9/1M tokens)
PRIMARY_AI_MODEL = {
    'provider': 'bedrock',
    'model_id': 'meta.llama3-3-70b-instruct-v1:0',
    'region': config('AWS_BEDROCK_REGION', default='us-east-1'),
    'cost_per_1m_tokens': 0.99,
    'max_tokens': 4096,
    'temperature': 0.7,
    'description': 'Meta Llama 3.3 70B - High quality, cost-effective',
}

# Alternative Model (For simple tasks - even cheaper)
# Cost: $0.35 input / $1.05 output per 1M tokens
ALTERNATIVE_AI_MODEL = {
    'provider': 'bedrock',
    'model_id': 'meta.llama4-scout-17b-instruct-v1:0',
    'region': config('AWS_BEDROCK_REGION', default='us-east-1'),
    'cost_per_1m_tokens': 0.70,  # Average
    'max_tokens': 2048,
    'temperature': 0.7,
    'description': 'Meta Llama 4 Scout - Ultra cost-effective',
}

# Fallback Model (Keep Claude Haiku as backup)
# Cost: $0.25 input / $1.25 output per 1M tokens
FALLBACK_AI_MODEL = {
    'provider': 'bedrock',
    'model_id': 'anthropic.claude-3-haiku-20240307-v1:0',
    'region': config('AWS_BEDROCK_REGION', default='us-east-1'),
    'cost_per_1m_tokens': 0.75,  # Average
    'max_tokens': 4096,
    'temperature': 0.7,
    'description': 'Claude 3 Haiku - High quality fallback',
}

# ═══════════════════════════════════════════════════════════════
# USE CASE SPECIFIC CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════

# CV Parsing - Use primary model (high accuracy needed)
CV_PARSING_MODEL = PRIMARY_AI_MODEL

# Rashid AI Chat - Use primary model (conversational quality)
RASHID_CHAT_MODEL = PRIMARY_AI_MODEL

# Career Tools - Use primary model (quality advice)
CAREER_TOOLS_MODEL = PRIMARY_AI_MODEL

# Job Recommendations - Use primary model (matching quality)
RECOMMENDATIONS_MODEL = PRIMARY_AI_MODEL

# Email Content Generation - Can use alternative (simple task)
EMAIL_GENERATION_MODEL = ALTERNATIVE_AI_MODEL

# ═══════════════════════════════════════════════════════════════
# PROMPT TEMPLATES
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPTS = {
    'cv_parsing': """You are an expert CV/resume parser. Extract structured information from CVs.
Focus on: skills, experience, education, contact information.
Return data in JSON format. Be thorough and accurate.""",

    'rashid_chat': """You are Rashid, an AI career mentor for the USAM Career Compass platform.
You help job seekers with career advice in both English and Egyptian Arabic.
Be helpful, professional, and empathetic. Provide actionable career guidance.""",

    'career_tools': """You are a career development expert. Provide professional, actionable advice.
Be specific, practical, and encouraging. Focus on concrete steps the user can take.""",

    'recommendations': """You are a job matching expert. Analyze user profiles and job descriptions.
Provide match scores and explain why jobs are good fits. Consider skills, experience, and preferences.""",

    'email_content': """You are a professional email content creator. Write engaging, professional emails.
Keep them concise, action-oriented, and user-friendly. Match the tone to the campaign type.""",
}

# ═══════════════════════════════════════════════════════════════
# COST TRACKING
# ═══════════════════════════════════════════════════════════════

def estimate_monthly_cost(tokens_per_month: int, model: dict) -> float:
    """Estimate monthly AI cost based on token usage"""
    tokens_in_millions = tokens_per_month / 1_000_000
    return tokens_in_millions * model['cost_per_1m_tokens']

def get_cost_comparison():
    """Get cost comparison vs previous Claude setup"""
    return {
        'previous_model': 'Claude 3.5 Sonnet',
        'previous_cost_per_1m': 9.00,  # Average of $3 input + $15 output
        'new_model': PRIMARY_AI_MODEL['description'],
        'new_cost_per_1m': PRIMARY_AI_MODEL['cost_per_1m_tokens'],
        'savings_percentage': round((1 - PRIMARY_AI_MODEL['cost_per_1m_tokens'] / 9.00) * 100, 1),
        'monthly_savings_estimate': 112,  # Based on typical usage
        'annual_savings_estimate': 1344,
    }

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_model_for_task(task: str) -> dict:
    """Get the appropriate AI model for a specific task"""
    model_map = {
        'cv_parsing': CV_PARSING_MODEL,
        'chat': RASHID_CHAT_MODEL,
        'tools': CAREER_TOOLS_MODEL,
        'recommendations': RECOMMENDATIONS_MODEL,
        'email': EMAIL_GENERATION_MODEL,
    }
    return model_map.get(task, PRIMARY_AI_MODEL)

def get_all_models():
    """Get list of all configured models"""
    return {
        'primary': PRIMARY_AI_MODEL,
        'alternative': ALTERNATIVE_AI_MODEL,
        'fallback': FALLBACK_AI_MODEL,
    }
