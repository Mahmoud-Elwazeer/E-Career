"""
Management command to run verification on jobs.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.jobs.models import Job
from apps.verification.engine import VerificationEngine


class Command(BaseCommand):
    help = 'Run verification on jobs (all, pending, or specific job IDs)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--job-ids',
            type=str,
            help='Comma-separated list of job IDs to verify'
        )
        parser.add_argument(
            '--pending',
            action='store_true',
            help='Verify only jobs without verification'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='verify_all',
            help='Verify all active jobs'
        )
        parser.add_argument(
            '--trust-threshold',
            type=float,
            default=0.4,
            help='Minimum trust score threshold (default: 0.4)'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='async_mode',
            help='Run as Celery task (asynchronous)'
        )
    
    def handle(self, *args, **options):
        job_ids_str = options['job_ids']
        pending = options['pending']
        verify_all = options['verify_all']
        trust_threshold = options['trust_threshold']
        async_mode = options['async_mode']
        
        # Build query
        if job_ids_str:
            job_ids = [int(x.strip()) for x in job_ids_str.split(',') if x.strip().isdigit()]
            jobs = Job.objects.filter(id__in=job_ids)
        elif pending:
            jobs = Job.objects.filter(verification__isnull=True, status='active')
        elif verify_all:
            jobs = Job.objects.filter(status='active')
        else:
            self.stdout.write(self.style.WARNING('Please specify --job-ids, --pending, or --all'))
            return
        
        total = jobs.count()
        verified = 0
        blocked = 0
        rejected = 0
        
        self.stdout.write(f"Verifying {total} jobs...")
        
        if async_mode:
            from apps.verification.tasks import verify_job_task
            for job in jobs.iterator():
                verify_job_task.delay(job.id)
                verified += 1
            self.stdout.write(self.style.SUCCESS(f"Queued {verified} verification tasks"))
            return
        
        # Run synchronously
        engine = VerificationEngine()
        
        for job in jobs.iterator():
            try:
                result = engine.verify_job(job)
                
                if result.status == "rejected":
                    if "BLOCKED" in result.notes:
                        blocked += 1
                    else:
                        rejected += 1
                else:
                    verified += 1
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Verification failed for job {job.id}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"Verification complete! "
            f"Verified: {verified}, Blocked: {blocked}, Rejected: {rejected}"
        ))