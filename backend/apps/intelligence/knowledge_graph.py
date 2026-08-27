"""
Knowledge Graph Service.

Builds and queries a knowledge graph of skills, roles, companies, and
career paths using the existing PostgreSQL + skills taxonomy.

The graph connects:
- Skills → Roles (which skills are needed for which roles)
- Skills → Skills (prerequisites, related, complementary)
- Roles → Career Paths (progression routes)
- Companies → Skills (what companies look for)
- Users → Skills (what users have)
"""
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from django.db.models import Count, Q, F
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 60 * 60 * 6


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    id: str
    label: str
    type: str  # skill, role, company, career_path
    properties: Dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    """An edge connecting two nodes."""
    source: str
    target: str
    relationship: str
    weight: float = 1.0


@dataclass
class GraphQueryResult:
    """Result of a graph query."""
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    paths: List[List[str]] = field(default_factory=list)


class KnowledgeGraphService:
    """
    Queries the implicit knowledge graph in the platform data.

    Instead of a separate graph DB, we derive graph relationships from:
    - skills_skillrelationship table
    - jobs_jobskill table
    - career_careerpath table
    - job title patterns
    """

    def get_skill_neighborhood(self, skill_name: str, depth: int = 2) -> GraphQueryResult:
        """
        Get all skills related to a given skill within N hops.
        """
        cache_key = f"kg:skill_neighborhood:{skill_name}:{depth}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        from apps.skills.models import Skill, SkillRelationship

        try:
            skill = Skill.objects.get(name__iexact=skill_name)
        except Skill.DoesNotExist:
            return GraphQueryResult()

        nodes = [GraphNode(id=str(skill.id), label=skill.name, type="skill")]
        edges = []
        visited: Set[str] = {str(skill.id)}

        current_ids = [skill.id]

        for _ in range(depth):
            relationships = SkillRelationship.objects.filter(
                Q(from_skill_id__in=current_ids) | Q(to_skill_id__in=current_ids)
            ).select_related('from_skill', 'to_skill')

            next_ids = []
            for rel in relationships:
                if str(rel.to_skill_id) not in visited:
                    nodes.append(GraphNode(
                        id=str(rel.to_skill_id),
                        label=rel.to_skill.name,
                        type="skill",
                    ))
                    visited.add(str(rel.to_skill_id))
                    next_ids.append(rel.to_skill_id)

                if str(rel.from_skill_id) not in visited:
                    nodes.append(GraphNode(
                        id=str(rel.from_skill_id),
                        label=rel.from_skill.name,
                        type="skill",
                    ))
                    visited.add(str(rel.from_skill_id))
                    next_ids.append(rel.from_skill_id)

                edges.append(GraphEdge(
                    source=str(rel.from_skill_id),
                    target=str(rel.to_skill_id),
                    relationship=rel.relationship_type,
                    weight=rel.weight if hasattr(rel, 'weight') else 1.0,
                ))

            current_ids = next_ids

        result = GraphQueryResult(nodes=nodes, edges=edges)
        cache.set(cache_key, result, CACHE_TIMEOUT)
        return result

    def get_role_skills_graph(self, role_title: str) -> GraphQueryResult:
        """
        Get all skills associated with a role title, weighted by frequency.
        """
        from apps.jobs.models import Job
        from apps.skills.models import JobSkill

        jobs = Job.objects.filter(
            title__icontains=role_title, is_expired=False
        )

        skill_counts = (
            JobSkill.objects.filter(job__in=jobs)
            .values('skill__id', 'skill__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:30]
        )

        role_node = GraphNode(
            id=f"role:{role_title}",
            label=role_title,
            type="role",
            properties={"job_count": jobs.count()},
        )

        nodes = [role_node]
        edges = []

        for item in skill_counts:
            skill_node = GraphNode(
                id=str(item['skill__id']),
                label=item['skill__name'],
                type="skill",
                properties={"frequency": item['count']},
            )
            nodes.append(skill_node)
            edges.append(GraphEdge(
                source=role_node.id,
                target=skill_node.id,
                relationship="requires",
                weight=item['count'],
            ))

        return GraphQueryResult(nodes=nodes, edges=edges)

    def get_career_path_graph(self, current_role: str) -> GraphQueryResult:
        """
        Get possible career progression paths from a current role.
        """
        from apps.career.models import CareerPath

        paths = CareerPath.objects.filter(
            Q(from_role__icontains=current_role) | Q(title__icontains=current_role)
        )

        nodes = [GraphNode(
            id=f"role:{current_role}",
            label=current_role,
            type="role",
        )]
        edges = []
        path_lists = []

        for path in paths:
            target_role = path.to_role if hasattr(path, 'to_role') else path.title
            target_node = GraphNode(
                id=f"role:{target_role}",
                label=target_role,
                type="role",
            )
            nodes.append(target_node)
            edges.append(GraphEdge(
                source=f"role:{current_role}",
                target=target_node.id,
                relationship="progresses_to",
            ))
            path_lists.append([current_role, target_role])

        return GraphQueryResult(nodes=nodes, edges=edges, paths=path_lists)

    def get_company_skill_demand(self, company_slug: str) -> GraphQueryResult:
        """Get skills most demanded by a specific company."""
        from apps.jobs.models import Job, Company
        from apps.skills.models import JobSkill

        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            return GraphQueryResult()

        skill_counts = (
            JobSkill.objects.filter(job__company=company, job__is_expired=False)
            .values('skill__id', 'skill__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:20]
        )

        company_node = GraphNode(
            id=f"company:{company_slug}",
            label=company.name,
            type="company",
        )

        nodes = [company_node]
        edges = []

        for item in skill_counts:
            skill_node = GraphNode(
                id=str(item['skill__id']),
                label=item['skill__name'],
                type="skill",
                properties={"demand_count": item['count']},
            )
            nodes.append(skill_node)
            edges.append(GraphEdge(
                source=company_node.id,
                target=skill_node.id,
                relationship="demands",
                weight=item['count'],
            ))

        return GraphQueryResult(nodes=nodes, edges=edges)

    def get_user_skill_gaps(self, user_id: int, target_role: str) -> Dict:
        """
        Compute skill gaps between user's skills and target role requirements.
        """
        from apps.career.models import CareerProfile
        from apps.skills.models import JobSkill
        from apps.jobs.models import Job

        try:
            profile = CareerProfile.objects.get(user_id=user_id)
            user_skills = set(
                profile.skills.values_list('name', flat=True)
            ) if hasattr(profile, 'skills') else set()
        except CareerProfile.DoesNotExist:
            user_skills = set()

        role_jobs = Job.objects.filter(title__icontains=target_role, is_expired=False)
        required_skills = set(
            JobSkill.objects.filter(job__in=role_jobs)
            .values_list('skill__name', flat=True)
            .annotate(count=Count('id'))
            .order_by('-count')[:20]
        )

        matched = user_skills & required_skills
        gaps = required_skills - user_skills
        extra = user_skills - required_skills

        return {
            "target_role": target_role,
            "matched_skills": sorted(matched),
            "skill_gaps": sorted(gaps),
            "extra_skills": sorted(extra),
            "match_percentage": round(len(matched) / max(len(required_skills), 1) * 100, 1),
        }


_kg_service: Optional[KnowledgeGraphService] = None


def get_knowledge_graph_service() -> KnowledgeGraphService:
    global _kg_service
    if _kg_service is None:
        _kg_service = KnowledgeGraphService()
    return _kg_service
