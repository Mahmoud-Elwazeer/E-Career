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


    def calculate_salary_guidance(self, profile_data, job_data):
        """
        Calculate salary guidance for a candidate based on profile and job data.
        
        Args:
            profile_data: User profile dict
            job_data: Job dict
            
        Returns:
            dict: Salary guidance with range and reasoning
        """
        system_prompt = """You are an expert salary negotiation advisor. Analyze the job posting and candidate profile
to provide salary guidance.

Return JSON:
{
  "min_salary": 80000,
  "target_salary": 95000,
  "max_salary": 110000,
  "currency": "USD",
  "confidence": 0.85,
  "reasoning": "Based on 5 years experience and market data...",
  "negotiation_tips": [
    "Highlight your AWS certification",
    "Mention your leadership experience"
  ],
  "market_comparison": {
    "local_average": 85000,
    "industry_average": 92000,
    "experience_adjustment": "+15%"
  }
}
"""
        
        prompt = f"""Provide salary guidance for this candidate applying to this job:

CANDIDATE PROFILE:
{json.dumps(profile_data, indent=2)}

JOB POSTING:
{json.dumps(job_data, indent=2)}

Provide salary guidance with reasoning and negotiation tips."""

        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.2,
                user=None
            )
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            salary_data = json.loads(json_str)
            return salary_data
            
        except Exception as e:
            logger.error(f"Error calculating salary guidance: {e}")
            return self._basic_salary_guidance(profile_data, job_data)
    
    def _basic_salary_guidance(self, profile_data, job_data):
        """Fallback basic salary guidance"""
        job_salary_min = job_data.get('salary_min')
        job_salary_max = job_data.get('salary_max')
        currency = job_data.get('salary_currency', 'USD')
        
        if job_salary_min and job_salary_max:
            target = (job_salary_min + job_salary_max) / 2
            return {
                'min_salary': int(job_salary_min * 0.9),
                'target_salary': int(target),
                'max_salary': int(job_salary_max * 1.1),
                'currency': currency,
                'confidence': 0.5,
                'reasoning': 'Based on job posting salary range',
                'negotiation_tips': ['Research market rates', 'Consider benefits package'],
                'market_comparison': {
                    'local_average': int(target),
                    'industry_average': int(target),
                    'experience_adjustment': '0%'
                }
            }
        
        return {
            'min_salary': None,
            'target_salary': None,
            'max_salary': None,
            'currency': currency,
            'confidence': 0.3,
            'reasoning': 'No salary range provided in job posting',
            'negotiation_tips': ['Ask about salary range in interview'],
            'market_comparison': {
                'local_average': None,
                'industry_average': None,
                'experience_adjustment': None
            }
        }
    
    def generate_interview_questions(self, role, experience_level, interview_type='technical'):
        """
        Generate interview questions for a specific role and experience level.
        
        Args:
            role: Job title/role
            experience_level: entry, mid, senior, lead
            interview_type: technical, behavioral, coding, system_design
            
        Returns:
            dict: Interview questions and evaluation criteria
        """
        system_prompt = """You are an expert interviewer. Generate relevant interview questions based on the role,
experience level, and interview type.

Return JSON:
{
  "questions": [
    {
      "question": "Question text",
      "type": "technical|behavioral|coding",
      "difficulty": "junior|mid|senior|lead",
      "evaluation_criteria": ["What to look for in a good answer"],
      "red_flags": ["Signs of a weak answer"]
    }
  ],
  "total_questions": 5,
  "estimated_duration_minutes": 30,
  "preparation_tips": ["Tips for the candidate"]
}
"""
        
        prompt = f"""Generate {interview_type} interview questions for a {experience_level} level {role} position.

Return ONLY the JSON object."""

        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.3,
                user=None
            )
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            questions_data = json.loads(json_str)
            return questions_data
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            return self._basic_interview_questions(role, experience_level, interview_type)
    
    def _basic_interview_questions(self, role, experience_level, interview_type):
        """Fallback basic interview questions"""
        return {
            'questions': [
                {
                    'question': f'Can you tell me about your experience with {role}?',
                    'type': 'behavioral',
                    'difficulty': experience_level,
                    'evaluation_criteria': ['Clear communication', 'Relevant experience', 'Specific examples'],
                    'red_flags': ['Vague answers', 'Lack of specific examples']
                },
                {
                    'question': f'What are your strengths and weaknesses?',
                    'type': 'behavioral',
                    'difficulty': experience_level,
                    'evaluation_criteria': ['Self-awareness', 'Honesty', 'Improvement mindset'],
                    'red_flags': ['Generic answers', 'No self-awareness']
                }
            ],
            'total_questions': 2,
            'estimated_duration_minutes': 15,
            'preparation_tips': ['Review the job description', 'Prepare STAR examples']
        }
    
    def evaluate_interview_response(self, question, response, role, interview_type='technical'):
        """
        Evaluate a candidate's interview response.
        
        Args:
            question: The interview question
            response: Candidate's response
            role: Job title/role
            interview_type: technical, behavioral, coding, system_design
            
        Returns:
            dict: Evaluation score and feedback
        """
        system_prompt = """You are an expert interviewer evaluator. Evaluate candidate responses to interview questions.

Return JSON:
{
  "score": 75,
  "max_score": 100,
  "breakdown": {
    "relevance": {"score": 80, "feedback": "Answer was relevant to the question"},
    "depth": {"score": 70, "feedback": "Could provide more detail"},
    "structure": {"score": 85, "feedback": "Well-structured answer"},
    "technical_accuracy": {"score": 70, "feedback": "Some technical inaccuracies"}
  },
  "strengths": ["Good communication skills", "Relevant experience"],
  "weaknesses": ["Lacked specific examples", "Some technical gaps"],
  "improvement_tips": ["Provide more specific examples", "Review technical concepts"],
  "recommendation": "Consider for next round"
}
"""
        
        prompt = f"""Evaluate this interview response:

INTERVIEW TYPE: {interview_type}
ROLE: {role}
QUESTION: {question}
CANDIDATE RESPONSE: {response}

Provide evaluation with scores and feedback."""

        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.2,
                user=None
            )
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            evaluation_data = json.loads(json_str)
            return evaluation_data
            
        except Exception as e:
            logger.error(f"Error evaluating interview response: {e}")
            return {
                'score': 50,
                'max_score': 100,
                'breakdown': {},
                'strengths': [],
                'weaknesses': ['Evaluation failed'],
                'improvement_tips': ['Try again'],
                'recommendation': 'Review required'
            }
    
    def rank_candidates_for_job(self, job_data, candidate_profiles):
        """
        Rank multiple candidates for a job using AI.
        
        Args:
            job_data: Job posting data
            candidate_profiles: List of candidate profile data
            
        Returns:
            dict: Ranked candidates with scores and explanations
        """
        system_prompt = """You are an expert recruitment assistant. Rank candidates based on their fit for a job.

Return JSON:
{
  "rankings": [
    {
      "candidate_id": 1,
      "overall_score": 85,
      "skill_match_score": 90,
      "experience_score": 80,
      "education_score": 95,
      "explanation": "Strong match with 9/10 required skills...",
      "recommendation": "High priority - schedule interview"
    }
  ],
  "total_candidates": 5,
  "top_candidate_id": 1
}
"""
        
        prompt = f"""Rank these candidates for the following job:

JOB POSTING:
{json.dumps(job_data, indent=2)}

CANDIDATE PROFILES:
{json.dumps(candidate_profiles, indent=2)}

Provide rankings with detailed explanations."""

        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=3000,
                temperature=0.2,
                user=None
            )
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            ranking_data = json.loads(json_str)
            return ranking_data
            
        except Exception as e:
            logger.error(f"Error ranking candidates: {e}")
            return self._basic_candidate_ranking(job_data, candidate_profiles)
    
    def _basic_candidate_ranking(self, job_data, candidate_profiles):
        """Fallback basic candidate ranking"""
        rankings = []
        for i, profile in enumerate(candidate_profiles):
            # Basic scoring
            score = 50
            skills = profile.get('skills', [])
            required_skills = job_data.get('required_skills', [])
            
            if required_skills:
                match_count = len(set(s.lower() for s in skills) & set(s.lower() for s in required_skills))
                skill_score = (match_count / len(required_skills)) * 100
                score += skill_score * 0.4
            
            rankings.append({
                'candidate_id': i,
                'overall_score': min(int(score), 100),
                'skill_match_score': int(score * 0.5),
                'experience_score': int(score * 0.3),
                'education_score': int(score * 0.2),
                'explanation': 'Basic algorithm ranking',
                'recommendation': 'Review recommended'
            })
        
        return {
            'rankings': sorted(rankings, key=lambda x: x['overall_score'], reverse=True),
            'total_candidates': len(rankings),
            'top_candidate_id': rankings[0]['candidate_id'] if rankings else None
        }


# Singleton instance
bedrock_service = BedrockService()
