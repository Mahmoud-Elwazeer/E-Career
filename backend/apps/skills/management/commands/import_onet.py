"""
Management Command: import_onet

Import O*NET dataset (importance and level ratings) into the database.

Usage:
    python manage.py import_onet --importance <path> --level <path>

The O*NET dataset can be downloaded from:
- O*NET Content Model: https://services.onetcenter.org/reference/

Note: This command expects CSV files in the O*NET format.
"""

import csv
import logging
from pathlib import Path
from typing import Optional, Tuple
from django.core.management.base import BaseCommand, CommandError

from apps.skills.models import Skill, Occupation, OccupationSkill

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Import O*NET dataset into the database."""
    
    help = "Import O*NET dataset (importance and level ratings)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--importance",
            type=str,
            help="Path to O*NET importance ratings CSV file",
        )
        parser.add_argument(
            "--level",
            type=str,
            help="Path to O*NET level ratings CSV file",
        )
        parser.add_argument(
            "--crosswalk",
            type=str,
            help="Path to ESCO-O*NET crosswalk CSV file",
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
        
        self.stdout.write(self.style.SUCCESS("Starting O*NET import"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Import importance ratings
        importance_file = options.get("importance")
        if importance_file:
            self._import_importance(importance_file, dry_run, limit)
        
        # Import level ratings
        level_file = options.get("level")
        if level_file:
            self._import_level(level_file, dry_run, limit)
        
        # Import crosswalk
        crosswalk_file = options.get("crosswalk")
        if crosswalk_file:
            self._import_crosswalk(crosswalk_file, dry_run, limit)
        
        self.stdout.write(self.style.SUCCESS("O*NET import complete"))
    
    def _import_importance(self, file_path: str, dry_run: bool, limit: Optional[int]) -> Tuple[int, int]:
        """Import importance ratings from O*NET CSV file."""
        self.stdout.write(f"Importing importance ratings from {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"Importance file not found: {file_path}")
        
        imported = 0
        failed = 0
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    
                    try:
                        # Extract importance data from row
                        # O*NET format: elementId, elementName, scaleId, value, n, standardError
                        element_id = row.get("elementId", "").strip()
                        if not element_id:
                            continue
                        
                        value = row.get("value", "").strip()
                        if not value:
                            continue
                        
                        try:
                            importance = float(value)
                            if importance < 1 or importance > 5:
                                continue
                        except ValueError:
                            continue
                        
                        # Get occupation and skill from crosswalk
                        onet_code = self._extract_onet_code(element_id)
                        if not onet_code:
                            continue
                        
                        # Find matching occupation and skill
                        occupation = self._find_occupation_by_onet(onet_code)
                        if not occupation:
                            continue
                        
                        skill = self._find_skill_by_onet(element_id)
                        if not skill:
                            continue
                        
                        if not dry_run:
                            # Update or create the mapping with importance rating
                            mapping, created = OccupationSkill.objects.update_or_create(
                                occupation=occupation,
                                skill=skill,
                                defaults={
                                    "importance": importance,
                                }
                            )
                            if created:
                                imported += 1
                        else:
                            imported += 1
                            
                    except Exception as e:
                        failed += 1
                        logger.error(f"Error importing importance {row.get('elementId', 'unknown')}: {e}")
                    
                    # Progress indicator
                    if (imported + failed) % 1000 == 0:
                        self.stdout.write(f"  Processed {imported + failed} importance ratings...")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading importance file: {e}"))
            raise
        
        self.stdout.write(self.style.SUCCESS(f"Importance: {imported} imported, {failed} failed"))
        return imported, failed
    
    def _import_level(self, file_path: str, dry_run: bool, limit: Optional[int]) -> Tuple[int, int]:
        """Import level ratings from O*NET CSV file."""
        self.stdout.write(f"Importing level ratings from {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"Level file not found: {file_path}")
        
        imported = 0
        failed = 0
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    
                    try:
                        # Extract level data from row
                        element_id = row.get("elementId", "").strip()
                        if not element_id:
                            continue
                        
                        value = row.get("value", "").strip()
                        if not value:
                            continue
                        
                        try:
                            level = float(value)
                            if level < 1 or level > 7:
                                continue
                        except ValueError:
                            continue
                        
                        # Find matching occupation and skill
                        onet_code = self._extract_onet_code(element_id)
                        if not onet_code:
                            continue
                        
                        occupation = self._find_occupation_by_onet(onet_code)
                        if not occupation:
                            continue
                        
                        skill = self._find_skill_by_onet(element_id)
                        if not skill:
                            continue
                        
                        if not dry_run:
                            # Update the mapping with level rating
                            updated = OccupationSkill.objects.filter(
                                occupation=occupation,
                                skill=skill,
                            ).update(level=level)
                            if updated > 0:
                                imported += 1
                        else:
                            imported += 1
                            
                    except Exception as e:
                        failed += 1
                        logger.error(f"Error importing level {row.get('elementId', 'unknown')}: {e}")
                    
                    # Progress indicator
                    if (imported + failed) % 1000 == 0:
                        self.stdout.write(f"  Processed {imported + failed} level ratings...")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading level file: {e}"))
            raise
        
        self.stdout.write(self.style.SUCCESS(f"Level: {imported} imported, {failed} failed"))
        return imported, failed
    
    def _import_crosswalk(self, file_path: str, dry_run: bool, limit: Optional[int]) -> Tuple[int, int]:
        """Import ESCO-O*NET crosswalk from CSV file."""
        self.stdout.write(f"Importing crosswalk from {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"Crosswalk file not found: {file_path}")
        
        imported = 0
        failed = 0
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    
                    try:
                        # Extract crosswalk data from row
                        esco_uri = row.get("escoUri", "").strip()
                        onet_element_id = row.get("onetElementId", "").strip()
                        
                        if not esco_uri or not onet_element_id:
                            continue
                        
                        # Update skill with O*NET cross-reference
                        if not dry_run:
                            updated = Skill.objects.filter(
                                esco_uri=esco_uri,
                            ).update(onet_element_id=onet_element_id)
                            if updated > 0:
                                imported += 1
                        else:
                            imported += 1
                            
                    except Exception as e:
                        failed += 1
                        logger.error(f"Error importing crosswalk: {e}")
                    
                    # Progress indicator
                    if (imported + failed) % 1000 == 0:
                        self.stdout.write(f"  Processed {imported + failed} crosswalks...")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading crosswalk file: {e}"))
            raise
        
        self.stdout.write(self.style.SUCCESS(f"Crosswalk: {imported} imported, {failed} failed"))
        return imported, failed
    
    def _extract_onet_code(self, element_id: str) -> Optional[str]:
        """Extract O*NET SOC code from element ID."""
        # O*NET element IDs follow format: 27-1011.00-0000
        # The first part is the SOC code
        parts = element_id.split("-")
        if len(parts) >= 1:
            return parts[0]
        return None
    
    def _find_occupation_by_onet(self, onet_code: str) -> Optional[Occupation]:
        """Find occupation by O*NET SOC code."""
        try:
            return Occupation.objects.get(onet_soc_code=onet_code)
        except Occupation.DoesNotExist:
            return None
    
    def _find_skill_by_onet(self, element_id: str) -> Optional[Skill]:
        """Find skill by O*NET element ID."""
        try:
            return Skill.objects.get(onet_element_id=element_id)
        except Skill.DoesNotExist:
            return None