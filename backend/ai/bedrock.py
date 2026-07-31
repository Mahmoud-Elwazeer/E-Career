"""
AWS Bedrock integration for CV parsing and AI features
"""

import json
import logging
import time
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class BedrockService:
    """AWS Bedrock client for AI operations"""

    def __init__(self):
        self._client = None
        self._model_id = getattr(settings, 'BEDROCK_MODEL_ID', 'anthropic.claude-sonnet-4-20250514-v1:0')
        
        # Circuit breaker state
        self._circuit_open = False
        self._circuit_opened_at = None
        self._failure_count = 0
        self._success_count = 0
        self._last_check_time = None
        self._failure_window: list[float] = []  # Timestamps of recent failures

    @property
    def client(self):
        """Lazy initialization of Bedrock client"""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    'bedrock-runtime',
                    aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                    aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                    region_name=getattr(settings, 'AWS_DEFAULT_REGION', 'us-east-1')
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Bedrock client: {e}")
                self._client = None
        return self._client

    @property
    def is_available(self):
        """Check if Bedrock is configured and available"""
        return self.client is not None

    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker should be open.
        
        Returns True if circuit is OPEN (should NOT call Bedrock).
        """
        if not self._circuit_open:
            return False
        
        # Check if enough time has passed to try again (5 minutes)
        if self._circuit_opened_at:
            elapsed = time.time() - self._circuit_opened_at
            if elapsed >= 300:  # 5 minutes
                # Reset circuit and try again
                self._circuit_open = False
                self._circuit_opened_at = None
                self._failure_count = 0
                self._success_count = 0
                self._failure_window.clear()
                logger.info("circuit_breaker_reset", model=self._model_id)
                return False
        
        return True  # Circuit is still open
    
    def _record_success(self):
        """Record a successful call."""
        self._success_count += 1
        self._failure_count = max(0, self._failure_count - 1)
        
        # Reset circuit if we have enough successes
        if self._success_count >= 5 and self._circuit_open:
            self._circuit_open = False
            self._circuit_opened_at = None
            self._failure_count = 0
            self._success_count = 0
            self._failure_window.clear()
            logger.info("circuit_breaker_reset_on_success", model=self._model_id)
    
    def _record_failure(self):
        """Record a failed call."""
        self._failure_count += 1
        self._failure_window.append(time.time())
        
        # Clean old failures (older than 2 minutes)
        now = time.time()
        self._failure_window = [t for t in self._failure_window if now - t < 120]
        
        # Check if failure rate > 50% in the last 2 minutes
        if len(self._failure_window) >= 2:
            recent_failures = len([t for t in self._failure_window if now - t < 120])
            if recent_failures / max(len(self._failure_window), 1) > 0.5:
                self._circuit_open = True
                self._circuit_opened_at = now
                logger.warning(
                    "circuit_breaker_opened",
                    model=self._model_id,
                    failures=recent_failures,
                    total=len(self._failure_window),
                )
    
    def invoke_model(self, prompt, system_prompt=None, max_tokens=4096, temperature=0.3, user=None):
        """
        Invoke Claude via AWS Bedrock

        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum response tokens
            temperature: Response creativity (0-1)
            user: Optional user for cost tracking

        Returns:
            str: Model response
        """
        if not self.is_available:
            raise RuntimeError("Bedrock service is not configured")

        # Check circuit breaker
        if self._check_circuit_breaker():
            raise RuntimeError("Bedrock circuit breaker is open - service temporarily unavailable")

        start_time = time.time()
        tokens_in = 0
        tokens_out = 0
        cost_usd = 0.0

        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature
            }

            if system_prompt:
                body["system"] = system_prompt

            response = self.client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(body)
            )

            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text']

            # Estimate tokens (rough approximation: 1 token ~ 4 characters)
            tokens_in = len(prompt) // 4
            tokens_out = len(response_text) // 4

            # Calculate cost (approximate rates)
            # Claude Sonnet: $3.00/1M input tokens, $15.00/1M output tokens
            # Claude Haiku: $0.25/1M input tokens, $1.25/1M output tokens
            model_cost = getattr(settings, 'BEDROCK_MODEL_COST', {})
            input_rate = model_cost.get('input_per_million', 3.00)
            output_rate = model_cost.get('output_per_million', 15.00)
            cost_usd = (tokens_in / 1_000_000) * input_rate + (tokens_out / 1_000_000) * output_rate

            # Emit AI_MODEL_CALLED event
            try:
                from apps.events.emitter import emit
                from apps.events.types import AI_MODEL_CALLED
                emit(
                    event_type=AI_MODEL_CALLED,
                    category="ai",
                    user=user,
                    target_type="model",
                    target_id=self._model_id,
                    data={
                        "model": self._model_id,
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out,
                        "cost_usd": round(cost_usd, 6),
                        "latency_ms": round((time.time() - start_time) * 1000, 2),
                        "prompt_length": len(prompt),
                        "response_length": len(response_text),
                    },
                    request=None,
                )
            except Exception:
                pass

            # Record success
            self._record_success()
            return response_text

        except Exception as e:
            # Record failure
            self._record_failure()
            logger.error(f"Bedrock API error: {e}")
            raise

    def parse_cv(self, cv_text):
        """
        Parse CV text and extract structured information

        Args:
            cv_text: Raw CV text content

        Returns:
            dict: Structured CV data
        """
        system_prompt = """You are an expert CV parser. Extract structured information from the provided CV text.

