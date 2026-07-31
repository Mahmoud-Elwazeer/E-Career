"""
Management Command: import_esco

Import ESCO dataset (skills, occupations, and mappings) into the database.

Usage:
    python manage.py import_esco --skills <path> --occupations <path> --mappings <path>

The ESCO dataset can be downloaded from:
- Skills: https://ec.europa.eu/esco/portal/download
- Occupations: https://ec.europa.eu/esco/portal/download
- Mappings: https://ec.europa.eu/esco/portal/download

Note: This command expects CSV files in the ESCO format.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.skills.models import Skill, Occupation, OccupationSkill

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Import ESCO dataset into the database."""
    
    help = "Import ESCO dataset (skills, occupations, and mappings)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--skills",
            type=str,
            help="Path to ESCO skills CSV file",
        )
        parser.add_argument(
            "--occupations",
            type=str,
            help="Path to ESCO occupations CSV file",
        )
        parser.add_argument(
            "--mappings",
            type=str,
            help="Path to ESCO skill-to-occupation mappings CSV file",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without actually importing",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of records to import (for testing)",
        )
    
    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        limit = options.get("limit")
        
        self.stdout.write(self.style.SUCCESS("Starting ESCO import"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Import skills
        skills_file = options.get("skills")
        if skills_file:
            self._import_skills(skills_file, dry_run, limit)
        
        # Import occupations
        occupations_file = options.get("occupations")
        if occupations_file:
            self._import_occupations(occupations_file, dry_run, limit)
        
        # Import mappings
        mappings_file = options.get("mappings")
        if mappings_file:
            self._import_mappings(mappings_file, dry_run, limit)
        
        self.stdout.write(self.style.SUCCESS("ESCO import complete"))
    
    def _import_skills(self, file_path: str, dry_run: bool, limit: Optional[int]) -> Tuple[int, int]:
        """Import skills from ESCO CSV file."""
        self.stdout.write(f"Importing skills from {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"Skills file not found: {file_path}")
        
        imported = 0
        failed = 0
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    
                    try:
                        # Extract skill data from row
                        # ESCO CSV format varies, adjust field names as needed
                        esco_uri = row.get("conceptUri", "").strip()
                        if not esco_uri:
                            continue
                        
                        name = row.get("preferredLabel", {}).get("en", "") or row.get("preferredLabel", "")
                        description = row.get("definition", {}).get("en", "") or row.get("definition", "")
                        
                        # Determine skill type and category based on URI
                        skill_type = self._determine_skill_type(esco_uri)
                        category = self._determine_skill_category(esco_uri)
                        
                        # Get parent skill if exists
                        parent = None
                        parent_uri = row.get("broader", "")
                        if parent_uri:
                            try:
                                parent = Skill.objects.get(esco_uri=parent_uri)
                            except Skill.DoesNotExist:
                                pass
                        
                        if not dry_run:
                            skill, created = Skill.objects.update_or_create(
                                esco_uri=esco_uri,
                                defaults={
                                    "name": name[:255],
                                    "description": description,
                                    "type": skill_type,
                                    "category": category,
                                    "parent": parent,
                                }
                            )
                            if created:
                                imported += 1
                        else:
                            imported += 1
                            
                    except Exception as e:
                        failed += 1
                        logger.error(f"Error importing skill {row.get('conceptUri', 'unknown')}: {e}")
                    
                    # Progress indicator
                    if (imported + failed) % 1000 == 0:
                        self.stdout.write(f"  Processed {imported + failed} skills...")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading skills file: {e}"))
            raise
        
        self.stdout.write(self.style.SUCCESS(f"Skills: {imported} imported, {failed} failed"))
        return imported, failed
    
    def _import_occupations(self, file_path: str, dry_run: bool, limit: Optional[int]) -> Tuple[int, int]:
        """Import occupations from ESCO CSV file."""
        self.stdout.write(f"Importing occupations from {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"Occupations file not found: {file_path}")
        
        imported = 0
        failed = 0
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    
                    try:
                        # Extract occupation data from row
                        esco_uri = row.get("conceptUri", "").strip()
                        if not esco_uri:
                            continue
                        
                        name = row.get("preferredLabel", {}).get("en", "") or row.get("preferredLabel", "")
                        description = row.get("definition", {}).get("en", "") or row.get("definition", "")
                        
                        # Get parent occupation if exists
                        parent = None
                        parent_uri = row.get("broader", "")
                        if parent_uri:
                            try:
                                parent = Occupation.objects.get(esco_uri=parent_uri)
                            except Occupation.DoesNotExist:
                                pass
                        
                        if not dry_run:
                            occupation, created = Occupation.objects.update_or_create(
                                esco_uri=esco_uri,
                                defaults={
                                    "name": name[:255],
                                    "description": description,
                                    "parent": parent,
                                }
                            )
                            if created:
                                imported += 1
                        else:
                            imported += 1
                            
                    except Exception as e:
                        failed += 1
                        logger.error(f"Error importing occupation {row.get('conceptUri', 'unknown')}: {e}")
                    
                    # Progress indicator
                    if (imported + failed) % 1000 == 0:
                        self.stdout.write(f"  Processed {imported + failed} occupations...")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading occupations file: {e}"))
            raise
        
        self.stdout.write(self.style.SUCCESS(f"Occupations: {imported} imported, {failed} failed"))
        return imported, failed
    
    def _import_mappings(self, file_path: str, dry_run: bool, limit: Optional[int]) -> Tuple[int, int]:
        """Import skill-to-occupation mappings from ESCO CSV file."""
        self.stdout.write(f"Importing mappings from {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"Mappings file not found: {file_path}")
        
        imported = 0
        failed = 0
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    
                    try:
                        # Extract mapping data from row
                        skill_uri = row.get("skillUri", "").strip()
                        occupation_uri = row.get("occupationUri", "").strip()
                        
                        if not skill_uri or not occupation_uri:
                            continue
                        
                        # Get skill and occupation
                        try:
                            skill = Skill.objects.get(esco_uri=skill_uri)
                            occupation = Occupation.objects.get(esco_uri=occupation_uri)
                        except (Skill.DoesNotExist, Occupation.DoesNotExist):
                            continue
                        
                        if not dry_run:
                            # Create mapping
                            mapping, created = OccupationSkill.objects.get_or_create(
                                occupation=occupation,
                                skill=skill,
                                defaults={
                                    "importance": 3.0,  # Default importance
                                    "level": 3.0,  # Default level
                                }
                            )
                            if created:
                                imported += 1
                        else:
                            imported += 1
                            
                    except Exception as e:
                        failed += 1
                        logger.error(f"Error importing mapping: {e}")
                    
                    # Progress indicator
                    if (imported + failed) % 1000 == 0:
                        self.stdout.write(f"  Processed {imported + failed} mappings...")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading mappings file: {e}"))
            raise
        
        self.stdout.write(self.style.SUCCESS(f"Mappings: {imported} imported, {failed} failed"))
        return imported, failed
    
    def _determine_skill_type(self, esco_uri: str) -> str:
        """Determine skill type from ESCO URI."""
        if "/skill/" in esco_uri:
            return "technical"
        elif "/language/" in esco_uri:
            return "language"
        elif "/tool/" in esco_uri:
            return "tool"
        elif "/framework/" in esco_uri:
            return "framework"
        elif "/methodology/" in esco_uri:
            return "methodology"
        else:
            return "technical"
    
    def _determine_skill_category(self, esco_uri: str) -> str:
        """Determine skill category from ESCO URI."""
        # ESCO skills have hierarchy levels in the URI
        if "/skill/" in esco_uri:
            parts = esco_uri.split("/")
            if len(parts) >= 6:
                return "skill"
        return "skill"