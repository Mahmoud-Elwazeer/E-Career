"""
Skill Gap Analysis Service

Analyzes the gap between a user's current skills and the skills required
for their target roles using the skill knowledge graph.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class SkillGapAnalyzer:
    """
    Analyzes skill gaps between user's current skills and target role requirements.
    
    Uses the skill knowledge graph to:
    - Identify missing skills for target roles
    - Suggest related skills to learn
    - Calculate gap severity
    - Generate learning recommendations
    """
    
    def __init__(self, user):
        """
        Initialize analyzer for a specific user.
        
        Args:
            user: Django User instance
        """
        self.user = user
        self._user_skills = None
        self._target_roles = None
        self._skill_graph = None
    
    @property
    def user_skills(self) -> List[str]:
        """Get user's verified skills."""
        if self._user_skills is None:
            from apps.career.models import CareerUserSkill
            self._user_skills = list(
                CareerUserSkill.objects.filter(
                    user=self.user,
                    verified=True
                ).select_related('skill').values_list('skill__name', flat=True)
            )
        return self._user_skills
    
    @property
    def target_roles(self) -> List[Dict[str, str]]:
        """Get user's target roles."""
        if self._target_roles is None:
            self._target_roles = self.user.career_profile.target_roles or []
        return self._target_roles
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete skill gap analysis.
        
        Returns:
            Dictionary with:
            - overall_gap_score: Average gap score across all target roles
            - gaps_by_role: Detailed gaps for each target role
            - missing_skills: List of all missing skills
            - recommendations: Learning recommendations
            - gap_severity: Overall severity (low/medium/high/critical)
        """
        gaps_by_role = []
        all_missing_skills = set()
        total_gap_score = 0
        
        for target_role in self.target_roles:
            role_name = target_role.get('role', '')
            if not role_name:
                continue
            
            role_gaps = self._analyze_role_gaps(role_name)
            gaps_by_role.append(role_gaps)
            
            all_missing_skills.update(role_gaps['missing_skills'])
            total_gap_score += role_gaps['gap_score']
        
        # Calculate overall metrics
        num_roles = len(self.target_roles) if self.target_roles else 1
        overall_gap_score = total_gap_score / num_roles
        
        # Determine severity
        if overall_gap_score < 20:
            severity = 'low'
        elif overall_gap_score < 40:
            severity = 'medium'
        elif overall_gap_score < 60:
            severity = 'high'
        else:
            severity = 'critical'
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_missing_skills)
        
        return {
            'overall_gap_score': round(overall_gap_score, 1),
            'gap_severity': severity,
            'gaps_by_role': gaps_by_role,
            'missing_skills': list(all_missing_skills),
            'recommendations': recommendations,
            'analysis_date': self._get_analysis_date(),
        }
    
    def _analyze_role_gaps(self, role_name: str) -> Dict[str, Any]:
        """Analyze skill gaps for a specific role."""
        # Get required skills for this role
        required_skills = self._get_required_skills(role_name)
        
        # Find missing skills
        missing_skills = [
            skill for skill in required_skills 
            if skill.lower() not in [s.lower() for s in self.user_skills]
        ]
        
        # Calculate gap score (0-100)
        if not required_skills:
            gap_score = 0
        else:
            gap_score = (len(missing_skills) / len(required_skills)) * 100
        
        # Get related skills to learn
        related_skills = self._get_related_skills(missing_skills)
        
        return {
            'role': role_name,
            'required_skills_count': len(required_skills),
            'missing_skills_count': len(missing_skills),
            'gap_score': round(gap_score, 1),
            'missing_skills': missing_skills,
            'related_skills': related_skills,
        }
    
    def _get_required_skills(self, role_name: str) -> List[str]:
        """Get required skills for a role from O*NET data."""
        from apps.skills.models import Occupation, OccupationSkill
        
        # Try to find occupation by name
        try:
            occupation = Occupation.objects.filter(
                name__icontains=role_name
            ).first()
            
            if occupation:
                # Get skills for this occupation
                occupation_skills = OccupationSkill.objects.filter(
                    occupation=occupation
                ).select_related('skill')[:20]
                
                return [os.skill.name for os in occupation_skills]
        except Exception as e:
            logger.warning(f"Failed to get skills for role {role_name}: {e}")
        
        # Fallback: return common skills for common roles
        common_role_skills = {
            'software engineer': [
                'Python', 'JavaScript', 'SQL', 'Git', 'Docker',
                'REST APIs', 'Microservices', 'Agile', 'System Design',
                'Data Structures', 'Algorithms', 'Cloud Computing'
            ],
            'data scientist': [
                'Python', 'R', 'SQL', 'Machine Learning', 'Data Analysis',
                'Statistical Analysis', 'Data Visualization', 'Big Data',
                'Deep Learning', 'Natural Language Processing'
            ],
            'product manager': [
                'Product Strategy', 'Agile', 'User Research', 'Roadmapping',
                'Prioritization', 'Stakeholder Management', 'Data Analysis'
            ],
            'ux designer': [
                'Figma', 'User Research', 'Wireframing', 'Prototyping',
                'User Testing', 'Interaction Design', 'Visual Design'
            ],
        }
        
        return common_role_skills.get(role_name.lower(), [])
    
    def _get_related_skills(self, missing_skills: List[str]) -> List[Dict[str, Any]]:
        """Get related skills to learn for each missing skill."""
        from apps.skills.models import Skill
        
        related_skills = []
        
        for skill_name in missing_skills[:10]:  # Top 10 missing skills
            try:
                skill = Skill.objects.filter(name__iexact=skill_name).first()
                if skill:
                    # Get related skills from graph
                    related = self._get_graph_related_skills(skill)
                    if related:
                        related_skills.append({
                            'missing_skill': skill_name,
                            'related_skills': related,
                        })
            except Exception as e:
                logger.warning(f"Failed to get related skills for {skill_name}: {e}")
        
        return related_skills
    
    def _get_graph_related_skills(self, skill) -> List[str]:
        """Get related skills from the knowledge graph."""
        from apps.skills.graph import SkillGraph
        
        try:
            graph = SkillGraph()
            related = graph.find_related_skills(str(skill.id), depth=2)
            
            if related:
                return [r.get('skill_name', '') for r in related[:5]]
        except Exception as e:
            logger.warning(f"Failed to query skill graph: {e}")
        
        return []
    
    def _generate_recommendations(self, missing_skills: List[str]) -> List[Dict[str, str]]:
        """Generate learning recommendations based on missing skills."""
        recommendations = []
        
        # Group skills by category
        skill_categories = defaultdict(list)
        for skill in missing_skills:
            category = self._categorize_skill(skill)
            skill_categories[category].append(skill)
        
        # Generate recommendations for each category
        for category, skills in skill_categories.items():
            if category == 'technical':
                recommendations.append({
                    'category': 'technical',
                    'title': 'Technical Skills Development',
                    'description': f'Focus on learning {", ".join(skills[:3])} to improve your technical profile.',
                    'actions': [
                        'Take online courses on platforms like Coursera or Udemy',
                        'Practice on coding platforms like LeetCode or HackerRank',
                        'Contribute to open source projects',
                    ],
                })
            elif category == 'soft':
                recommendations.append({
                    'category': 'soft',
                    'title': 'Soft Skills Enhancement',
                    'description': f'Improve your {", ".join(skills[:3])} skills.',
                    'actions': [
                        'Join public speaking groups like Toastmasters',
                        'Seek mentorship from experienced professionals',
                        'Read books on communication and leadership',
                    ],
                })
            elif category == 'tool':
                recommendations.append({
                    'category': 'tool',
                    'title': 'Tool Proficiency',
                    'description': f'Learn to use {", ".join(skills[:3])} effectively.',
                    'actions': [
                        'Watch tutorial videos on YouTube',
                        'Complete official documentation tutorials',
                        'Practice with sample projects',
                    ],
                })
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill into technical, soft, or tool."""
        technical_keywords = [
            'python', 'javascript', 'java', 'c++', 'sql', 'html', 'css',
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'aws',
            'docker', 'kubernetes', 'linux', 'git', 'api', 'database',
            'machine learning', 'data science', 'algorithm', 'network',
        ]
        
        tool_keywords = [
            'figma', 'photoshop', ' Premiere', 'after effects', 'excel',
            'word', 'powerpoint', 'slack', 'jira', 'trello', 'notion',
            'salesforce', 'hubspot', 'zoom', 'teams', 'google analytics',
        ]
        
        skill_lower = skill.lower()
        
        if any(kw in skill_lower for kw in technical_keywords):
            return 'technical'
        elif any(kw in skill_lower for kw in tool_keywords):
            return 'tool'
        else:
            return 'soft'
    
    def _get_analysis_date(self) -> str:
        """Get current timestamp."""
        from django.utils import timezone
        return timezone.now().isoformat()


def analyze_skill_gaps(user) -> Dict[str, Any]:
    """
    Convenience function to analyze skill gaps.
    
    Args:
        user: Django User instance
        
    Returns:
        Skill gap analysis dictionary
    """
    analyzer = SkillGapAnalyzer(user)
    return analyzer.analyze()