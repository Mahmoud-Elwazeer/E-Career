"""
Setup scraping sources for the E-Career platform.
Adds job boards and career pages to scrape from.
"""
from django.core.management.base import BaseCommand
from apps.jobs.models import Source


SOURCES = [
    # Egyptian Job Boards
    {'name': 'Wuzzuf', 'url': 'https://wuzzuf.net', 'source_type': 'job_board', 'slug': 'wuzzuf'},
    {'name': 'LinkedIn Egypt', 'url': 'https://linkedin.com/jobs', 'source_type': 'job_board', 'slug': 'linkedin-egypt'},
    {'name': 'Bayt', 'url': 'https://bayt.com', 'source_type': 'job_board', 'slug': 'bayt'},
    {'name': 'Glassdoor', 'url': 'https://glassdoor.com', 'source_type': 'job_board', 'slug': 'glassdoor'},
    {'name': 'Indeed Egypt', 'url': 'https://eg.indeed.com', 'source_type': 'job_board', 'slug': 'indeed-eg'},
    {'name': 'Jobzella', 'url': 'https://jobzella.com', 'source_type': 'job_board', 'slug': 'jobzella'},
    {'name': 'Masrawy Jobs', 'url': 'https://jobs.masrawy.com', 'source_type': 'job_board', 'slug': 'masrawy-jobs'},
    {'name': 'Ahly Jobs', 'url': 'https://ahlyjobs.com', 'source_type': 'job_board', 'slug': 'ahly-jobs'},
    
    # MENA Job Boards
    {'name': 'Gulf Jobs', 'url': 'https://gulfjobs.com', 'source_type': 'job_board', 'slug': 'gulf-jobs'},
    {'name': 'Naukrigulf', 'url': 'https://naukrigulf.com', 'source_type': 'job_board', 'slug': 'naukrigulf'},
    {'name': 'Emirates Jobs', 'url': 'https://emiratesjobs.com', 'source_type': 'job_board', 'slug': 'emirates-jobs'},
    {'name': 'Saudi Jobs', 'url': 'https://saudijobs.com', 'source_type': 'job_board', 'slug': 'saudi-jobs'},
    
    # International Job Boards
    {'name': 'Indeed', 'url': 'https://indeed.com', 'source_type': 'job_board', 'slug': 'indeed'},
    {'name': 'Glassdoor', 'url': 'https://glassdoor.com', 'source_type': 'job_board', 'slug': 'glassdoor-intl'},
    {'name': 'LinkedIn', 'url': 'https://linkedin.com/jobs', 'source_type': 'job_board', 'slug': 'linkedin'},
    {'name': 'Indeed Global', 'url': 'https://indeed.com', 'source_type': 'job_board', 'slug': 'indeed-global'},
    
    # Tech-Specific
    {'name': 'AngelList', 'url': 'https://angellist.com', 'source_type': 'job_board', 'slug': 'angellist'},
    {'name': 'HackerRank Jobs', 'url': 'https://hackerrank.com/jobs', 'source_type': 'job_board', 'slug': 'hackerrank-jobs'},
    {'name': 'Stack Overflow Jobs', 'url': 'https://stackoverflow.com/jobs', 'source_type': 'job_board', 'slug': 'stackoverflow-jobs'},
    {'name': 'GitHub Jobs', 'url': 'https://github.com/jobs', 'source_type': 'job_board', 'slug': 'github-jobs'},
    
    # Consulting & Professional Services
    {'name': 'McKinsey Careers', 'url': 'https://mckinsey.com/careers', 'source_type': 'company_careers', 'slug': 'mckinsey'},
    {'name': 'Boston Consulting Group', 'url': 'https://bcg.com/careers', 'source_type': 'company_careers', 'slug': 'bcg'},
    {'name': 'Accenture', 'url': 'https://accenture.com/careers', 'source_type': 'company_careers', 'slug': 'accenture'},
    {'name': 'Deloitte', 'url': 'https://deloitte.com/careers', 'source_type': 'company_careers', 'slug': 'deloitte'},
    {'name': 'EY', 'url': 'https://ey.com/careers', 'source_type': 'company_careers', 'slug': 'ey'},
    {'name': 'KPMG', 'url': 'https://kpmg.com/careers', 'source_type': 'company_careers', 'slug': 'kpmg'},
    {'name': 'PwC', 'url': 'https://pwc.com/careers', 'source_type': 'company_careers', 'slug': 'pwc'},
]


class Command(BaseCommand):
    help = 'Setup scraping sources for the E-Career platform'
    
    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing sources first')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be created')
    
    def handle(self, *args, **options):
        if options['clear']:
            Source.objects.all().delete()
            self.stdout.write('Cleared existing sources')
        
        if options['dry_run']:
            self.stdout.write("=== DRY RUN MODE ===")
            self.stdout.write(f"Would create {len(SOURCES)} sources:")
            for s in SOURCES:
                self.stdout.write(f"  - {s['name']} ({s['source_type']})")
            return
        
        created = 0
        for source_data in SOURCES:
            source, is_new = Source.objects.get_or_create(
                slug=source_data['slug'],
                defaults={
                    'name': source_data['name'],
                    'url': source_data['url'],
                    'type': source_data['source_type'],
                    'is_active': True,
                }
            )
            if is_new:
                created += 1
                self.stdout.write(f"Created: {source.name}")
            else:
                self.stdout.write(f"Exists: {source.name}")
        
        self.stdout.write(self.style.SUCCESS(f"\nSetup complete! Created {created} new sources"))