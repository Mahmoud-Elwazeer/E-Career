"""
Run all health checks and report status.
Usage: python manage.py health_check
Exit code 0 = all healthy, 1 = some degraded, 2 = critical failure
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
import requests

class Command(BaseCommand):
    help = 'Run health checks on all services'
    
    def add_arguments(self, parser):
        parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        checks = {}
        critical_failures = 0
        degraded_services = 0
        
        # Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks['database'] = 'OK'
        except Exception as e:
            checks['database'] = f'FAIL: {e}'
            critical_failures += 1
        
        # Redis
        try:
            cache.set('health', 'ok', 10)
            assert cache.get('health') == 'ok'
            checks['redis'] = 'OK'
        except Exception as e:
            checks['redis'] = f'FAIL: {e}'
            degraded_services += 1
        
        # Typesense
        try:
            resp = requests.get('http://localhost:8108/health', timeout=5)
            if resp.status_code == 200:
                checks['typesense'] = 'OK'
            else:
                checks['typesense'] = f'FAIL: HTTP {resp.status_code}'
                degraded_services += 1
        except Exception as e:
            checks['typesense'] = f'FAIL: {e}'
            degraded_services += 1
        
        # Qdrant
        try:
            resp = requests.get('http://localhost:6333', timeout=5)
            if resp.status_code == 200:
                checks['qdrant'] = 'OK'
            else:
                checks['qdrant'] = f'FAIL: HTTP {resp.status_code}'
                degraded_services += 1
        except Exception as e:
            checks['qdrant'] = f'FAIL: {e}'
            degraded_services += 1
        
        # Print results
        self.stdout.write("=" * 50)
        self.stdout.write("E-Career Health Check Report")
        self.stdout.write("=" * 50)
        
        for service, status in checks.items():
            icon = '✅' if status == 'OK' else '❌'
            self.stdout.write(f"{icon} {service}: {status}")
        
        self.stdout.write("=" * 50)
        
        if critical_failures > 0:
            self.stdout.write(self.style.ERROR(f"\nCRITICAL: {critical_failures} service(s) down"))
            self.stdout.write("Please check the services and restart them.")
            raise SystemExit(2)
        elif degraded_services > 0:
            self.stdout.write(self.style.WARNING(f"\nWARNING: {degraded_services} service(s) degraded"))
            self.stdout.write("Some features may not work correctly.")
            raise SystemExit(1)
        else:
            self.stdout.write(self.style.SUCCESS("\nAll services are healthy!"))
            raise SystemExit(0)