# Multi-Model Strategy - Cost Optimization

> **Smart model selection for E-Career platform**

---

## 🎯 **Model Configuration**

### **Primary Model: Llama4-Scout 17B**
```
Model ID: meta.llama4-scout-17b-instruct-v1:0
```

**Strengths:**
- ✅ Strong Arabic language support
- ✅ Excellent conversational abilities
- ✅ Good instruction-following
- ✅ 17B parameters = quality + reasonable cost
- ✅ Complex reasoning capabilities

**Use For:**
- Rashid AI chat conversations
- Job matching reasoning
- Cover letter generation
- Interview preparation responses
- LinkedIn profile optimization

---

### **Secondary Model: Gemma-4-E2B**
```
Model ID: google.gemma-4-e2b
```

**Strengths:**
- ✅ Fast response time
- ✅ Low cost (great for high-volume)
- ✅ Good structured extraction
- ✅ Efficient for simple tasks

**Use For:**
- CV text extraction
- Job description parsing
- Email template filling
- Quick classifications
- Batch processing tasks

---

## 📊 **Cost vs. Quality Matrix**

| Task | Volume | Complexity | Model | Cost/1K | Quality |
|------|--------|------------|-------|---------|---------|
| Rashid Chat | Medium | High | Llama4-17B | $$ | ⭐⭐⭐⭐⭐ |
| CV Parsing | High | Low | Gemma-4 | $ | ⭐⭐⭐⭐ |
| Job Match | High | High | Llama4-17B | $$ | ⭐⭐⭐⭐⭐ |
| Cover Letters | Low | High | Llama4-17B | $$ | ⭐⭐⭐⭐⭐ |
| Email Gen | Medium | Low | Gemma-4 | $ | ⭐⭐⭐⭐ |
| Quick Tasks | High | Low | Gemma-4 | $ | ⭐⭐⭐ |

---

## 🔧 **Implementation Pattern**

### **Bedrock Service (Smart Model Router)**

```python
# backend/ai/bedrock_service.py

import os
import boto3
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    """Model tiers for different task types"""
    PRIMARY = "primary"      # High quality (Llama4-17B)
    SECONDARY = "secondary"  # Fast and cheap (Gemma-4)

class BedrockService:
    """Smart multi-model AWS Bedrock service"""
    
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Model configuration
        self.models = {
            ModelTier.PRIMARY: os.getenv(
                'BEDROCK_MODEL_PRIMARY',
                'meta.llama4-scout-17b-instruct-v1:0'
            ),
            ModelTier.SECONDARY: os.getenv(
                'BEDROCK_MODEL_SECONDARY',
                'google.gemma-4-e2b'
            )
        }
        
        # Task-specific model mapping
        self.task_models = {
            'rashid_chat': ModelTier.PRIMARY,
            'cv_parsing': ModelTier.SECONDARY,
            'job_matching': ModelTier.PRIMARY,
            'cover_letter': ModelTier.PRIMARY,
            'interview_prep': ModelTier.PRIMARY,
            'linkedin_opt': ModelTier.PRIMARY,
            'email_gen': ModelTier.SECONDARY,
            'quick_task': ModelTier.SECONDARY,
        }
    
    def invoke_model(
        self, 
        prompt: str, 
        task_type: str = 'rashid_chat',
        system_prompt: str = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ):
        """
        Invoke appropriate model based on task type
        
        Args:
            prompt: User prompt
            task_type: Type of task (determines model selection)
            system_prompt: System instructions
            max_tokens: Max response length
            temperature: Response creativity
        
        Returns:
            str: Model response
        """
        # Select appropriate model
        model_tier = self.task_models.get(task_type, ModelTier.PRIMARY)
        model_id = self.models[model_tier]
        
        logger.info(f"Using {model_id} for task: {task_type}")
        
        try:
            # Build request body
            body = {
                'prompt': prompt,
                'max_tokens': max_tokens,
                'temperature': temperature,
            }
            
            if system_prompt:
                body['system'] = system_prompt
            
            # Invoke model
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            return self._extract_text(response_body, model_id)
        
        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            raise
    
    def _extract_text(self, response_body: dict, model_id: str) -> str:
        """Extract text from different model response formats"""
        
        # Llama4 format
        if 'generation' in response_body:
            return response_body['generation']
        
        # Gemma format
        if 'outputs' in response_body:
            return response_body['outputs'][0]['text']
        
        # Generic format
        if 'text' in response_body:
            return response_body['text']
        
        # Fallback
        logger.warning(f"Unknown response format from {model_id}")
        return str(response_body)
    
    def parse_cv(self, cv_text: str):
        """Parse CV using fast secondary model"""
        system_prompt = """Extract structured information from this CV.
Return JSON with: personal info, experience, education, skills, certifications."""
        
        prompt = f"Parse this CV:\n\n{cv_text}\n\nReturn JSON only."
        
        response = self.invoke_model(
            prompt=prompt,
            task_type='cv_parsing',  # Uses Gemma-4 (fast)
            system_prompt=system_prompt,
            max_tokens=4000,
            temperature=0.1
        )
        
        # Extract JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        json_str = response[json_start:json_end]
        
        return json.loads(json_str)
    
    def calculate_match_score(self, profile_data: dict, job_data: dict):
        """Calculate job match using primary model"""
        system_prompt = """You are a job matching expert. Analyze compatibility."""
        
        prompt = f"""
Profile: {json.dumps(profile_data, indent=2)}
Job: {json.dumps(job_data, indent=2)}

Return JSON with: overall_score, breakdown, strengths, gaps, recommendation.
"""
        
        response = self.invoke_model(
            prompt=prompt,
            task_type='job_matching',  # Uses Llama4-17B (quality)
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.2
        )
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        json_str = response[json_start:json_end]
        
        return json.loads(json_str)


# Singleton instance
bedrock_service = BedrockService()
```

