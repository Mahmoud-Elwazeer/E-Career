"""
Cover Letter Generation Service

Generates personalized cover letters using AI based on user profile and job requirements.
"""
import logging
from typing import Optional
from django.conf import settings
from apps.intelligence.career_ai import career_ai_service as bedrock_service

logger = logging.getLogger(__name__)


class CoverLetterService:
    """Service for generating personalized cover letters."""

    def generate_cover_letter(
        self,
        user,
        job,
        user_profile_text: Optional[str] = None,
        tone: str = "professional"
    ) -> dict:
        """
        Generate a tailored cover letter for a specific job.

        Args:
            user: User instance
            job: Job instance
            user_profile_text: Optional custom profile text (otherwise auto-generated)
            tone: Tone of the letter ('professional', 'enthusiastic', 'formal')

        Returns:
            dict with 'content', 'confidence', and 'suggestions'
        """
        try:
            # Build context from user's profile
            context = self._build_user_context(user, user_profile_text)

            # Build job context
            job_context = self._build_job_context(job)

            # Generate cover letter via AI
            prompt = self._build_prompt(context, job_context, tone)

            response = bedrock_service.invoke_model(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.7,
                system_prompt=(
                    "You are an expert career coach writing personalized cover letters. "
                    "Write in first person. Be specific, genuine, and compelling. "
                    "Reference the candidate's actual experience and the job's specific requirements."
                )
            )

            # Parse response
            content = response if isinstance(response, str) else response.get("text", "")

            return {
                "content": content,
                "confidence": 0.85,  # High confidence for Sonnet
                "word_count": len(content.split()),
                "tone": tone,
            }

        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}")
            return {
                "content": self._grounded_fallback(user, job),
                "confidence": 0.5,  # deterministic + grounded in real matched skills
                "degraded": True,   # signals AI path unavailable (e.g. Bedrock blocked)
                "error": str(e),
            }

    def _build_user_context(self, user, custom_text: Optional[str] = None) -> str:
        """Build user context from profile."""
        if custom_text:
            return custom_text

        context_parts = []

        # Basic info
        context_parts.append(f"Name: {user.get_full_name()}")

        # Career profile if exists
        if hasattr(user, 'career_profile'):
            profile = user.career_profile

            # Skills
            if hasattr(profile, 'career_user_skills'):
                skills = profile.career_user_skills.all()[:10]
                if skills:
                    skill_names = [s.skill.name for s in skills if s.skill]
                    context_parts.append(f"Skills: {', '.join(skill_names)}")

            # CV parsed data
            if profile.cv_parsed_data:
                data = profile.cv_parsed_data
                if 'experience' in data:
                    context_parts.append(f"Experience: {data['experience']}")
                if 'education' in data:
                    context_parts.append(f"Education: {data['education']}")

        return "\n".join(context_parts) if context_parts else "No profile data available."

    def _build_job_context(self, job) -> str:
        """Build job context."""
        parts = [
            f"Company: {job.company.name}",
            f"Position: {job.title}",
            f"Description: {job.description[:500]}",  # Truncate if long
        ]

        if job.requirements:
            parts.append(f"Requirements: {job.requirements[:300]}")

        return "\n".join(parts)

    def _build_prompt(self, user_context: str, job_context: str, tone: str) -> str:
        """Build the AI prompt."""
        return f"""Write a compelling cover letter for this job application.

CANDIDATE PROFILE:
{user_context}

JOB DETAILS:
{job_context}

REQUIREMENTS:
- Write in first person (I, my, etc.)
- Tone: {tone}
- Length: 250-350 words
- Structure: Opening paragraph → Why I'm a fit → Why I'm excited → Closing
- Reference specific skills/experience that match the job requirements
- Be genuine and specific, not generic
- End with a call to action

OUTPUT FORMAT:
Return ONLY the cover letter text, no preamble or explanation.
"""

    def _fallback_cover_letter(self, user, job) -> str:
        """Minimal template (kept for compatibility)."""
        name = user.get_full_name()
        company = job.company.name
        position = job.title
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {position} position at {company}. With my background and skills, I believe I would be a valuable addition to your team.

My experience aligns well with the requirements outlined in the job description. I am particularly drawn to this opportunity because of {company}'s reputation in the industry and the chance to contribute to meaningful work.

I would welcome the opportunity to discuss how my qualifications match your needs. Thank you for considering my application.

Sincerely,
{name}"""

    def _grounded_fallback(self, user, job) -> str:
        """Deterministic, evidence-grounded draft used when the AI path is
        unavailable (e.g. Bedrock blocked).

        Unlike the bland generic template, this references the candidate's
        ACTUAL skills that overlap the job — reusing the deterministic matching
        engine so the letter is specific and honest even without AI. No
        fabrication: only skills the candidate actually has AND the job asks for
        are named.
        """
        name = user.get_full_name() if hasattr(user, "get_full_name") else getattr(user, "name", "")
        company = getattr(getattr(job, "company", None), "name", "the company")
        position = getattr(job, "title", "the role")

        matched_skills: list[str] = []
        try:
            profile = getattr(user, "career_profile", None) or getattr(user, "profile", None)
            if profile is not None:
                from apps.matching.engine import unified_matching_engine
                result = unified_matching_engine.match(profile, job)
                matched_skills = result.matched_requirements[:6]
        except Exception:  # matching is best-effort here
            matched_skills = []

        if matched_skills:
            skills_sentence = (
                "In particular, my experience with "
                + self._join_human(matched_skills)
                + f" maps directly to what the {position} role requires."
            )
        else:
            skills_sentence = (
                "My background aligns with the core requirements outlined in the job description."
            )

        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {position} position at {company}. {skills_sentence}

I am drawn to this opportunity because it lets me apply these strengths to meaningful work, and I am confident I can contribute quickly to your team.

I would welcome the chance to discuss how my experience matches your needs. Thank you for considering my application.

Sincerely,
{name}"""

    @staticmethod
    def _join_human(items: list[str]) -> str:
        items = [str(i) for i in items if i]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"


# Global instance
cover_letter_service = CoverLetterService()
