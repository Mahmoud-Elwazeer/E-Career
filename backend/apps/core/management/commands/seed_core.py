"""
Management command to seed core data (feature flags and rules).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import FeatureFlag, Rule
from core.seed_data import get_feature_flags, get_rules


class Command(BaseCommand):
    """Seed feature flags and rules into the database."""
    
    help = 'Seed feature flags and rules into the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--feature-flags',
            action='store_true',
            help='Seed only feature flags',
        )
        parser.add_argument(
            '--rules',
            action='store_true',
            help='Seed only rules',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Seed all data',
        )
    
    @transaction.atomic
    def handle(self, *args, **options):
        seed_feature_flags = options.get('feature_flags') or options.get('all')
        seed_rules = options.get('rules') or options.get('all')
        
        if seed_feature_flags:
            self.seed_feature_flags()
        
        if seed_rules:
            self.seed_rules()
        
        if not (seed_feature_flags or seed_rules):
            self.seed_feature_flags()
            self.seed_rules()
    
    def seed_feature_flags(self):
        """Seed feature flags."""
        self.stdout.write('Seeding feature flags...')
        
        feature_flags = get_feature_flags()
        created_count = 0
        updated_count = 0
        
        for flag_data in feature_flags:
            flag, created = FeatureFlag.objects.update_or_create(
                key=flag_data['key'],
                defaults=flag_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created: {flag.label}')
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {flag.label}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Feature flags: {created_count} created, {updated_count} updated'
            )
        )
    
    def seed_rules(self):
        """Seed rules."""
        self.stdout.write('Seeding rules...')
        
        rules = get_rules()
        created_count = 0
        updated_count = 0
        
        for rule_data in rules:
            rule, created = Rule.objects.update_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created: {rule.name}')
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {rule.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Rules: {created_count} created, {updated_count} updated'
            )
        )