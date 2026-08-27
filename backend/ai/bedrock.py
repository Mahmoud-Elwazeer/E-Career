"""
AWS Bedrock integration — COMPATIBILITY SHIM.

This module delegates all AI calls to the centralized intelligence service at
apps.intelligence. It preserves the BedrockService interface so existing
callers continue working without modification during the migration period.

New code should import from apps.intelligence directly:
    from apps.intelligence import get_ai_service
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class BedrockService:
    """Compatibility wrapper that delegates to apps.intelligence.AIService."""

    def __init__(self):
        self._service = None
        self._model_id = getattr(settings, 'BEDROCK_MODEL_ID', 'anthropic.claude-sonnet-4-20250514-v1:0')

    @property
    def _ai(self):
        if self._service is None:
            from apps.intelligence.service import get_ai_service
            self._service = get_ai_service()
        return self._service

    @property
    def client(self):
        return self._ai.plugin._client if hasattr(self._ai.plugin, '_client') else None

    @property
    def is_available(self):
        from apps.intelligence.circuit_breaker import ai_circuit_breaker
        return ai_circuit_breaker.is_available()

    def invoke_model(self, prompt, system_prompt=None, max_tokens=4096, temperature=0.3, user=None):
        from apps.intelligence.llm_plugin import LLMRequest

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt or "",
            model="sonnet",
            max_tokens=max_tokens,
            temperature=temperature,
            user_id=getattr(user, 'id', None) if user else None,
        )
        response = self._ai.generate(request)

        if response.metadata and response.metadata.get("is_fallback"):
            raise RuntimeError("AI service temporarily unavailable")

        return response.content

    def parse_cv(self, cv_text):
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
            )

            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {e}")
            raise ValueError("Failed to parse CV - invalid JSON response")
        except Exception as e:
            logger.error(f"Error parsing CV: {e}")
            raise

    def calculate_match_score(self, profile_data, job_data):
        if not self.is_available:
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
            )

            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return self._basic_match_score(profile_data, job_data)

    def _basic_match_score(self, profile_data, job_data):
        score = 0
        breakdown = {}

        profile_skills = set(s.lower() for s in profile_data.get('skills', []))
        job_skills = set(s.lower() for s in job_data.get('required_skills', []))
        if job_skills:
            skill_match = len(profile_skills & job_skills) / len(job_skills)
            breakdown['skills'] = {
                'score': int(skill_match * 100),
                'reasoning': f"Matched {len(profile_skills & job_skills)}/{len(job_skills)} required skills"
            }
            score += skill_match * 40

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

        breakdown['education'] = {'score': 80, 'reasoning': 'Education requirements not specified'}
        score += 12
        breakdown['location'] = {'score': 50, 'reasoning': 'Location not evaluated'}
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
  "negotiation_tips": ["Highlight your AWS certification", "Mention your leadership experience"],
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
            )

            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error calculating salary guidance: {e}")
            return self._basic_salary_guidance(profile_data, job_data)

    def _basic_salary_guidance(self, profile_data, job_data):
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
            )

            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            return self._basic_interview_questions(role, experience_level, interview_type)

    def _basic_interview_questions(self, role, experience_level, interview_type):
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
                    'question': 'What are your strengths and weaknesses?',
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
            resp = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.2,
            )

            json_start = resp.find('{')
            json_end = resp.rfind('}') + 1
            json_str = resp[json_start:json_end]
            return json.loads(json_str)

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
            )

            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error ranking candidates: {e}")
            return self._basic_candidate_ranking(job_data, candidate_profiles)

    def _basic_candidate_ranking(self, job_data, candidate_profiles):
        rankings = []
        for i, profile in enumerate(candidate_profiles):
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


# Singleton instance — delegates to apps.intelligence
bedrock_service = BedrockService()
