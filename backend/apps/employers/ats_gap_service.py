"""
ATS Gap Analysis Service

Analyzes job postings to identify quality gaps and suggests improvements
for better ATS compatibility and candidate matching.
"""
import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class ATSGapAnalyzer:
    """Identifies gaps in job postings that reduce ATS effectiveness."""

    MINIMUM_DESCRIPTION_LENGTH = 200
    MINIMUM_REQUIREMENTS_LENGTH = 100
    RECOMMENDED_SKILLS_COUNT = 5

    def analyze(self, job_posting) -> Dict:
        """
        Analyze a job posting and return gap analysis with suggestions.

        Returns:
            {
                score: int (0-100),
                gaps: [{field, severity, message, suggestion}],
                strengths: [str],
            }
        """
        gaps = []
        strengths = []
        score = 100

        # 1. Title quality
        title_analysis = self._check_title(job_posting.title)
        gaps.extend(title_analysis['gaps'])
        strengths.extend(title_analysis['strengths'])
        score -= title_analysis['penalty']

        # 2. Description completeness
        desc_analysis = self._check_description(job_posting.description)
        gaps.extend(desc_analysis['gaps'])
        strengths.extend(desc_analysis['strengths'])
        score -= desc_analysis['penalty']

        # 3. Requirements clarity
        req_analysis = self._check_requirements(job_posting.requirements)
        gaps.extend(req_analysis['gaps'])
        strengths.extend(req_analysis['strengths'])
        score -= req_analysis['penalty']

        # 4. Salary transparency
        if not job_posting.salary_min and not job_posting.salary_max:
            gaps.append({
                'field': 'salary',
                'severity': 'medium',
                'message': 'No salary range specified',
                'suggestion': 'Adding salary range increases applications by 30-50%'
            })
            score -= 10
        else:
            strengths.append('Salary range provided')

        # 5. Location specificity
        if not job_posting.location or len(job_posting.location) < 3:
            gaps.append({
                'field': 'location',
                'severity': 'high',
                'message': 'Location not specified',
                'suggestion': 'Specify city/country or "Remote" explicitly'
            })
            score -= 10
        else:
            strengths.append('Location specified')

        # 6. Apply URL verification
        if not job_posting.apply_url_verified:
            gaps.append({
                'field': 'apply_url',
                'severity': 'low',
                'message': 'Apply URL not yet verified',
                'suggestion': 'Verify the URL resolves to your careers page'
            })
            score -= 5

        # 7. Custom form fields check
        if hasattr(job_posting, 'custom_form_fields') and job_posting.custom_form_fields:
            if len(job_posting.custom_form_fields) > 10:
                gaps.append({
                    'field': 'custom_form_fields',
                    'severity': 'medium',
                    'message': f'Too many custom questions ({len(job_posting.custom_form_fields)})',
                    'suggestion': 'More than 5 custom questions reduces completion rate significantly'
                })
                score -= 5
            else:
                strengths.append('Custom application questions configured')

        return {
            'score': max(0, min(100, score)),
            'gaps': sorted(gaps, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['severity'], 3)),
            'strengths': strengths,
            'total_gaps': len(gaps),
        }

    def _check_title(self, title: str) -> Dict:
        gaps = []
        strengths = []
        penalty = 0

        if not title or len(title) < 5:
            gaps.append({
                'field': 'title',
                'severity': 'high',
                'message': 'Job title is missing or too short',
                'suggestion': 'Use a clear, specific title (e.g., "Senior Backend Engineer")'
            })
            penalty += 15
        else:
            # Check for vague titles
            vague_terms = ['ninja', 'rockstar', 'guru', 'wizard', 'unicorn']
            if any(term in title.lower() for term in vague_terms):
                gaps.append({
                    'field': 'title',
                    'severity': 'low',
                    'message': 'Title uses informal language that may confuse ATS',
                    'suggestion': 'Use standard industry title for better search matching'
                })
                penalty += 5
            else:
                strengths.append('Clear job title')

        return {'gaps': gaps, 'strengths': strengths, 'penalty': penalty}

    def _check_description(self, description: str) -> Dict:
        gaps = []
        strengths = []
        penalty = 0

        if not description:
            gaps.append({
                'field': 'description',
                'severity': 'high',
                'message': 'Job description is empty',
                'suggestion': 'Add a detailed description covering responsibilities, team, and growth'
            })
            penalty += 20
            return {'gaps': gaps, 'strengths': strengths, 'penalty': penalty}

        if len(description) < self.MINIMUM_DESCRIPTION_LENGTH:
            gaps.append({
                'field': 'description',
                'severity': 'medium',
                'message': f'Description too short ({len(description)} chars, minimum recommended: {self.MINIMUM_DESCRIPTION_LENGTH})',
                'suggestion': 'Expand with team info, day-to-day responsibilities, and growth opportunities'
            })
            penalty += 10
        else:
            strengths.append('Detailed description')

        # Check for bullet points/structure
        if '\n' not in description and len(description) > 300:
            gaps.append({
                'field': 'description',
                'severity': 'low',
                'message': 'Description lacks formatting/structure',
                'suggestion': 'Use bullet points and sections for readability'
            })
            penalty += 5

        # Check for company culture mentions
        culture_terms = ['team', 'culture', 'benefit', 'growth', 'learn', 'mission', 'value']
        if any(term in description.lower() for term in culture_terms):
            strengths.append('Includes company culture information')

        return {'gaps': gaps, 'strengths': strengths, 'penalty': penalty}

    def _check_requirements(self, requirements: str) -> Dict:
        gaps = []
        strengths = []
        penalty = 0

        if not requirements:
            gaps.append({
                'field': 'requirements',
                'severity': 'high',
                'message': 'Requirements section is empty',
                'suggestion': 'List 5-8 key skills/qualifications needed'
            })
            penalty += 15
            return {'gaps': gaps, 'strengths': strengths, 'penalty': penalty}

        if len(requirements) < self.MINIMUM_REQUIREMENTS_LENGTH:
            gaps.append({
                'field': 'requirements',
                'severity': 'medium',
                'message': 'Requirements section is too brief',
                'suggestion': 'Add specific technical skills, years of experience, and education level'
            })
            penalty += 10

        # Check for measurable criteria
        has_years = bool(re.search(r'\d+\+?\s*year', requirements.lower()))
        if has_years:
            strengths.append('Includes experience level requirements')
        else:
            gaps.append({
                'field': 'requirements',
                'severity': 'low',
                'message': 'No measurable experience criteria',
                'suggestion': 'Add "X+ years of experience in..." for clarity'
            })
            penalty += 5

        return {'gaps': gaps, 'strengths': strengths, 'penalty': penalty}


ats_gap_analyzer = ATSGapAnalyzer()
