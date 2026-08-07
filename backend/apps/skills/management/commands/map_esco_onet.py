"""
Management Command: map_esco_onet

Create mappings between ESCO skills and O*NET occupations based on name similarity.

Usage:
    python manage.py map_esco_onet --threshold 0.8

This command links our ESCO skills taxonomy with O*NET occupations for career path
recommendations by finding the best matches based on name similarity.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.skills.models import Skill, Occupation, SkillRelationship

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Map ESCO skills to O*NET occupations."""
    
    help = "Map ESCO skills to O*NET occupations based on name similarity"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.8,
            help="Minimum confidence threshold for mappings (0-1, default: 0.8)",
        )
        parser.add_argument(
            "--esco-file",
            type=str,
            help="Path to ESCO skills CSV file (optional, uses database if not provided)",
        )
        parser.add_argument(
            "--onet-file",
            type=str,
            help="Path to O*NET occupations CSV file (optional, uses database if not provided)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be mapped without actually creating mappings",
        )
    
    def handle(self, *args, **options):
        threshold = options.get("threshold", 0.8)
        dry_run = options.get("dry_run", False)
        
        self.stdout.write(self.style.SUCCESS("Starting ESCO-O*NET mapping"))
        self.stdout.write(f"Confidence threshold: {threshold}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Get ESCO skills
        if options.get("esco_file"):
            esco_skills = self._load_esco_skills(options["esco_file"])
        else:
            esco_skills = list(Skill.objects.filter(esco_uri__isnull=False).values('id', 'esco_uri', 'name', 'name_ar'))
        
        # Get O*NET occupations
        if options.get("onet_file"):
            onet_occupations = self._load_onet_occupations(options["onet_file"])
        else:
            onet_occupations = list(Occupation.objects.filter(onet_soc_code__isnull=False).values('id', 'onet_soc_code', 'name', 'name_ar'))
        
        self.stdout.write(f"Found {len(esco_skills)} ESCO skills")
        self.stdout.write(f"Found {len(onet_occupations)} O*NET occupations")
        
        # Create mappings
        mapped, avg_confidence, unmapped = self._create_mappings(
            esco_skills, onet_occupations, threshold, dry_run
        )
        
        # Log statistics
        self.stdout.write(self.style.SUCCESS(f"\nMapping Statistics:"))
        self.stdout.write(f"  Total mapped: {mapped}")
        self.stdout.write(f"  Average confidence: {avg_confidence:.2%}" if avg_confidence else "  Average confidence: N/A")
        self.stdout.write(f"  Unmapped: {unmapped}")
        
        self.stdout.write(self.style.SUCCESS("ESCO-O*NET mapping complete"))
    
    def _load_esco_skills(self, file_path: str) -> List[Dict]:
        """Load ESCO skills from CSV file."""
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"ESCO file not found: {file_path}")
        
        skills = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("preferredLabel", {}).get("en", "") or row.get("preferredLabel", "")
                skills.append({
                    "id": row.get("conceptUri", ""),
                    "esco_uri": row.get("conceptUri", ""),
                    "name": name,
                    "name_ar": row.get("altLabels", {}).get("ar", ""),
                })
        return skills
    
    def _load_onet_occupations(self, file_path: str) -> List[Dict]:
        """Load O*NET occupations from CSV file."""
        path = Path(file_path)
        if not path.exists():
            raise CommandError(f"O*NET file not found: {file_path}")
        
        occupations = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                occupations.append({
                    "id": row.get("O*NET-SOC Code", ""),
                    "onet_soc_code": row.get("O*NET-SOC Code", ""),
                    "name": row.get("Title", ""),
                    "name_ar": "",
                })
        return occupations
    
    def _create_mappings(
        self,
        esco_skills: List[Dict],
        onet_occupations: List[Dict],
        threshold: float,
        dry_run: bool
    ) -> Tuple[int, Optional[float], int]:
        """Create mappings between ESCO skills and O*NET occupations."""
        from difflib import SequenceMatcher
        
        mapped = 0
        total_confidence = 0.0
        unmapped = 0
        
        for esco_skill in esco_skills:
            best_match = None
            best_confidence = 0.0
            
            # Find best matching O*NET occupation
            for onet_occ in onet_occupations:
                # Calculate similarity between skill name and occupation title
                confidence = SequenceMatcher(
                    None,
                    esco_skill["name"].lower(),
                    onet_occ["name"].lower()
                ).ratio()
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = onet_occ
            
            # Only create mapping if confidence is above threshold
            if best_confidence >= threshold:
                if not dry_run:
                    # Create or update the mapping
                    SkillRelationship.objects.update_or_create(
                        from_skill_id=esco_skill["id"],
                        to_skill_id=best_match["id"],
                        relationship_type="related_to",
                        defaults={
                            "weight": best_confidence,
                            "source": "computed",
                        }
                    )
                mapped += 1
                total_confidence += best_confidence
            else:
                unmapped += 1
            
            # Progress indicator
            if (mapped + unmapped) % 1000 == 0:
                self.stdout.write(f"  Processed {mapped + unmapped} skills...")
        
        avg_confidence = total_confidence / mapped if mapped > 0 else None
        return mapped, avg_confidence, unmapped