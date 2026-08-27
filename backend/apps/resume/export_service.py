"""
Resume Export Service - generates PDF/HTML/JSON from resume data.

Uses Django templates for HTML rendering and xhtml2pdf for PDF conversion.
"""
import io
import json
import logging
import os
from typing import Optional

from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


class ResumeExportService:
    TEMPLATES = {
        'modern': 'resume/export/modern.html',
        'professional': 'resume/export/professional.html',
        'creative': 'resume/export/creative.html',
        'minimalist': 'resume/export/minimalist.html',
    }

    def export_pdf(self, resume) -> Optional[bytes]:
        html = self._render_html(resume)
        try:
            from xhtml2pdf import pisa
            buffer = io.BytesIO()
            pisa_status = pisa.CreatePDF(io.StringIO(html), dest=buffer)
            if pisa_status.err:
                logger.error("PDF generation failed: %d errors", pisa_status.err)
                return None
            return buffer.getvalue()
        except ImportError:
            logger.warning("xhtml2pdf not installed, falling back to HTML export")
            return html.encode('utf-8')

    def export_html(self, resume) -> str:
        return self._render_html(resume)

    def export_json(self, resume) -> str:
        return json.dumps({
            'personal_info': resume.personal_info,
            'summary': resume.summary,
            'experience': resume.experience,
            'education': resume.education,
            'skills': resume.skills,
            'projects': resume.projects,
            'certifications': resume.certifications,
            'languages': resume.languages,
            'interests': resume.interests,
        }, indent=2)

    def _render_html(self, resume) -> str:
        template_category = 'modern'
        if resume.template:
            template_category = resume.template.category

        template_name = self.TEMPLATES.get(template_category, self.TEMPLATES['modern'])

        try:
            return render_to_string(template_name, {'resume': resume})
        except Exception:
            return render_to_string('resume/export/modern.html', {'resume': resume})


resume_export_service = ResumeExportService()
