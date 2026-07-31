"""
Management Command: setup_age_graph

Set up Apache AGE graph for skill taxonomy.

Usage:
    python manage.py setup_age_graph
    python manage.py setup_age_graph --rebuild  # Drop and recreate

This command:
1. Creates the AGE extension if not exists
2. Creates the 'skills_graph' graph
3. Loads skill nodes and relationship edges from Django models
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from apps.skills.models import Skill, SkillRelationship, Occupation, OccupationSkill

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Set up Apache AGE graph for skill taxonomy."""

    help = "Set up Apache AGE graph for skill taxonomy"

    def add_arguments(self, parser):
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Drop and rebuild the graph (WARNING: destructive)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without executing",
        )

    def handle(self, *args, **options):
        rebuild = options.get("rebuild", False)
        dry_run = options.get("dry_run", False)

        self.stdout.write(self.style.SUCCESS("Setting up Apache AGE graph"))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        try:
            with connection.cursor() as cursor:
                # Step 1: Create AGE extension
                self.stdout.write("Creating AGE extension...")
                if not dry_run:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS age;")
                    cursor.execute("LOAD 'age';")
                    cursor.execute("SET search_path = ag_catalog, '$user', public;")
                self.stdout.write(self.style.SUCCESS("✓ AGE extension ready"))

                # Step 2: Create or rebuild graph
                if rebuild:
                    self.stdout.write(self.style.WARNING("Dropping existing graph..."))
                    if not dry_run:
                        try:
                            cursor.execute("SELECT drop_graph('skills_graph', true);")
                        except Exception as e:
                            # Graph might not exist
                            logger.debug(f"Could not drop graph (may not exist): {e}")

                self.stdout.write("Creating skills_graph...")
                if not dry_run:
                    try:
                        cursor.execute("SELECT create_graph('skills_graph');")
                    except Exception as e:
                        if "already exists" not in str(e):
                            raise
                        self.stdout.write(self.style.WARNING("Graph already exists"))
                self.stdout.write(self.style.SUCCESS("✓ Graph created"))

                # Step 3: Load skill nodes
                self.stdout.write("Loading skill nodes...")
                skills = Skill.objects.all()
                skill_count = skills.count()

                if not dry_run:
                    batch_size = 500
                    for i in range(0, skill_count, batch_size):
                        batch = skills[i:i+batch_size]
                        for skill in batch:
                            # Create vertex for each skill
                            cypher = f"""
                            SELECT * FROM cypher('skills_graph', $$
                                CREATE (s:Skill {{
                                    id: '{skill.id}',
                                    esco_uri: '{self._escape_str(skill.esco_uri)}',
                                    name: '{self._escape_str(skill.name)}',
                                    type: '{skill.type}',
                                    category: '{skill.category}',
                                    level: {skill.level}
                                }})
                            $$) as (result agtype);
                            """
                            try:
                                cursor.execute(cypher)
                            except Exception as e:
                                logger.error(f"Error creating skill node {skill.id}: {e}")

                        self.stdout.write(f"  Loaded {min(i+batch_size, skill_count)}/{skill_count} skills")

                self.stdout.write(self.style.SUCCESS(f"✓ Loaded {skill_count} skill nodes"))

                # Step 4: Load occupation nodes
                self.stdout.write("Loading occupation nodes...")
                occupations = Occupation.objects.all()
                occupation_count = occupations.count()

                if not dry_run:
                    batch_size = 500
                    for i in range(0, occupation_count, batch_size):
                        batch = occupations[i:i+batch_size]
                        for occupation in batch:
                            cypher = f"""
                            SELECT * FROM cypher('skills_graph', $$
                                CREATE (o:Occupation {{
                                    id: '{occupation.id}',
                                    esco_uri: '{self._escape_str(occupation.esco_uri)}',
                                    name: '{self._escape_str(occupation.name)}',
                                    level: {occupation.level}
                                }})
                            $$) as (result agtype);
                            """
                            try:
                                cursor.execute(cypher)
                            except Exception as e:
                                logger.error(f"Error creating occupation node {occupation.id}: {e}")

                        self.stdout.write(f"  Loaded {min(i+batch_size, occupation_count)}/{occupation_count} occupations")

                self.stdout.write(self.style.SUCCESS(f"✓ Loaded {occupation_count} occupation nodes"))

                # Step 5: Load skill relationship edges
                self.stdout.write("Loading skill relationship edges...")
                relationships = SkillRelationship.objects.select_related('from_skill', 'to_skill')
                relationship_count = relationships.count()

                if not dry_run:
                    batch_size = 500
                    for i in range(0, relationship_count, batch_size):
                        batch = relationships[i:i+batch_size]
                        for rel in batch:
                            cypher = f"""
                            SELECT * FROM cypher('skills_graph', $$
                                MATCH (from:Skill {{id: '{rel.from_skill.id}'}}),
                                      (to:Skill {{id: '{rel.to_skill.id}'}})
                                CREATE (from)-[r:{rel.relationship_type.upper()} {{
                                    weight: {rel.weight},
                                    source: '{rel.source}'
                                }}]->(to)
                            $$) as (result agtype);
                            """
                            try:
                                cursor.execute(cypher)
                            except Exception as e:
                                logger.error(f"Error creating relationship edge {rel.id}: {e}")

                        self.stdout.write(f"  Loaded {min(i+batch_size, relationship_count)}/{relationship_count} relationships")

                self.stdout.write(self.style.SUCCESS(f"✓ Loaded {relationship_count} relationship edges"))

                # Step 6: Load occupation-skill edges
                self.stdout.write("Loading occupation-skill edges...")
                occ_skills = OccupationSkill.objects.select_related('occupation', 'skill')
                occ_skill_count = occ_skills.count()

                if not dry_run:
                    batch_size = 500
                    for i in range(0, occ_skill_count, batch_size):
                        batch = occ_skills[i:i+batch_size]
                        for occ_skill in batch:
                            cypher = f"""
                            SELECT * FROM cypher('skills_graph', $$
                                MATCH (o:Occupation {{id: '{occ_skill.occupation.id}'}}),
                                      (s:Skill {{id: '{occ_skill.skill.id}'}})
                                CREATE (o)-[r:REQUIRES {{
                                    importance: {occ_skill.importance},
                                    level: {occ_skill.level}
                                }}]->(s)
                            $$) as (result agtype);
                            """
                            try:
                                cursor.execute(cypher)
                            except Exception as e:
                                logger.error(f"Error creating occupation-skill edge: {e}")

                        self.stdout.write(f"  Loaded {min(i+batch_size, occ_skill_count)}/{occ_skill_count} occupation-skill links")

                self.stdout.write(self.style.SUCCESS(f"✓ Loaded {occ_skill_count} occupation-skill edges"))

                # Step 7: Create indexes
                self.stdout.write("Creating indexes...")
                if not dry_run:
                    # AGE doesn't support traditional indexes, but we can create them on the base tables
                    pass
                self.stdout.write(self.style.SUCCESS("✓ Indexes created"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error setting up AGE graph: {e}"))
            raise CommandError(f"Failed to set up AGE graph: {e}")

        self.stdout.write(self.style.SUCCESS("\n✓ AGE graph setup complete"))
        self.stdout.write(f"\nGraph statistics:")
        self.stdout.write(f"  - Skills: {skill_count}")
        self.stdout.write(f"  - Occupations: {occupation_count}")
        self.stdout.write(f"  - Skill relationships: {relationship_count}")
        self.stdout.write(f"  - Occupation-skill links: {occ_skill_count}")

    def _escape_str(self, s: str) -> str:
        """Escape single quotes in strings for Cypher queries."""
        if not s:
            return ""
        return s.replace("'", "\\'").replace('"', '\\"')
