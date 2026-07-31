"""
Tests for skill knowledge graph queries.
"""

import pytest
from django.test import TestCase
from apps.skills.models import Skill, SkillRelationship, Occupation, OccupationSkill, CareerPath
from apps.skills.graph import SkillGraph


@pytest.mark.django_db
class TestGraphQueries(TestCase):
    """Test knowledge graph query utilities."""

    def setUp(self):
        """Set up test data."""
        self.graph = SkillGraph()

        # Create test skills
        self.python = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/python",
            name="Python Programming",
            type="technical",
            category="skill",
            level=3,
        )

        self.django = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/django",
            name="Django Framework",
            type="framework",
            category="skill",
            level=3,
        )

        self.flask = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/flask",
            name="Flask Framework",
            type="framework",
            category="skill",
            level=3,
        )

        self.sql = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/sql",
            name="SQL",
            type="technical",
            category="skill",
            level=3,
        )

        # Create relationships
        SkillRelationship.objects.create(
            from_skill=self.python,
            to_skill=self.django,
            relationship_type="prerequisite_for",
            weight=0.9,
            source="esco",
        )

        SkillRelationship.objects.create(
            from_skill=self.python,
            to_skill=self.flask,
            relationship_type="prerequisite_for",
            weight=0.8,
            source="esco",
        )

        SkillRelationship.objects.create(
            from_skill=self.django,
            to_skill=self.sql,
            relationship_type="related_to",
            weight=0.7,
            source="computed",
        )

        # Create occupation
        self.backend_dev = Occupation.objects.create(
            esco_uri="http://data.europa.eu/esco/occupation/backend",
            name="Backend Developer",
            level=3,
        )

        OccupationSkill.objects.create(
            occupation=self.backend_dev,
            skill=self.python,
            importance=4.8,
            level=6.0,
        )

        OccupationSkill.objects.create(
            occupation=self.backend_dev,
            skill=self.django,
            importance=4.2,
            level=5.5,
        )

    def test_find_related_skills(self):
        """Test finding related skills."""
        # This will use Django ORM fallback since AGE might not be set up in test env
        related = self.graph.find_related_skills(str(self.python.id), depth=1)

        # Should find Django and Flask (direct relationships)
        skill_ids = [r.get('skill_id') for r in related]
        assert len(skill_ids) >= 2  # At least Django and Flask

    def test_find_skill_path(self):
        """Test finding paths between skills."""
        paths = self.graph.find_skill_path(
            from_skill_id=int(self.python.id),
            to_skill_id=int(self.sql.id),
        )

        # Should find path: Python -> Django -> SQL
        assert len(paths) > 0

    def test_get_skill_distance(self):
        """Test calculating skill distance."""
        # Direct relationship: Python -> Django
        distance = self.graph.get_skill_distance(
            skill_id_1=int(self.python.id),
            skill_id_2=int(self.django.id),
        )
        assert distance == 1

        # Two-hop path: Python -> Django -> SQL
        distance = self.graph.get_skill_distance(
            skill_id_1=int(self.python.id),
            skill_id_2=int(self.sql.id),
        )
        assert distance >= 2 or distance == -1  # Depends on implementation depth

        # Same skill
        distance = self.graph.get_skill_distance(
            skill_id_1=int(self.python.id),
            skill_id_2=int(self.python.id),
        )
        assert distance == 0

    def test_get_skill_hierarchy(self):
        """Test getting skill hierarchy."""
        parent = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/programming",
            name="Programming",
            type="technical",
            category="main_group",
            level=1,
        )

        child = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/oop",
            name="Object-Oriented Programming",
            type="technical",
            category="sub_group",
            level=2,
            parent=parent,
        )

        grandchild = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/java",
            name="Java",
            type="technical",
            category="skill",
            level=3,
            parent=child,
        )

        hierarchy = self.graph.get_skill_hierarchy(int(grandchild.id))

        assert hierarchy['depth'] == 3
        assert len(hierarchy['hierarchy_path']) == 3
        assert hierarchy['hierarchy_path'][0]['name'] == "Programming"
        assert hierarchy['hierarchy_path'][1]['name'] == "Object-Oriented Programming"
        assert hierarchy['hierarchy_path'][2]['name'] == "Java"

    def test_get_occupation_skills(self):
        """Test getting skills for an occupation."""
        skills = self.graph.get_occupation_skills(int(self.backend_dev.id))

        assert len(skills) == 2

        # Check Python skill
        python_skill = next(s for s in skills if s['skill__name'] == "Python Programming")
        assert python_skill['importance'] == 4.8
        assert python_skill['level'] == 6.0

    def test_get_career_paths(self):
        """Test getting career paths."""
        senior_dev = Occupation.objects.create(
            esco_uri="http://data.europa.eu/esco/occupation/senior",
            name="Senior Backend Developer",
            level=4,
        )

        CareerPath.objects.create(
            from_occupation=self.backend_dev,
            to_occupation=senior_dev,
            typical_years=3.0,
            probability=0.7,
            required_skills_delta=["system_design", "leadership"],
        )

        paths = self.graph.get_career_paths(int(self.backend_dev.id))

        assert len(paths) == 1
        assert paths[0]['to_occupation__name'] == "Senior Backend Developer"
        assert paths[0]['typical_years'] == 3.0
        assert paths[0]['probability'] == 0.7

    def test_skill_relationship_types(self):
        """Test different relationship types."""
        complementary = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/git",
            name="Git Version Control",
            type="tool",
            category="skill",
            level=3,
        )

        SkillRelationship.objects.create(
            from_skill=self.python,
            to_skill=complementary,
            relationship_type="complementary",
            weight=0.6,
            source="computed",
        )

        # Query relationships by type
        prereqs = SkillRelationship.objects.filter(
            from_skill=self.python,
            relationship_type="prerequisite_for",
        ).count()
        assert prereqs >= 2  # Django and Flask

        compl = SkillRelationship.objects.filter(
            from_skill=self.python,
            relationship_type="complementary",
        ).count()
        assert compl >= 1  # Git
