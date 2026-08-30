"""CV Tailoring Service - Suggests improvements for specific jobs"""
import logging

logger = logging.getLogger(__name__)


class CVTailorService:
    def analyze(self, user, job):
        """Return suggestions for tailoring CV to job."""
        user_skills = []
        if hasattr(user, 'career_profile'):
            profile = user.career_profile
            user_skills = profile.skills or []
            if not user_skills:
                user_skills = [
                    s.skill.name
                    for s in profile.career_user_skills.all()[:20]
                ] if hasattr(profile, 'career_user_skills') else []

        job_skills = [js.skill.name for js in job.skills.all()[:20]]

        missing = set(js.lower() for js in job_skills) - set(
            s.lower() for s in user_skills
        )

        description = (job.description or '')[:500]

        prompt = f"""Analyze CV vs job requirements and suggest improvements.

User Skills: {', '.join(user_skills) or 'None listed'}
Job Title: {job.title}
Job Requirements: {description}

Provide 3-5 specific suggestions to tailor the CV:
1. Keywords to add
2. Skills to emphasize
3. Experience to highlight
4. Sections to expand

Format as bullet points."""

        try:
            from apps.intelligence.career_ai import career_ai_service as bedrock_service
            result = bedrock_service.invoke_model(
                prompt=prompt, max_tokens=500, temperature=0.5
            )
            content = result if isinstance(result, str) else result.get("text", "")
        except Exception as e:
            logger.warning("AI tailoring unavailable: %s", e)
            content = self._basic_suggestions(user_skills, job_skills, job)

        return {
            "suggestions": [s.strip() for s in content.split("\n") if s.strip()],
            "missing_skills": list(missing)[:10],
            "match_score": (
                len(set(s.lower() for s in user_skills) & set(s.lower() for s in job_skills))
                / len(job_skills) if job_skills else 0
            ),
        }

    def tailor_for_job(self, user, job):
        """Full before/after tailoring with ATS scores."""
        from apps.career.ats_scoring_service import ats_scoring_service

        cv_text = ''
        if hasattr(user, 'career_profile') and user.career_profile.cv_parsed_data:
            cv_text = user.career_profile.cv_parsed_data.get('text', '')

        job_desc = (job.description or '')[:2000]

        original_ats = ats_scoring_service.score(cv_text, job_desc) if cv_text else {
            'overall_score': 0, 'section_scores': {}, 'recommendations': []
        }

        analysis = self.analyze(user, job)

        tailored_text = cv_text
        if cv_text and analysis.get('missing_skills'):
            skills_line = 'Additional Skills: ' + ', '.join(analysis['missing_skills'][:5])
            tailored_text = cv_text + '\n\n' + skills_line

        tailored_ats = ats_scoring_service.score(tailored_text, job_desc) if tailored_text else original_ats

        return {
            'original_score': original_ats['overall_score'],
            'tailored_score': tailored_ats['overall_score'],
            'score_delta': tailored_ats['overall_score'] - original_ats['overall_score'],
            'suggestions': analysis['suggestions'],
            'missing_skills': analysis['missing_skills'],
            'skill_match_ratio': analysis['match_score'],
            'tailored_resume_preview': tailored_text[:3000] if tailored_text else None,
            'original_ats_breakdown': original_ats.get('section_scores', {}),
            'tailored_ats_breakdown': tailored_ats.get('section_scores', {}),
        }

    def _basic_suggestions(self, user_skills, job_skills, job):
        """Generate basic suggestions without AI."""
        lines = []
        missing = set(s.lower() for s in job_skills) - set(s.lower() for s in user_skills)
        if missing:
            lines.append(f"- Add these keywords to your resume: {', '.join(list(missing)[:5])}")
        lines.append(f"- Tailor your summary to mention '{job.title}' explicitly")
        lines.append("- Quantify your achievements with metrics where possible")
        lines.append("- Mirror the job description's language for key requirements")
        return '\n'.join(lines)


cv_tailor_service = CVTailorService()
