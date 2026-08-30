"""
Insider Connections Service (Item 5.5)

Finds E-Career users who work at a target company (first-party, consent-gated)
and optionally surfaces public GitHub contributors at the company's org.
"""
import logging
from typing import Any

from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class ConnectionsService:
    def find_connections(self, company_id: int, requesting_user=None) -> dict[str, Any]:
        from apps.jobs.models import Company
        from apps.career.models import CareerProfile

        company = Company.objects.get(id=company_id)

        ecareer_users = self._find_ecareer_connections(company, requesting_user)
        github_contributors = self._find_github_contributors(company)

        return {
            'company': {
                'id': company.id,
                'name': company.name,
                'slug': company.slug,
            },
            'ecareer_connections': ecareer_users,
            'github_contributors': github_contributors,
            'total_connections': len(ecareer_users) + len(github_contributors),
        }

    def _find_ecareer_connections(self, company, requesting_user=None) -> list[dict]:
        from apps.career.models import CareerProfile

        profiles = CareerProfile.objects.filter(
            is_discoverable=True,
        ).select_related('user')

        if requesting_user:
            profiles = profiles.exclude(user=requesting_user)

        connections = []
        company_name_lower = company.name.lower()
        company_domain = (company.domain or '').lower()

        for profile in profiles:
            match_reason = None

            if profile.current_company and company_name_lower in profile.current_company.lower():
                match_reason = 'current_employee'

            if not match_reason and profile.cv_parsed_data:
                experience = profile.cv_parsed_data.get('experience', [])
                for exp in experience:
                    exp_company = ''
                    if isinstance(exp, dict):
                        exp_company = exp.get('company', '')
                    elif isinstance(exp, str):
                        exp_company = exp
                    if exp_company and company_name_lower in exp_company.lower():
                        match_reason = 'former_employee'
                        break

            if match_reason:
                connections.append({
                    'user_id': profile.user.id,
                    'name': profile.user.get_full_name() or profile.user.email.split('@')[0],
                    'current_role': profile.current_role or '',
                    'current_company': profile.current_company or '',
                    'connection_type': match_reason,
                    'experience_years': profile.experience_years or 0,
                })

        return connections[:20]

    def _find_github_contributors(self, company) -> list[dict]:
        github_org = getattr(company, 'github_org', None) or ''
        if not github_org:
            return []

        try:
            import urllib.request
            import json

            url = f'https://api.github.com/orgs/{github_org}/members?per_page=10'
            req = urllib.request.Request(url, headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'E-Career-Platform',
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                members = json.loads(resp.read())

            return [
                {
                    'username': m.get('login', ''),
                    'profile_url': m.get('html_url', ''),
                    'avatar_url': m.get('avatar_url', ''),
                    'source': 'github_public',
                }
                for m in members[:10]
            ]
        except Exception as e:
            logger.info("GitHub org lookup failed for %s: %s", github_org, e)
            return []


connections_service = ConnectionsService()
