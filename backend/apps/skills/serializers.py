"""
Skills App Serializers

This module defines the serializers for the skill taxonomy models.
"""

from rest_framework import serializers
from apps.skills.models import Skill, SkillRelationship, Occupation, OccupationSkill, CareerPath


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model."""
    
    children_count = serializers.SerializerMethodField()
    hierarchy_path = serializers.CharField(read_only=True)
    
    class Meta:
        model = Skill
        fields = [
            "id",
            "esco_uri",
            "onet_element_id",
            "name",
            "name_ar",
            "type",
            "category",
            "level",
            "parent",
            "description",
            "embedding",
            "hierarchy_path",
            "children_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "hierarchy_path", "children_count"]
    
    def get_children_count(self, obj):
        return obj.children.count()


class SkillWriteSerializer(serializers.ModelSerializer):
    """Serializer for writing to Skill model."""
    
    class Meta:
        model = Skill
        fields = [
            "esco_uri",
            "onet_element_id",
            "name",
            "name_ar",
            "type",
            "category",
            "level",
            "parent",
            "description",
        ]


class SkillRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for SkillRelationship model."""
    
    from_skill_name = serializers.CharField(source="from_skill.name", read_only=True)
    to_skill_name = serializers.CharField(source="to_skill.name", read_only=True)
    
    class Meta:
        model = SkillRelationship
        fields = [
            "id",
            "from_skill",
            "from_skill_name",
            "to_skill",
            "to_skill_name",
            "relationship_type",
            "weight",
            "source",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "from_skill_name", "to_skill_name"]


class OccupationSerializer(serializers.ModelSerializer):
    """Serializer for Occupation model."""
    
    children_count = serializers.SerializerMethodField()
    skills_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Occupation
        fields = [
            "id",
            "esco_uri",
            "onet_soc_code",
            "name",
            "name_ar",
            "description",
            "level",
            "parent",
            "children_count",
            "skills_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "children_count", "skills_count"]
    
    def get_children_count(self, obj):
        return obj.children.count()
    
    def get_skills_count(self, obj):
        return obj.skills.count()


class OccupationSkillSerializer(serializers.ModelSerializer):
    """Serializer for OccupationSkill model."""
    
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    occupation_name = serializers.CharField(source="occupation.name", read_only=True)
    
    class Meta:
        model = OccupationSkill
        fields = [
            "id",
            "occupation",
            "occupation_name",
            "skill",
            "skill_name",
            "importance",
            "level",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "skill_name", "occupation_name"]


class CareerPathSerializer(serializers.ModelSerializer):
    """Serializer for CareerPath model."""
    
    from_occupation_name = serializers.CharField(source="from_occupation.name", read_only=True)
    to_occupation_name = serializers.CharField(source="to_occupation.name", read_only=True)
    
    class Meta:
        model = CareerPath
        fields = [
            "id",
            "from_occupation",
            "from_occupation_name",
            "to_occupation",
            "to_occupation_name",
            "typical_years",
            "probability",
            "required_skills_delta",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "from_occupation_name", "to_occupation_name"]


# Utility serializers for API responses

class SkillHierarchySerializer(serializers.ModelSerializer):
    """Serializer for skill hierarchy display."""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Skill
        fields = ["id", "name", "type", "category", "level", "children"]
    
    def get_children(self, obj):
        children = obj.children.all()[:10]  # Limit to 10 children
        return SkillHierarchySerializer(children, many=True).data


class OccupationWithSkillsSerializer(serializers.ModelSerializer):
    """Serializer for occupation with its required skills."""
    
    skills = serializers.SerializerMethodField()
    
    class Meta:
        model = Occupation
        fields = ["id", "name", "description", "skills"]
    
    def get_skills(self, obj):
        occupation_skills = obj.skills.select_related("skill").all()[:50]
        return [
            {
                "id": os.skill.id,
                "name": os.skill.name,
                "importance": os.importance,
                "level": os.level,
            }
            for os in occupation_skills
        ]


class SkillSearchSerializer(serializers.Serializer):
    """Serializer for skill search results."""
    
    query = serializers.CharField()
    results = SkillSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()