"""
Database Optimization Management Command

Usage:
    python manage.py optimize_db --report
    python manage.py optimize_db --warm-cache
    python manage.py optimize_db --analyze
"""
from django.core.management.base import BaseCommand
from apps.core.db_optimization import print_optimization_report, check_database_health
from apps.core.cache import warm_cache, get_cache_stats


class Command(BaseCommand):
    help = 'Database and cache optimization utilities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report',
            action='store_true',
            help='Print database optimization report',
        )
        parser.add_argument(
            '--warm-cache',
            action='store_true',
            help='Pre-populate cache with frequent data',
        )
        parser.add_argument(
            '--cache-stats',
            action='store_true',
            help='Show cache performance statistics',
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Run database health check',
        )

    def handle(self, *args, **options):
        if options['report']:
            self.stdout.write(self.style.NOTICE('Generating optimization report...'))
            print_optimization_report()

        if options['warm_cache']:
            self.stdout.write(self.style.NOTICE('Warming cache...'))
            warm_cache()
            self.stdout.write(self.style.SUCCESS('✓ Cache warmed successfully'))

        if options['cache_stats']:
            self.stdout.write(self.style.NOTICE('Cache Statistics:'))
            stats = get_cache_stats()
            for key, value in stats.items():
                self.stdout.write(f"  {key}: {value}")

        if options['health_check']:
            self.stdout.write(self.style.NOTICE('Running health check...'))
            health = check_database_health()
            for key, value in health.items():
                style = self.style.SUCCESS if value == 'OK' or isinstance(value, int) else self.style.WARNING
                self.stdout.write(style(f"  {key}: {value}"))

        if not any([options['report'], options['warm_cache'], options['cache_stats'], options['health_check']]):
            self.stdout.write(
                self.style.WARNING('No action specified. Use --help to see available options.')
            )
