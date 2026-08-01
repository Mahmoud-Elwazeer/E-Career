"""
Skills Admin Configuration

This module defines the Django admin interface for the skill taxonomy.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.skills.models import Skill, SkillRelationship, Occupation, OccupationSkill, CareerPath


@admin.register(Skill)
class SkillAdmin(ModelAdmin):
    """Admin interface for Skill model."""
    
    list_display = [
        "name",
        "type",
        "category",
        "level",
        "parent",
        "esco_uri",
        "created_at",
    ]
    list_filter = [
        "type",
        "category",
        "level",
        "parent",
        "created_at",
    ]
    search_fields = [
        "name",
        "esco_uri",
        "onet_element_id",
    ]
    ordering = ["name"]
    list_select_related = ["parent"]
    autocomplete_fields = ["parent"]
    readonly_fields = ["esco_uri", "created_at", "updated_at"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": (
                "name",
                "name_ar",
                "type",
                "category",
                "description",
            )
        }),
        ("ESCO Identifier", {
            "fields": (
                "esco_uri",
                "onet_element_id",
            )
        }),
        ("Hierarchy", {
            "fields": (
                "level",
                "parent",
            )
        }),
        ("System Fields", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )


@admin.register(SkillRelationship)
class SkillRelationshipAdmin(ModelAdmin):
    """Admin interface for SkillRelationship model."""
    
    list_display = [
        "from_skill",
        "relationship_type",
        "to_skill",
        "weight",
        "source",
        "created_at",
    ]
    list_filter = [
        "relationship_type",
        "source",
        "created_at",
    ]
    search_fields = [
        "from_skill__name",
        "to_skill__name",
    ]
    ordering = ["from_skill__name"]
    list_select_related = ["from_skill", "to_skill"]
    autocomplete_fields = ["from_skill", "to_skill"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Relationship", {
            "fields": (
                "from_skill",
                "to_skill",
                "relationship_type",
            )
        }),
        ("Details", {
            "fields": (
                "weight",
                "source",
            )
        }),
        ("System Fields", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )


@admin.register(Occupation)
class OccupationAdmin(ModelAdmin):
    """Admin interface for Occupation model."""
    
    list_display = [
        "name",
        "level",
        "parent",
        "esco_uri",
        "created_at",
    ]
    list_filter = [
        "level",
        "parent",
        "created_at",
    ]
    search_fields = [
        "name",
        "esco_uri",
        "onet_soc_code",
    ]
    ordering = ["name"]
    list_select_related = ["parent"]
    autocomplete_fields = ["parent"]
    readonly_fields = ["esco_uri", "created_at", "updated_at"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": (
                "name",
                "name_ar",
                "description",
            )
        }),
        ("ESCO Identifier", {
            "fields": (
                "esco_uri",
                "onet_soc_code",
            )
        }),
        ("Hierarchy", {
            "fields": (
                "level",
                "parent",
            )
        }),
        ("System Fields", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )


@admin.register(OccupationSkill)
class OccupationSkillAdmin(ModelAdmin):
    """Admin interface for OccupationSkill model."""
    
    list_display = [
        "occupation",
        "skill",
        "importance",
        "level",
        "created_at",
    ]
    list_filter = [
        "importance",
        "level",
        "created_at",
    ]
    search_fields = [
        "occupation__name",
        "skill__name",
    ]
    ordering = ["occupation__name", "skill__name"]
    list_select_related = ["occupation", "skill"]
    autocomplete_fields = ["occupation", "skill"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Mapping", {
            "fields": (
                "occupation",
                "skill",
            )
        }),
        ("Ratings", {
            "fields": (
                "importance",
                "level",
            )
        }),
        ("System Fields", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )


@admin.register(CareerPath)
class CareerPathAdmin(ModelAdmin):
    """Admin interface for CareerPath model."""
    
    list_display = [
        "from_occupation",
        "to_occupation",
        "typical_years",
        "probability",
        "created_at",
    ]
    list_filter = [
        "created_at",
    ]
    search_fields = [
        "from_occupation__name",
        "to_occupation__name",
    ]
    ordering = ["from_occupation__name"]
    list_select_related = ["from_occupation", "to_occupation"]
    autocomplete_fields = ["from_occupation", "to_occupation"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Career Path", {
            "fields": (
                "from_occupation",
                "to_occupation",
            )
        }),
        ("Metrics", {
            "fields": (
                "typical_years",
                "probability",
                "required_skills_delta",
            )
        }),
        ("System Fields", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )