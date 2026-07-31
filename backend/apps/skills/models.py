"""
Skills App Models

This module defines the models for the skill taxonomy and knowledge graph.
Based on ESCO and O*NET datasets.
"""

import logging
from django.db import models
from apps.core.models import UUIDModel

logger = logging.getLogger(__name__)


class Skill(UUIDModel):
    id = models.UUIDField(primary_key=True, default=None, editable=False)
    
    def save(self, *args, **kwargs):
        if not self.id:
            import uuid
            self.id = uuid.uuid4()
        super().save(*args, **kwargs)
    """
    Skill model based on ESCO taxonomy.
    
    Skills are the fundamental units of the knowledge graph.
    """
    
    TYPE_CHOICES = [
        ("technical", "Technical"),
        ("soft", "Soft Skill"),
        ("language", "Language"),
        ("tool", "Tool"),
        ("framework", "Framework"),
        ("methodology", "Methodology"),
    ]
    
    CATEGORY_CHOICES = [
        ("main_group", "Main Group"),
        ("sub_group", "Sub Group"),
        ("unit_group", "Unit Group"),
        ("skill", "Skill"),
        ("detailed_skill", "Detailed Skill"),
    ]
    
    # ESCO identifier
    esco_uri = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="ESCO URI (e.g., http://data.europa.eu/esco/skill/123456)"
    )
    
    # O*NET cross-reference
    onet_element_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="O*NET element ID for cross-referencing"
    )
    
    # Skill name
    name = models.CharField(max_length=255, db_index=True)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        help_text="Arabic translation of the skill name"
    )
    
    # Classification
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="technical",
        db_index=True
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="skill",
        db_index=True
    )
    
    # Hierarchy
    level = models.IntegerField(
        default=1,
        help_text="Hierarchy depth (1=broad, 5=specific)"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        db_index=True
    )
    
    # Description
    description = models.TextField(blank=True)
    
    # Embedding for semantic similarity (pgvector)
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text="Vector embedding for semantic similarity (stored as JSON array)"
    )
    
    class Meta:
        db_table = "skills_skill"
        ordering = ["name"]
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
    
    def __str__(self):
        return self.name
    
    @property
    def is_top_level(self) -> bool:
        """Check if this is a top-level skill (no parent)."""
        return self.parent_id is None
    
    @property
    def hierarchy_path(self) -> str:
        """Get the full hierarchy path from root to this skill."""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " > ".join(path)


class SkillRelationship(UUIDModel):
    """
    Skill relationship model.
    
    Defines relationships between skills (prerequisites, related skills, etc.).
    """
    
    RELATIONSHIP_TYPE_CHOICES = [
        ("related_to", "Related To"),
        ("prerequisite_for", "Prerequisite For"),
        ("broader_than", "Broader Than"),
        ("complementary", "Complementary"),
        ("alternative", "Alternative"),
    ]
    
    SOURCE_CHOICES = [
        ("esco", "ESCO"),
        ("onet", "O*NET"),
        ("computed", "Computed"),
        ("manual", "Manual"),
    ]
    
    from_skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
        db_index=True
    )
    to_skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
        db_index=True
    )
    
    relationship_type = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_TYPE_CHOICES,
        db_index=True
    )
    
    weight = models.FloatField(
        default=1.0,
        help_text="Strength of relationship (0-1)"
    )
    
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="esco",
        db_index=True
    )
    
    class Meta:
        db_table = "skills_relationship"
        unique_together = [("from_skill", "to_skill", "relationship_type")]
        verbose_name = "Skill Relationship"
        verbose_name_plural = "Skill Relationships"
    
    def __str__(self):
        return f"{self.from_skill} → {self.to_skill} ({self.relationship_type})"


class Occupation(UUIDModel):
    """
    Occupation model based on ESCO taxonomy.
    
    Occupations are collections of skills required for specific roles.
    """
    
    # ESCO identifier
    esco_uri = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="ESCO URI (e.g., http://data.europa.eu/esco/occupation/123456)"
    )
    
    # O*NET cross-reference
    onet_soc_code = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text="O*NET SOC code for cross-referencing"
    )
    
    # Occupation name
    name = models.CharField(max_length=255, db_index=True)
    name_ar = models.CharField(
        max_length=255,
        blank=True,
        help_text="Arabic translation of the occupation name"
    )
    
    # Description
    description = models.TextField(blank=True)
    
    # Hierarchy
    level = models.IntegerField(
        default=1,
        help_text="Hierarchy depth (1=broad, 5=specific)"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        db_index=True
    )
    
    class Meta:
        db_table = "skills_occupation"
        ordering = ["name"]
        verbose_name = "Occupation"
        verbose_name_plural = "Occupations"
    
    def __str__(self):
        return self.name
    
    @property
    def is_top_level(self) -> bool:
        """Check if this is a top-level occupation (no parent)."""
        return self.parent_id is None


class OccupationSkill(UUIDModel):
    """
    Occupation-Skill mapping model.
    
    Links occupations to required skills with importance ratings from O*NET.
    """
    
    occupation = models.ForeignKey(
        Occupation,
        on_delete=models.CASCADE,
        related_name="skills",
        db_index=True
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="occupations",
        db_index=True
    )
    
    # O*NET importance rating (1-5)
    importance = models.FloatField(
        default=3.0,
        help_text="Importance rating from O*NET (1-5)"
    )
    
    # O*NET level rating (1-7)
    level = models.FloatField(
        default=3.0,
        help_text="Level rating from O*NET (1-7)"
    )
    
    class Meta:
        db_table = "skills_occupation_skill"
        unique_together = [("occupation", "skill")]
        verbose_name = "Occupation Skill"
        verbose_name_plural = "Occupation Skills"
    
    def __str__(self):
        return f"{self.occupation} requires {self.skill}"


class CareerPath(UUIDModel):
    """
    Career path model.
    
    Defines transitions between occupations (career progression).
    """
    
    from_occupation = models.ForeignKey(
        Occupation,
        on_delete=models.CASCADE,
        related_name="career_paths_from",
        db_index=True
    )
    to_occupation = models.ForeignKey(
        Occupation,
        on_delete=models.CASCADE,
        related_name="career_paths_to",
        db_index=True
    )
    
    typical_years = models.FloatField(
        null=True,
        blank=True,
        help_text="Typical number of years for this transition"
    )
    
    probability = models.FloatField(
        null=True,
        blank=True,
        help_text="Probability of this transition occurring (0-1)"
    )
    
    required_skills_delta = models.JSONField(
        null=True,
        blank=True,
        help_text="Skills needed for transition (stored as JSON)"
    )
    
    class Meta:
        db_table = "skills_career_path"
        unique_together = [("from_occupation", "to_occupation")]
        verbose_name = "Career Path"
        verbose_name_plural = "Career Paths"
    
    def __str__(self):
        return f"{self.from_occupation} → {self.to_occupation}"


class JobSkill(UUIDModel):
    """
    Job-Skill mapping model.
    
    Links jobs to extracted skills with importance ratings.
    """
    
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='skills',
        db_index=True
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='jobs',
        db_index=True
    )
    
    # Importance rating (1-5)
    importance = models.FloatField(
        default=3.0,
        help_text="Importance rating (1-5)"
    )
    
    # Experience level
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='intermediate',
        db_index=True
    )
    
    # Source of extraction
    SOURCE_CHOICES = [
        ('ai', 'AI Extraction'),
        ('manual', 'Manual'),
        ('import', 'Import'),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='ai',
        db_index=True
    )
    
    class Meta:
        db_table = "jobs_job_skill"
        unique_together = [("job", "skill")]
        verbose_name = "Job Skill"
        verbose_name_plural = "Job Skills"
    
    def __str__(self):
        return f"{self.job} requires {self.skill}"