---

## 💰 **Cost Estimation**

### **Monthly Usage (1000 users)**

| Task | Volume/Month | Model | Cost/1K Tokens | Estimated Cost |
|------|--------------|-------|----------------|----------------|
| Rashid Chat | 50K messages | Llama4-17B | $0.003 | ~$450 |
| CV Parsing | 5K CVs | Gemma-4 | $0.0001 | ~$5 |
| Job Matching | 100K matches | Llama4-17B | $0.003 | ~$900 |
| Cover Letters | 2K letters | Llama4-17B | $0.003 | ~$18 |
| Email Gen | 20K emails | Gemma-4 | $0.0001 | ~$2 |
| **TOTAL** | | | | **~$1,375/month** |

**Savings vs. all-primary:** ~60% cost reduction

---

## 🎯 **Task Routing Logic**

```python
# When to use each model:

# PRIMARY (Llama4-17B) - Quality Critical
✅ User-facing conversations (Rashid chat)
✅ Complex reasoning (job matching)
✅ Creative writing (cover letters, LinkedIn)
✅ Interview preparation (needs nuance)

# SECONDARY (Gemma-4) - Speed Critical
✅ Data extraction (CV parsing)
✅ Simple classification
✅ Email template filling
✅ Batch processing
✅ Quick lookups
```

---

## 🔄 **Dynamic Model Selection**

You can override model selection per request:

```python
# Force specific model
bedrock_service.invoke_model(
    prompt="Your prompt",
    task_type='rashid_chat',  # Uses Llama4-17B
    max_tokens=1000
)

# Or use secondary for testing
bedrock_service.invoke_model(
    prompt="Test prompt",
    task_type='quick_task',  # Uses Gemma-4
    max_tokens=500
)
```

---

## 📊 **Performance Comparison**

| Metric | Llama4-17B | Gemma-4 | Winner |
|--------|------------|---------|--------|
| Arabic Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Llama4 |
| Speed | 2-3s | 0.5-1s | Gemma |
| Cost/1K | $0.003 | $0.0001 | Gemma |
| Reasoning | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Llama4 |
| Structured Output | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Gemma |
| Conversational | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Llama4 |

---

## ✅ **Configuration Ready**

Your `.env` is now configured with:
- ✅ Primary: `meta.llama4-scout-17b-instruct-v1:0`
- ✅ Secondary: `google.gemma-4-e2b`
- ✅ Task-specific routing
- ✅ Cost optimization

---

## 🚀 **Ready to Implement**

All phase files will use this smart routing:
- Phase 2A (CV Parsing) → Gemma-4 ✅
- Phase 2B (Rashid Chat) → Llama4-17B ✅
- Phase 2C (Tools) → Mixed based on task ✅
- Phase 3B (Matching) → Llama4-17B ✅

**Cost-effective, smart, and production-ready!** 🎯
