"""
Quick-Apply Service (Item 5.3)

Prepares ATS-compatible application data from a user's CareerProfile so they
can review it before manually submitting on the employer's site.

IMPORTANT: This service does NOT auto-submit applications.
Greenhouse (boards-api.greenhouse.io), Lever (api.lever.co), and Ashby
(api.ashby.com) each expose public job-board APIs that accept applications,
but submitting through those APIs requires the specific employer to have
enabled their public job board AND the correct board token -- which E-Career
does not possess for arbitrary employers.  Therefore the service:
  1. Maps CareerProfile data into an ATS-compatible payload shape.
  2. Returns the payload + the direct apply URL for the user to review.
  3. Records a JobApplication when the user clicks through to apply.
"""
import logging
from typing import Any

from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ATS provider metadata (read-only reference)
# ---------------------------------------------------------------------------
ATS_PROVIDERS = {
    'greenhouse': {
        'name': 'Greenhouse',
        'submit_endpoint': 'https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}',
        'docs_url': 'https://developers.greenhouse.io/job-board.html',
        'note': (
            'Requires employer-specific board_token. '
            'E-Career cannot submit on behalf of the user.'
        ),
    },
    'lever': {
        'name': 'Lever',
        'submit_endpoint': 'https://api.lever.co/v0/postings/{company}/apply',
        'docs_url': 'https://github.com/lever/postings-api',
        'note': (
            'Requires the employer to have a public postings site. '
            'E-Career cannot submit on behalf of the user.'
        ),
    },
    'ashby': {
        'name': 'Ashby',
        'submit_endpoint': 'https://api.ashby.com/posting-api/application',
        'docs_url': 'https://developers.ashby.com',
        'note': (
            'Requires an Ashby API key scoped to the employer. '
            'E-Career cannot submit on behalf of the user.'
        ),
    },
}


class QuickApplyService:
    """Prepare application data from a CareerProfile for manual submission."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def prepare_application(self, user, job) -> dict[str, Any]:
        """
        Map CareerProfile data to an ATS-compatible payload shape.

        Returns a dict with:
          - mapped_fields: the application data the user should review
          - ats_info: provider metadata (if known)
          - apply_url: the direct URL where the user completes submission
          - already_applied: whether a JobApplication record already exists
        """
        from apps.career.models import CareerProfile
        from apps.employers.models import JobApplication

        try:
            profile = CareerProfile.objects.get(user=user)
        except CareerProfile.DoesNotExist:
            profile = None

        mapped_fields = self._map_profile_to_payload(user, profile, job)
        ats_info = self.get_ats_provider_info(job)
        apply_url = self._resolve_apply_url(job)
        already_applied = JobApplication.objects.filter(user=user, job=job).exists()

        return {
            'mapped_fields': mapped_fields,
            'ats_info': ats_info,
            'apply_url': apply_url,
            'already_applied': already_applied,
        }

    def get_ats_submit_url(self, job) -> str | None:
        """
        Return the theoretical ATS submission endpoint for this job.

        This is informational only -- E-Career cannot actually POST here
        without the employer's board token / API key.
        """
        platform = (job.ats_platform or '').lower().strip()
        provider = ATS_PROVIDERS.get(platform)
        if not provider:
            return None
        return provider['submit_endpoint']

    def get_ats_provider_info(self, job) -> dict[str, Any] | None:
        """Return metadata about the ATS provider, or None if unknown."""
        platform = (job.ats_platform or '').lower().strip()
        provider = ATS_PROVIDERS.get(platform)
        if not provider:
            return None
        return {
            'platform': platform,
            'name': provider['name'],
            'submit_endpoint_template': provider['submit_endpoint'],
            'docs_url': provider['docs_url'],
            'note': provider['note'],
            'can_auto_submit': False,  # Always False -- see module docstring
        }

    def record_application(self, user, job, method: str = 'quick_apply') -> dict[str, Any]:
        """
        Create a JobApplication record when the user clicks through to apply.

        If the user has already applied to this job, returns the existing
        record without creating a duplicate.
        """
        from apps.employers.models import JobApplication

        application, created = JobApplication.objects.get_or_create(
            user=user,
            job=job,
            defaults={
                'status': 'applied',
                'custom_form_responses': {'method': method},
            },
        )

        return {
            'application_id': application.id,
            'created': created,
            'applied_at': application.applied_at.isoformat(),
            'status': application.status,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_profile_to_payload(self, user, profile, job) -> dict[str, Any]:
        """
        Build a flat dict of fields that most ATS public APIs accept.

        Greenhouse, Lever, and Ashby share a common shape:
          first_name, last_name, email, phone, resume/cv, linkedin,
          portfolio/website, current_company, current_title, cover_letter.
        """
        payload: dict[str, Any] = {
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'email': user.email,
            'phone': '',
            'resume_url': None,
            'linkedin_url': '',
            'portfolio_url': '',
            'current_company': '',
            'current_title': '',
            'skills': [],
            'education': [],
            'experience_years': 0,
            'cover_letter': '',
        }

        if profile is None:
            return payload

        # Contact / identity
        payload['phone'] = (
            profile.cv_parsed_data.get('phone', '') if profile.cv_parsed_data else ''
        )
        payload['resume_url'] = profile.cv_file_url
        payload['linkedin_url'] = (
            profile.linkedin_data.get('url', '') if profile.linkedin_data else ''
        )
        payload['portfolio_url'] = profile.portfolio_url or ''

        # Professional info
        payload['current_company'] = profile.current_company or ''
        payload['current_title'] = profile.current_role or ''
        payload['experience_years'] = profile.experience_years or 0

        # Skills
        payload['skills'] = list(profile.skills or [])

        # Education
        payload['education'] = list(profile.education or [])

        # Languages
        payload['languages'] = list(profile.languages or [])

        # Certifications
        payload['certifications'] = list(profile.certifications or [])

        return payload

    def _resolve_apply_url(self, job) -> str:
        """Return the best URL for the user to apply at."""
        if job.direct_apply_url:
            return job.direct_apply_url
        return job.source_url or ''


quick_apply_service = QuickApplyService()
