"""
Tests for ESCO and O*NET taxonomy import.
"""

import pytest
from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from apps.skills.models import Skill, Occupation, OccupationSkill, SkillRelationship


@pytest.mark.django_db
class TestESCOImport(TestCase):
    """Test ESCO dataset import."""

    def test_import_skills_dry_run(self):
        """Test import_esco command in dry-run mode."""
        out = StringIO()
        # Dry run should not raise errors even with missing files
        # In production, you'd provide actual ESCO CSV paths
        pass

    def test_skill_model_creation(self):
        """Test creating a skill instance."""
        skill = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/test123",
            name="Python Programming",
            type="technical",
            category="skill",
            level=3,
            description="Ability to write Python code",
        )

        assert skill.id is not None
        assert skill.name == "Python Programming"
        assert skill.type == "technical"
        assert skill.is_top_level is True

    def test_skill_hierarchy(self):
        """Test skill hierarchy relationships."""
        parent = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/parent",
            name="Programming",
            type="technical",
            category="main_group",
            level=1,
        )

        child = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/child",
            name="Python Programming",
            type="technical",
            category="skill",
            level=2,
            parent=parent,
        )

        assert child.parent == parent
        assert child.is_top_level is False
        assert child.hierarchy_path == "Programming > Python Programming"
        assert parent.children.count() == 1

    def test_occupation_creation(self):
        """Test creating an occupation instance."""
        occupation = Occupation.objects.create(
            esco_uri="http://data.europa.eu/esco/occupation/test456",
            name="Software Developer",
            level=3,
            description="Develops software applications",
        )

        assert occupation.id is not None
        assert occupation.name == "Software Developer"
        assert occupation.is_top_level is True

    def test_occupation_skill_mapping(self):
        """Test occupation-skill mapping."""
        skill = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/test123",
            name="Python Programming",
            type="technical",
            category="skill",
            level=3,
        )

        occupation = Occupation.objects.create(
            esco_uri="http://data.europa.eu/esco/occupation/test456",
            name="Software Developer",
            level=3,
        )

        mapping = OccupationSkill.objects.create(
            occupation=occupation,
            skill=skill,
            importance=4.5,
            level=5.0,
        )

        assert mapping.occupation == occupation
        assert mapping.skill == skill
        assert mapping.importance == 4.5
        assert mapping.level == 5.0
        assert occupation.skills.count() == 1
        assert skill.occupations.count() == 1

    def test_skill_relationship(self):
        """Test skill relationship creation."""
        skill1 = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/test1",
            name="Python Programming",
            type="technical",
            category="skill",
            level=3,
        )

        skill2 = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/test2",
            name="Django Framework",
            type="framework",
            category="skill",
            level=3,
        )

        relationship = SkillRelationship.objects.create(
            from_skill=skill1,
            to_skill=skill2,
            relationship_type="prerequisite_for",
            weight=0.8,
            source="manual",
        )

        assert relationship.from_skill == skill1
        assert relationship.to_skill == skill2
        assert relationship.relationship_type == "prerequisite_for"
        assert relationship.weight == 0.8
        assert skill1.outgoing_relationships.count() == 1
        assert skill2.incoming_relationships.count() == 1

    def test_skill_unique_esco_uri(self):
        """Test that esco_uri must be unique."""
        Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/unique",
            name="Test Skill",
            type="technical",
            category="skill",
            level=3,
        )

        with pytest.raises(Exception):  # IntegrityError
            Skill.objects.create(
                esco_uri="http://data.europa.eu/esco/skill/unique",
                name="Duplicate Skill",
                type="technical",
                category="skill",
                level=3,
            )


@pytest.mark.django_db
class TestONETImport(TestCase):
    """Test O*NET dataset import."""

    def test_onet_crosswalk(self):
        """Test O*NET to ESCO crosswalk."""
        skill = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/test123",
            onet_element_id="2.A.1.a",
            name="Reading Comprehension",
            type="technical",
            category="skill",
            level=3,
        )

        assert skill.onet_element_id == "2.A.1.a"

        # Test query by O*NET ID
        found = Skill.objects.filter(onet_element_id="2.A.1.a").first()
        assert found == skill

    def test_occupation_skill_importance_ratings(self):
        """Test O*NET importance and level ratings."""
        skill = Skill.objects.create(
            esco_uri="http://data.europa.eu/esco/skill/test123",
            name="Python Programming",
            type="technical",
            category="skill",
            level=3,
        )

        occupation = Occupation.objects.create(
            esco_uri="http://data.europa.eu/esco/occupation/test456",
            onet_soc_code="15-1252.00",
            name="Software Developer",
            level=3,
        )

        mapping = OccupationSkill.objects.create(
            occupation=occupation,
            skill=skill,
            importance=4.5,  # O*NET scale 1-5
            level=6.2,  # O*NET scale 1-7
        )

        assert 1.0 <= mapping.importance <= 5.0
        assert 1.0 <= mapping.level <= 7.0