Return a JSON object with the following structure:
{
  "personal": {
    "name": "Full name",
    "email": "email@example.com",
    "phone": "phone number",
    "location": "City, Country",
    "linkedin": "LinkedIn URL",
    "portfolio": "Portfolio/website URL",
    "summary": "Professional summary"
  },
  "experience": [
    {
      "title": "Job title",
      "company": "Company name",
      "location": "Location",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or 'Present'",
      "description": "Job description and achievements"
    }
  ],
  "education": [
    {
      "degree": "Degree type and field",
      "institution": "Institution name",
      "location": "Location",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM",
      "gpa": "GPA if mentioned"
    }
  ],
  "skills": {
    "technical": ["List of technical skills"],
    "languages": [{"language": "English", "level": "Native/Fluent/Professional/Basic"}],
    "soft_skills": ["List of soft skills"]
  },
  "certifications": [
    {
      "name": "Certification name",
      "issuer": "Issuing organization",
      "date": "YYYY-MM",
      "credential_id": "ID if provided"
    }
  ],
  "projects": [
    {
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["Tech stack"],
      "url": "Project URL if available"
    }
  ]
}

Important:
- Extract all available information
- Use null for missing fields
- Normalize date formats to YYYY-MM
- Clean up formatting and special characters
- Infer information only when clearly evident
"""

        prompt = f"""Parse this CV and extract structured information:

{cv_text}

Return ONLY the JSON object, no additional text."""

        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=8000,
                temperature=0.1,
                user=None  # CV parsing is not user-specific
            )

            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]

            parsed_data = json.loads(json_str)
            return parsed_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Bedrock response: {e}")
            logger.error(f"Response: {response[:500] if 'response' in dir() else 'N/A'}")
            raise ValueError("Failed to parse CV - invalid JSON response")
        except Exception as e:
            logger.error(f"Error parsing CV: {e}")
            raise

    def calculate_match_score(self, profile_data, job_data):
        """
        Calculate how well a profile matches a job using AI

        Args:
            profile_data: User profile dict
            job_data: Job dict

        Returns:
            dict: Match score and breakdown
        """
        if not self.is_available:
            # Fallback to basic algorithm
            return self._basic_match_score(profile_data, job_data)

        system_prompt = """You are an expert job matching AI. Analyze how well a candidate's profile matches a job posting.

