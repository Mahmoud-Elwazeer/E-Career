"""
GitHub Integration Service for E-Career.

Handles GitHub OAuth flow, repository analysis, and contribution tracking.
"""

import structlog
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

logger = structlog.get_logger()


class GitHubService:
    """Service for interacting with GitHub API."""
    
    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_GRAPHQL_BASE = "https://api.github.com/graphql"
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.session = requests.Session()
        if access_token:
            self.session.headers.update({
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json',
            })
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user's information."""
        response = self.session.get(f"{self.GITHUB_API_BASE}/user")
        response.raise_for_status()
        return response.json()
    
    def get_user_repos(self, username: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get all repositories for a user."""
        repos = []
        page = 1
        
        while True:
            response = self.session.get(
                f"{self.GITHUB_API_BASE}/users/{username}/repos",
                params={'per_page': per_page, 'page': page, 'type': 'owner'}
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
            
            repos.extend(data)
            page += 1
        
        return repos
    
    def get_repo_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed information about a repository."""
        response = self.session.get(
            f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}"
        )
        response.raise_for_status()
        return response.json()
    
    def get_repo_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get language breakdown for a repository."""
        response = self.session.get(
            f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/languages"
        )
        response.raise_for_status()
        return response.json()
    
    def get_contributions(self, username: str, since: datetime = None, until: datetime = None) -> Dict[str, Any]:
        """Get contribution data for a user."""
        if since is None:
            since = datetime.now() - timedelta(days=365)
        if until is None:
            until = datetime.now()
        
        # Get contribution graph data
        response = self.session.get(
            f"{self.GITHUB_API_BASE}/users/{username}/contributions",
            params={'from': since.isoformat(), 'until': until.isoformat()}
        )
        response.raise_for_status()
        
        # Parse contribution data
        contributions = response.json()
        
        return {
            'total_contributions': sum(c.get('count', 0) for c in contributions),
            'contribution_days': len([c for c in contributions if c.get('count', 0) > 0]),
            'contribution_data': contributions,
        }
    
    def get_stars(self, username: str) -> int:
        """Get total stars across user's repositories."""
        repos = self.get_user_repos(username)
        return sum(repo.get('stargazers_count', 0) for repo in repos)
    
    def analyze_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Analyze a single repository."""
        repo_info = self.get_repo_details(owner, repo)
        languages = self.get_repo_languages(owner, repo)
        
        # Calculate quality metrics
        quality_score = self._calculate_repo_quality(repo_info, languages)
        
        return {
            'name': repo_info.get('full_name'),
            'description': repo_info.get('description'),
            'stars': repo_info.get('stargazers_count', 0),
            'forks': repo_info.get('forks_count', 0),
            'open_issues': repo_info.get('open_issues_count', 0),
            'languages': list(languages.keys()),
            'language_breakdown': languages,
            'is_private': repo_info.get('private', False),
            'is_fork': repo_info.get('fork', False),
            'created_at': repo_info.get('created_at'),
            'updated_at': repo_info.get('updated_at'),
            'quality_score': quality_score,
        }
    
    def _calculate_repo_quality(self, repo_info: Dict, languages: Dict) -> float:
        """Calculate quality score for a repository."""
        score = 0.0
        
        # Stars (30%)
        stars = repo_info.get('stargazers_count', 0)
        if stars >= 1000:
            score += 0.3
        elif stars >= 100:
            score += 0.2
        elif stars >= 10:
            score += 0.1
        
        # Forks (20%)
        forks = repo_info.get('forks_count', 0)
        if forks >= 50:
            score += 0.2
        elif forks >= 10:
            score += 0.1
        
        # Activity (20%)
        updated_at = repo_info.get('updated_at')
        if updated_at:
            days_since_update = (datetime.now() - datetime.fromisoformat(updated_at.replace('Z', '+00:00'))).days
            if days_since_update < 30:
                score += 0.2
            elif days_since_update < 90:
                score += 0.15
            elif days_since_update < 180:
                score += 0.1
        
        # Documentation (15%)
        has_readme = repo_info.get('has_readme', False)
        if has_readme:
            score += 0.15
        
        # License (15%)
        has_license = repo_info.get('has_license', False)
        if has_license:
            score += 0.15
        
        return round(min(1.0, score), 3)
    
    def analyze_user_profile(self, username: str) -> Dict[str, Any]:
        """Analyze a user's GitHub profile."""
        user_info = self.get_user_info()
        repos = self.get_user_repos(username)
        
        # Aggregate repository data
        total_stars = 0
        total_forks = 0
        all_languages = {}
        project_count = 0
        active_projects = 0
        
        for repo in repos:
            if repo.get('fork'):
                continue
            
            project_count += 1
            total_stars += repo.get('stargazers_count', 0)
            total_forks += repo.get('forks_count', 0)
            
            # Update language counts
            languages = self.get_repo_languages(username, repo.get('name', ''))
            for lang, bytes_count in languages.items():
                all_languages[lang] = all_languages.get(lang, 0) + bytes_count
            
            # Check if active (updated in last 90 days)
            updated_at = repo.get('updated_at')
            if updated_at:
                days_since_update = (datetime.now() - datetime.fromisoformat(updated_at.replace('Z', '+00:00'))).days
                if days_since_update < 90:
                    active_projects += 1
        
        # Calculate technology diversity
        total_bytes = sum(all_languages.values())
        tech_diversity = len(all_languages) / max(project_count, 1)
        
        # Calculate activity score
        activity_score = active_projects / max(project_count, 1)
        
        return {
            'username': username,
            'name': user_info.get('name'),
            'company': user_info.get('company'),
            'location': user_info.get('location'),
            'email': user_info.get('email'),
            'avatar_url': user_info.get('avatar_url'),
            'profile_url': user_info.get('html_url'),
            'total_stars': total_stars,
            'total_forks': total_forks,
            'project_count': project_count,
            'active_projects': active_projects,
            'tech_stack': list(all_languages.keys()),
            'tech_diversity': round(tech_diversity, 3),
            'activity_score': round(activity_score, 3),
            'last_active': max(
                (repo.get('updated_at') for repo in repos if repo.get('updated_at')),
                default=None
            ),
        }


def analyze_portfolio_url(url: str) -> Dict[str, Any]:
    """
    Analyze a portfolio URL using Bedrock Haiku.
    
    This is a placeholder that would call the Bedrock service in production.
    """
    # Extract domain
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    
    # In production, this would call Bedrock Haiku to:
    # 1. Scrape the portfolio URL
    # 2. Analyze technologies used
    # 3. Evaluate project quality
    # 4. Generate observations
    
    return {
        'url': url,
        'domain': domain,
        'technologies': ['React', 'Node.js', 'TypeScript'],  # Placeholder
        'projects': [
            {
                'name': 'Project 1',
                'description': 'Sample project',
                'technologies': ['React', 'Node.js'],
                'stars': 100,
            }
        ],
        'quality_score': 0.8,
        'completeness_score': 0.7,
        'tech_stack': {
            'frontend': ['React', 'Tailwind'],
            'backend': ['Node.js', 'Express'],
            'database': ['PostgreSQL'],
        },
        'project_count': 3,
        'star_count': 150,
        'contribution_count': 50,
        'observations': {
            'strengths': ['Clean code structure', 'Good documentation'],
            'growth_areas': ['Add more projects', 'Improve mobile responsiveness'],
        },
    }