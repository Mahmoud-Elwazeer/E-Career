"""
Graph Query Utilities for Apache AGE

This module provides utilities for querying the skill knowledge graph using Apache AGE.
"""

import logging
from typing import Any, Dict, List, Optional
from django.db import connection

logger = logging.getLogger(__name__)


class SkillGraph:
    """Utility class for querying the skill knowledge graph using Apache AGE."""

    def __init__(self, graph_name: str = 'skills_graph'):
        self.connection = connection
        self.graph_name = graph_name
    
    def _execute_cypher(self, cypher: str) -> List[Dict[str, Any]]:
        """Execute a Cypher query using Apache AGE."""
        query = f"""
        SELECT * FROM cypher('{self.graph_name}', $$
            {cypher}
        $$) as (result agtype);
        """
        with self.connection.cursor() as cursor:
            try:
                cursor.execute("LOAD 'age';")
                cursor.execute("SET search_path = ag_catalog, '$user', public;")
                cursor.execute(query)
                results = cursor.fetchall()
                return [self._parse_agtype(row[0]) for row in results]
            except Exception as e:
                logger.error(f"AGE query failed: {e}, falling back to Django ORM")
                return []

    def _parse_agtype(self, agtype_result) -> Dict[str, Any]:
        """Parse AGE agtype result to Python dict."""
        # Apache AGE returns results as JSON-like strings
        # This is a simplified parser - in production you'd use the official parser
        import json
        if isinstance(agtype_result, str):
            try:
                return json.loads(agtype_result)
            except:
                return {"value": agtype_result}
        return agtype_result or {}

    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query (fallback for non-graph queries)."""
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def find_related_skills(self, skill_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """
        Find skills related to the given skill within the specified depth using AGE.

        Args:
            skill_id: UUID of the source skill
            depth: Maximum depth of relationships to traverse

        Returns:
            List of related skills with relationship information
        """
        # Try AGE first
        cypher = f"""
            MATCH (s:Skill {{id: '{skill_id}'}})-[r*1..{depth}]-(related:Skill)
            RETURN DISTINCT related.id as skill_id,
                   related.name as skill_name,
                   related.type as skill_type,
                   length(r) as distance
            LIMIT 50
        """

        results = self._execute_cypher(cypher)

        # Fallback to Django ORM if AGE fails
        if not results:
            logger.warning("AGE query failed, using Django ORM fallback")
            query = f"""
                SELECT
                    r.id as relationship_id,
                    r.relationship_type,
                    r.weight,
                    s.id as skill_id,
                    s.name as skill_name,
                    s.type as skill_type
                FROM skills_relationship r
                JOIN skills_skill s ON (
                    (r.from_skill_id = '{skill_id}' AND r.to_skill_id = s.id) OR
                    (r.to_skill_id = '{skill_id}' AND r.from_skill_id = s.id)
                )
                WHERE s.id != '{skill_id}'
                LIMIT 50
            """
            return self._execute_query(query)

        return results
    
    def find_skill_path(self, from_skill_id: int, to_skill_id: int) -> List[List[Dict[str, Any]]]:
        """
        Find paths between two skills.
        
        Args:
            from_skill_id: ID of the source skill
            to_skill_id: ID of the target skill
            
        Returns:
            List of paths (each path is a list of skills and relationships)
        """
        # This is a simplified implementation using Django ORM
        # For complex graph queries, consider using Apache AGE or Neo4j
        
        paths = []
        
        # Direct relationships
        direct = list(self._get_direct_paths(from_skill_id, to_skill_id))
        if direct:
            paths.append(direct)
        
        # One-hop paths
        one_hop = list(self._get_one_hop_paths(from_skill_id, to_skill_id))
        if one_hop:
            paths.extend(one_hop)
        
        return paths
    
    def _get_direct_paths(self, from_skill_id: int, to_skill_id: int) -> List[Dict[str, Any]]:
        """Get direct relationships between two skills."""
        from apps.skills.models import SkillRelationship
        
        return list(SkillRelationship.objects.filter(
            from_skill_id=from_skill_id,
            to_skill_id=to_skill_id
        ).values(
            "id", "relationship_type", "weight"
        ))
    
    def _get_one_hop_paths(self, from_skill_id: int, to_skill_id: int) -> List[List[Dict[str, Any]]]:
        """Get one-hop paths through intermediate skills."""
        from apps.skills.models import SkillRelationship, Skill
        
        # Find skills connected to from_skill
        from_relations = list(SkillRelationship.objects.filter(
            from_skill_id=from_skill_id
        ).values_list("to_skill_id", flat=True))
        
        # Find skills connected to to_skill
        to_relations = list(SkillRelationship.objects.filter(
            to_skill_id=to_skill_id
        ).values_list("from_skill_id", flat=True))
        
        # Find common intermediate skills
        intermediate_ids = set(from_relations) & set(to_relations)
        
        paths = []
        for intermediate_id in intermediate_ids:
            path = [
                {
                    "from_skill_id": from_skill_id,
                    "to_skill_id": intermediate_id,
                    "relationship_type": "related_to",
                },
                {
                    "from_skill_id": intermediate_id,
                    "to_skill_id": to_skill_id,
                    "relationship_type": "related_to",
                },
            ]
            paths.append(path)
        
        return paths
    
    def get_skill_distance(self, skill_id_1: int, skill_id_2: int) -> int:
        """
        Calculate the shortest path distance between two skills.
        
        Args:
            skill_id_1: ID of the first skill
            skill_id_2: ID of the second skill
            
        Returns:
            Shortest path distance (number of edges), or -1 if no path exists
        """
        if skill_id_1 == skill_id_2:
            return 0
        
        # Check for direct relationship
        from apps.skills.models import SkillRelationship
        
        direct = SkillRelationship.objects.filter(
            from_skill_id=skill_id_1,
            to_skill_id=skill_id_2
        ).exists()
        
        if direct:
            return 1
        
        # Check for one-hop paths
        from_relations = list(SkillRelationship.objects.filter(
            from_skill_id=skill_id_1
        ).values_list("to_skill_id", flat=True))
        
        to_relations = list(SkillRelationship.objects.filter(
            to_skill_id=skill_id_2
        ).values_list("from_skill_id", flat=True))
        
        if set(from_relations) & set(to_relations):
            return 2
        
        # For longer paths, we would need BFS or Dijkstra's algorithm
        # This is a simplified implementation
        return -1
    
    def get_skill_hierarchy(self, skill_id: int) -> Dict[str, Any]:
        """
        Get the full hierarchy path for a skill.
        
        Args:
            skill_id: ID of the skill
            
        Returns:
            Dictionary with hierarchy information
        """
        from apps.skills.models import Skill
        
        try:
            skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            return {"error": "Skill not found"}
        
        # Build hierarchy path
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
        """
        Get all skills required for an occupation.
        
        Args:
            occupation_id: ID of the occupation
            
        Returns:
            List of skills with importance and level ratings
        """
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
        """
        Get all career paths from an occupation.
        
        Args:
            occupation_id: ID of the occupation
            
        Returns:
            List of career paths with destination information
        """
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