Evaluate across these dimensions:
- Skills match (40%): Required skills vs candidate skills
- Experience match (25%): Years and relevance of experience
- Education match (15%): Required vs actual education level
- Location match (10%): Location preferences and job location
- Cultural fit (10%): Job description vs candidate profile alignment

Return JSON:
{
  "overall_score": 85,
  "breakdown": {
    "skills": {"score": 90, "reasoning": "Strong match with 8/10 required skills"},
    "experience": {"score": 80, "reasoning": "Has 5 years, job requires 3-5 years"},
    "education": {"score": 100, "reasoning": "BS in Computer Science matches requirement"},
    "location": {"score": 50, "reasoning": "Open to relocation but prefers remote"},
    "cultural_fit": {"score": 85, "reasoning": "Strong alignment with company values"}
  },
  "strengths": ["Excellent Python skills", "Relevant industry experience"],
  "gaps": ["Missing AWS certification", "Limited management experience"],
  "recommendation": "Strong candidate - recommended for interview"
}
"""

        prompt = f"""Analyze this job match:

CANDIDATE PROFILE:
{json.dumps(profile_data, indent=2)}

JOB POSTING:
{json.dumps(job_data, indent=2)}

Provide match score and detailed analysis."""

        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.2,
                user=None  # Match scoring is not user-specific
            )

            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]

            match_data = json.loads(json_str)
            return match_data

        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return self._basic_match_score(profile_data, job_data)

    def _basic_match_score(self, profile_data, job_data):
        """Fallback basic matching algorithm"""
        score = 0
        breakdown = {}

        # Skills match (40%)
        profile_skills = set(s.lower() for s in profile_data.get('skills', []))
        job_skills = set(s.lower() for s in job_data.get('required_skills', []))
        if job_skills:
            skill_match = len(profile_skills & job_skills) / len(job_skills)
            breakdown['skills'] = {
                'score': int(skill_match * 100),
                'reasoning': f"Matched {len(profile_skills & job_skills)}/{len(job_skills)} required skills"
            }
            score += skill_match * 40

        # Experience match (25%)
        profile_exp = profile_data.get('experience_years', 0)
        job_exp = job_data.get('experience_level', '')
        exp_map = {'entry': 1, 'junior': 2, 'mid': 4, 'senior': 6, 'lead': 8, 'executive': 10}
        required_exp = exp_map.get(job_exp.lower(), 0)
        if profile_exp >= required_exp:
            score += 25
            breakdown['experience'] = {'score': 100, 'reasoning': f"Has {profile_exp} years, requires {required_exp}+"}
        else:
            exp_score = int((profile_exp / required_exp) * 100) if required_exp else 100
            score += (exp_score / 100) * 25
            breakdown['experience'] = {'score': exp_score, 'reasoning': f"Has {profile_exp} years, requires {required_exp}+"}

        # Education (15%)
        breakdown['education'] = {'score': 80, 'reasoning': 'Education requirements not specified'}
        score += 12

        # Location (10%)
        profile_loc = profile_data.get('preferred_locations', [])
        job_loc = job_data.get('location', '')
        if job_loc and any(loc.lower() in job_loc.lower() for loc in profile_loc):
            score += 10
            breakdown['location'] = {'score': 100, 'reasoning': 'Location matches preference'}
        else:
            breakdown['location'] = {'score': 50, 'reasoning': 'Location not in preferences'}

        # Cultural fit (10%)
        breakdown['cultural_fit'] = {'score': 70, 'reasoning': 'Based on profile alignment'}
        score += 7

        return {
            'overall_score': int(min(score, 100)),
            'breakdown': breakdown,
            'strengths': list(profile_skills & job_skills) if job_skills else [],
            'gaps': list(job_skills - profile_skills) if job_skills else [],
            'recommendation': 'Candidate profile analyzed'
        }


# Singleton instance
bedrock_service = BedrockService()