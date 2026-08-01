"""
Feature Flags Seed Data for E-Career.

This module contains the initial feature flags to be seeded into the database.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any


def get_feature_flags() -> List[Dict[str, Any]]:
    """Get the initial feature flags to seed."""
    return [
        {
            'key': 'ai_interview_voice',
            'label': 'AI Interview Voice Mode',
            'description': 'Enable voice-based interviews with AI',
            'is_enabled': False,
            'enabled_for_users': [],
            'enabled_percentage': 0,
            'regions': [],
            'employer_only': False,
            'expires_at': None,
            'category': 'interview',
            'metadata': {
                'version': '1.0.0',
                'notes': 'Voice mode for interviews - in development',
            },
        },
        {
            'key': 'search_semantic',
            'label': 'Semantic Search',
            'description': 'Enable semantic search for job listings',
            'is_enabled': True,
            'enabled_for_users': [],
            'enabled_percentage': 100,
            'regions': [],
            'employer_only': False,
            'expires_at': None,
            'category': 'search',
            'metadata': {
                'version': '1.0.0',
                'notes': 'Semantic search enabled for all users',
            },
        },
        {
            'key': 'ai_career_brain',
            'label': 'AI Career Brain',
            'description': 'Enable AI-powered career brain features',
            'is_enabled': True,
            'enabled_for_users': [],
            'enabled_percentage': 100,
            'regions': [],
            'employer_only': False,
            'expires_at': None,
            'category': 'career',
            'metadata': {
                'version': '1.0.0',
                'notes': 'Career brain enabled for all users',
            },
        },
        {
            'key': 'employer_ai_ranking',
            'label': 'Employer AI Ranking',
            'description': 'Enable AI-powered candidate ranking for employers',
            'is_enabled': True,
            'enabled_for_users': [],
            'enabled_percentage': 100,
            'regions': [],
            'employer_only': True,
            'expires_at': None,
            'category': 'employer',
            'metadata': {
                'version': '1.0.0',
                'notes': 'AI ranking enabled for all employers',
            },
        },
        {
            'key': 'github_integration',
            'label': 'GitHub Integration',
            'description': 'Enable GitHub portfolio analysis',
            'is_enabled': True,
            'enabled_for_users': [],
            'enabled_percentage': 100,
            'regions': [],
            'employer_only': False,
            'expires_at': None,
            'category': 'portfolio',
            'metadata': {
                'version': '1.0.0',
                'notes': 'GitHub integration enabled for all users',
            },
        },
        {
            'key': 'notification_center',
            'label': 'Notification Center',
            'description': 'Enable the notification center feature',
            'is_enabled': True,
            'enabled_for_users': [],
            'enabled_percentage': 100,
            'regions': [],
            'employer_only': False,
            'expires_at': None,
            'category': 'notifications',
            'metadata': {
                'version': '1.0.0',
                'notes': 'Notification center enabled for all users',
            },
        },
        {
            'key': 'rule_engine',
            'label': 'Rule Engine',
            'description': 'Enable the rule engine for automated actions',
            'is_enabled': True,
            'enabled_for_users': [],
            'enabled_percentage': 100,
            'regions': [],
            'employer_only': False,
            'expires_at': None,
            'category': 'system',
            'metadata': {
                'version': '1.0.0',
                'notes': 'Rule engine enabled for all users',
            },
        },
        {
            'key': 'portfolio_analysis',
            'label': 'Portfolio Analysis',
            'description': 'Enable portfolio URL analysis',
            'is_enabled': True,
            'enabled_for_users': [],
            'enabled_percentage': 100,
            'regions': [],
            'employer_only': False,
            'expires_at': None,
            'category': 'portfolio',
            'metadata': {
                'version': '1.0.0',
                'notes': 'Portfolio analysis enabled for all users',
            },
        },
    ]


def get_rules() -> List[Dict[str, Any]]:
    """Get the initial rules to seed."""
    return [
        {
            'name': 'Flag Low-Quality Jobs',
            'description': 'Flag jobs with trust_score below 0.4 for admin review',
            'category': 'job',
            'conditions': {
                'operator': 'ALL',
                'conditions': [
                    {'field': 'job.trust_score', 'operator': 'lt', 'value': 0.4},
                    {'field': 'job.is_flagged', 'operator': 'eq', 'value': False},
                ],
            },
            'action_type': 'flag',
            'action_params': {
                'reason': 'Low trust score indicates potential scam or low-quality posting',
                'target': 'job',
            },
            'is_active': True,
            'priority': 100,
        },
        {
            'name': 'Expire Stale Jobs',
            'description': 'Auto-expire jobs that are 30+ days old with 3+ failures',
            'category': 'job',
            'conditions': {
                'operator': 'ALL',
                'conditions': [
                    {'field': 'job.age_days', 'operator': 'gte', 'value': 30},
                    {'field': 'job.failure_count', 'operator': 'gte', 'value': 3},
                    {'field': 'job.is_expired', 'operator': 'eq', 'value': False},
                ],
            },
            'action_type': 'alert',
            'action_params': {
                'message': 'Job has expired due to age and repeated failures',
                'target': 'job',
            },
            'is_active': True,
            'priority': 90,
        },
        {
            'name': 'Send Job Alert',
            'description': 'Send alert when job match meets minimum score threshold',
            'category': 'notification',
            'conditions': {
                'operator': 'ALL',
                'conditions': [
                    {'field': 'match_score', 'operator': 'gte', 'value': 0.7},
                    {'field': 'user.alert_frequency', 'operator': 'in', 'value': ['instant', 'daily']},
                ],
            },
            'action_type': 'alert',
            'action_params': {
                'message': 'New job match found!',
                'target': 'user',
            },
            'is_active': True,
            'priority': 80,
        },
        {
            'name': 'Recommend to Employer',
            'description': 'Recommend candidate to employer when career_score >= 85 and skill_match >= 90',
            'category': 'employer',
            'conditions': {
                'operator': 'ALL',
                'conditions': [
                    {'field': 'candidate.career_score', 'operator': 'gte', 'value': 0.85},
                    {'field': 'candidate.skill_match', 'operator': 'gte', 'value': 0.9},
                ],
            },
            'action_type': 'recommend_employer',
            'action_params': {
                'reason': 'Excellent match - highly recommended',
            },
            'is_active': True,
            'priority': 70,
        },
        {
            'name': 'Request CV Update',
            'description': 'Request CV update when CV is older than 180 days',
            'category': 'user',
            'conditions': {
                'operator': 'ALL',
                'conditions': [
                    {'field': 'cv_age_days', 'operator': 'gte', 'value': 180},
                ],
            },
            'action_type': 'request_cv_update',
            'action_params': {
                'message': 'Your CV is outdated. Please update it to improve your match quality.',
                'days_since_last_update': 180,
            },
            'is_active': True,
            'priority': 60,
        },
        {
            'name': 'Celebrate New Certification',
            'description': 'Celebrate when user earns a new certification',
            'category': 'celebration',
            'conditions': {
                'operator': 'ALL',
                'conditions': [
                    {'field': 'event', 'operator': 'eq', 'value': 'certification_earned'},
                ],
            },
            'action_type': 'celebrate',
            'action_params': {
                'message': 'Congratulations on earning your new certification! 🎓',
                'emoji': '🎓',
            },
            'is_active': True,
            'priority': 50,
        },
        {
            'name': 'Celebrate Score Improvement',
            'description': 'Celebrate when career score improves by 10+ points',
            'category': 'celebration',
            'conditions': {
                'operator': 'ALL',
                'conditions': [
                    {'field': 'score_improvement', 'operator': 'gte', 'value': 0.1},
                ],
            },
            'action_type': 'celebrate',
            'action_params': {
                'message': 'Great job! Your career score improved by {improvement}%! 🚀',
                'emoji': '🚀',
            },
            'is_active': True,
            'priority': 40,
        },
    ]