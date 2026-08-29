"""
Graph Query Utilities using recursive CTEs.

Queries the skill knowledge graph using standard PostgreSQL recursive CTEs
on the skills_relationship adjacency table. No external graph extensions required.
"""

import logging
from typing import Any, Dict, List

from django.db import connection

logger = logging.getLogger(__name__)


class SkillGraph:
    """Utility class for querying the skill knowledge graph via recursive CTEs."""

    def __init__(self, graph_name: str = 'skills_graph'):
        self.connection = connection

    def _execute_query(self, query: str, params=None) -> List[Dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(query, params or [])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def find_related_skills(self, skill_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """
        Find skills related to the given skill within the specified depth
        using a recursive CTE on the adjacency table.
        """
        query = """
            WITH RECURSIVE reachable(skill_id, distance) AS (
                SELECT to_skill_id, 1
                FROM skills_relationship
                WHERE from_skill_id = %s
                UNION
                SELECT from_skill_id, 1
                FROM skills_relationship
                WHERE to_skill_id = %s

                UNION ALL

                SELECT CASE
                    WHEN r.from_skill_id = rc.skill_id THEN r.to_skill_id
                    ELSE r.from_skill_id
                END,
                rc.distance + 1
                FROM skills_relationship r
                JOIN reachable rc ON (
                    r.from_skill_id = rc.skill_id OR r.to_skill_id = rc.skill_id
                )
                WHERE rc.distance < %s
            )
            SELECT DISTINCT
                s.id as skill_id,
                s.name as skill_name,
                s.type as skill_type,
                MIN(rc.distance) as distance
            FROM reachable rc
            JOIN skills_skill s ON s.id = rc.skill_id
            WHERE rc.skill_id != %s
            GROUP BY s.id, s.name, s.type
            ORDER BY MIN(rc.distance), s.name
            LIMIT 50
        """
        return self._execute_query(query, [skill_id, skill_id, depth, skill_id])

    def find_skill_path(self, from_skill_id: int, to_skill_id: int) -> List[List[Dict[str, Any]]]:
        """Find paths between two skills."""
        paths = []

        direct = list(self._get_direct_paths(from_skill_id, to_skill_id))
        if direct:
            paths.append(direct)

        one_hop = list(self._get_one_hop_paths(from_skill_id, to_skill_id))
        if one_hop:
            paths.extend(one_hop)

        return paths

    def _get_direct_paths(self, from_skill_id: int, to_skill_id: int) -> List[Dict[str, Any]]:
        from apps.skills.models import SkillRelationship

        return list(SkillRelationship.objects.filter(
            from_skill_id=from_skill_id,
            to_skill_id=to_skill_id
        ).values("id", "relationship_type", "weight"))

    def _get_one_hop_paths(self, from_skill_id: int, to_skill_id: int) -> List[List[Dict[str, Any]]]:
        from apps.skills.models import SkillRelationship

        from_relations = set(SkillRelationship.objects.filter(
            from_skill_id=from_skill_id
        ).values_list("to_skill_id", flat=True))

        to_relations = set(SkillRelationship.objects.filter(
            to_skill_id=to_skill_id
        ).values_list("from_skill_id", flat=True))

        paths = []
        for intermediate_id in from_relations & to_relations:
            paths.append([
                {"from_skill_id": from_skill_id, "to_skill_id": intermediate_id, "relationship_type": "related_to"},
                {"from_skill_id": intermediate_id, "to_skill_id": to_skill_id, "relationship_type": "related_to"},
            ])
        return paths

    def get_skill_distance(self, skill_id_1: int, skill_id_2: int) -> int:
        """
        Shortest-path distance between two skills using a bounded BFS via recursive CTE.
        Returns distance (edge count) or -1 if unreachable within 5 hops.
        """
        if skill_id_1 == skill_id_2:
            return 0

        query = """
            WITH RECURSIVE bfs(skill_id, distance) AS (
                SELECT to_skill_id, 1
                FROM skills_relationship
                WHERE from_skill_id = %s
                UNION
                SELECT from_skill_id, 1
                FROM skills_relationship
                WHERE to_skill_id = %s

                UNION ALL

                SELECT CASE
                    WHEN r.from_skill_id = b.skill_id THEN r.to_skill_id
                    ELSE r.from_skill_id
                END,
                b.distance + 1
                FROM skills_relationship r
                JOIN bfs b ON (
                    r.from_skill_id = b.skill_id OR r.to_skill_id = b.skill_id
                )
                WHERE b.distance < 5
            )
            SELECT MIN(distance) as min_dist
            FROM bfs
            WHERE skill_id = %s
        """
        results = self._execute_query(query, [skill_id_1, skill_id_1, skill_id_2])
        if results and results[0]['min_dist'] is not None:
            return results[0]['min_dist']
        return -1

    def get_skill_hierarchy(self, skill_id: int) -> Dict[str, Any]:
        """Get the full hierarchy path for a skill using parent traversal."""
        from apps.skills.models import Skill

        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return {"error": "Skill not found"}

        path = []
        current = skill
        while current:
            path.insert(0, {
                "id": current.id,
                "name": current.name,
                "type": current.type,
                "level": current.level,
            })
            current = current.parent

        return {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "hierarchy_path": path,
            "depth": len(path),
        }

    def get_occupation_skills(self, occupation_id: int) -> List[Dict[str, Any]]:
        from apps.skills.models import OccupationSkill

        return list(OccupationSkill.objects.filter(
            occupation_id=occupation_id
        ).select_related("skill").values(
            "skill_id",
            "skill__name",
            "skill__type",
            "importance",
            "level",
        ))

    def get_career_paths(self, occupation_id: int) -> List[Dict[str, Any]]:
        from apps.skills.models import CareerPath

        return list(CareerPath.objects.filter(
            from_occupation_id=occupation_id
        ).select_related("to_occupation").values(
            "id",
            "to_occupation_id",
            "to_occupation__name",
            "typical_years",
            "probability",
        ))
