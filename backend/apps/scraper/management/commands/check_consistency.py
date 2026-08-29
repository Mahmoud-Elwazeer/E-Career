"""
Consistency Checker Command

Checks for data inconsistencies across the platform:
- Jobs with invalid URLs
- Duplicate jobs
- Orphaned records
- Expired jobs not marked as expired
"""
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, Count, models

from apps.jobs.models import Job, Company, Source
from apps.core.models import PipelineHealth


class Command(BaseCommand):
    """Check for data inconsistencies."""
    
    help = 'Check for data inconsistencies across the platform'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix inconsistencies where possible',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
    
    def handle(self, *args, **options):
        fix = options.get('fix', False)
        verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.SUCCESS('Starting consistency check...'))
        self.stdout.write(f"Timestamp: {timezone.now().isoformat()}")
        self.stdout.write(f"Fix mode: {fix}")
        self.stdout.write(f"Verbose: {verbose}")
        self.stdout.write("-" * 60)
        
        issues = []
        
        # Check 1: Jobs with invalid URLs
        issues.extend(self._check_invalid_urls(fix, verbose))
        
        # Check 2: Duplicate jobs
        issues.extend(self._check_duplicates(fix, verbose))
        
        # Check 3: Orphaned records
        issues.extend(self._check_orphans(fix, verbose))
        
        # Check 4: Expired jobs not marked as expired
        issues.extend(self._check_expired_jobs(fix, verbose))
        
        # Check 5: Jobs with missing company
        issues.extend(self._check_missing_company(fix, verbose))
        
        # Summary
        self.stdout.write("-" * 60)
        self.stdout.write(self.style.SUCCESS('Consistency check complete!'))
        self.stdout.write(f"Total issues found: {len(issues)}")
        
        if issues:
            self.stdout.write(self.style.WARNING('Issues found:'))
            for issue in issues[:10]:  # Show first 10
                self.stdout.write(f"  - {issue}")
            if len(issues) > 10:
                self.stdout.write(f"  ... and {len(issues) - 10} more")
        
        # Update pipeline health
        PipelineHealth.objects.update_or_create(
            task_name='check_consistency',
            defaults={
                'last_run_at': timezone.now(),
                'last_status': 'success',
                'last_duration': 0,
                'run_count': 1,
            }
        )
    
    def _check_invalid_urls(self, fix: bool, verbose: bool) -> list:
        """Check for jobs with invalid URLs."""
        issues = []
        
        # Check jobs with empty apply URLs
        empty_urls = Job.objects.filter(
            Q(direct_apply_url='') | Q(direct_apply_url__isnull=True)
        )
        
        if empty_urls.exists():
            count = empty_urls.count()
            issues.append(f"Found {count} jobs with empty apply URLs")
            if verbose:
                for job in empty_urls[:5]:
                    issues.append(f"  - Job {job.id}: {job.title}")
            
            if fix:
                empty_urls.update(direct_apply_url=None)
                issues.append(f"Fixed {count} jobs by setting direct_apply_url to NULL")
        
        return issues
    
    def _check_duplicates(self, fix: bool, verbose: bool) -> list:
        """Check for duplicate jobs."""
        issues = []
        
        # Find jobs with same ATS platform and job ID
        duplicates = Job.objects.values('ats_platform', 'ats_job_id').annotate(
            count=models.Count('id')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            count = duplicates.count()
            issues.append(f"Found {count} sets of duplicate jobs (same ATS platform + job ID)")
            
            if verbose:
                for dup in duplicates[:5]:
                    issues.append(f"  - {dup['ats_platform']}: {dup['ats_job_id']} ({dup['count']} jobs)")
            
            if fix:
                # Keep the first job, mark others as duplicates
                for dup in duplicates:
                    jobs = Job.objects.filter(
                        ats_platform=dup['ats_platform'],
                        ats_job_id=dup['ats_job_id']
                    ).order_by('created_at')
                    
                    # Keep first, mark others as duplicate
                    for job in jobs[1:]:
                        job.is_duplicate = True
                        job.status = 'archived'
                        job.save()
                
                issues.append(f"Fixed duplicates by archiving duplicate jobs")
        
        return issues
    
    def _check_orphans(self, fix: bool, verbose: bool) -> list:
        """Check for orphaned records."""
        issues = []
        
        # Jobs without company
        jobs_without_company = Job.objects.filter(company__isnull=True)
        if jobs_without_company.exists():
            count = jobs_without_company.count()
            issues.append(f"Found {count} jobs without a company")
            
            if fix:
                jobs_without_company.delete()
                issues.append(f"Deleted {count} orphaned jobs")
        
        # Companies without jobs
        companies_without_jobs = Company.objects.filter(jobs__isnull=True)
        if companies_without_jobs.exists():
            count = companies_without_jobs.count()
            issues.append(f"Found {count} companies without jobs")
            
            if fix:
                companies_without_jobs.delete()
                issues.append(f"Deleted {count} orphaned companies")
        
        return issues
    
    def _check_expired_jobs(self, fix: bool, verbose: bool) -> list:
        """Check for expired jobs not marked as expired."""
        issues = []
        
        # Jobs past expiry date but not marked as expired
        expired_not_marked = Job.objects.filter(
            expires_at__lt=timezone.now(),
            is_expired=False
        )
        
        if expired_not_marked.exists():
            count = expired_not_marked.count()
            issues.append(f"Found {count} expired jobs not marked as expired")
            
            if fix:
                expired_not_marked.update(is_expired=True, quality_state='expired')
                issues.append(f"Fixed {count} jobs by marking as expired")
        
        return issues
    
    def _check_missing_company(self, fix: bool, verbose: bool) -> list:
        """Check for jobs with missing company information."""
        issues = []
        
        # Jobs with empty company name
        jobs_with_empty_company = Job.objects.filter(
            company__name=''
        )
        
        if jobs_with_empty_company.exists():
            count = jobs_with_empty_company.count()
            issues.append(f"Found {count} jobs with empty company name")
            
            if fix:
                jobs_with_empty_company.update(company=None)
                issues.append(f"Fixed {count} jobs by setting company to NULL")
        
        return issues