"""CV Tailoring Service - Suggests improvements for specific jobs"""
from apps.intelligence.career_ai import career_ai_service as bedrock_service

class CVTailorService:
    def analyze(self, user, job):
        """Return suggestions for tailoring CV to job."""
        user_skills = [s.skill.name for s in user.career_profile.career_user_skills.all()[:20]] if hasattr(user, 'career_profile') else []
        job_skills = [js.skill.name for js in job.job_skills.all()[:20]]

        missing = set(job_skills) - set(user_skills)

        prompt = f"""Analyze CV vs job requirements and suggest improvements.

User Skills: {', '.join(user_skills) or 'None listed'}
Job Title: {job.title}
Job Requirements: {job.requirements[:500] if job.requirements else job.description[:500]}

Provide 3-5 specific suggestions to tailor the CV:
1. Keywords to add
2. Skills to emphasize
3. Experience to highlight
4. Sections to expand

Format as bullet points."""

        result = bedrock_service.invoke_model(prompt=prompt, max_tokens=500, temperature=0.5)

        # Handle response (invoke_model returns string directly)
        content = result if isinstance(result, str) else result.get("text", "")

        return {
            "suggestions": [s.strip() for s in content.split("\n") if s.strip()],
            "missing_skills": list(missing)[:10],
            "match_score": len(set(user_skills) & set(job_skills)) / len(job_skills) if job_skills else 0
        }

cv_tailor_service = CVTailorService()
