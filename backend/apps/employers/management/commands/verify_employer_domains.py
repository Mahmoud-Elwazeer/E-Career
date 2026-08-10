"""
Management command to verify employer job posting domains.

Usage:
    python manage.py verify_employer_domains
    python manage.py verify_employer_domains --limit 50
    python manage.py verify_employer_domains --force  # Re-verify all
"""
from django.core.management.base import BaseCommand
from apps.employers.domain_verification import bulk_verify_unverified_postings
from apps.employers.models import JobPosting


class Command(BaseCommand):
    help = 'Verify employer job posting apply URLs against company domains'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of postings to verify (default: 100)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-verify all postings, even previously verified ones',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']

        self.stdout.write(self.style.NOTICE('Starting domain verification...'))

        if force:
            # Reset all verification statuses
            count = JobPosting.objects.update(
                apply_url_verified=False,
                apply_url_checked_at=None
            )
            self.stdout.write(
                self.style.WARNING(f'Reset verification status for {count} postings')
            )

        # Run bulk verification
        results = bulk_verify_unverified_postings(limit=limit)

        # Display results
        self.stdout.write(self.style.SUCCESS('\n=== Verification Results ==='))
        self.stdout.write(f"Total processed: {results['total']}")
        self.stdout.write(
            self.style.SUCCESS(f"✓ Verified: {results['verified']}")
        )
        self.stdout.write(
            self.style.ERROR(f"✗ Failed: {results['failed']}")
        )
        self.stdout.write(
            self.style.WARNING(f"⚠ Manual review needed: {results['manual_review']}")
        )

        # Show unverified count
        unverified_remaining = JobPosting.objects.filter(
            apply_url_verified=False
        ).count()

        if unverified_remaining > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n{unverified_remaining} postings still need verification'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 All postings verified!')
            )
