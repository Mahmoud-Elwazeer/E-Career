"""
Import companies from OpenJobs companies_v2.json.
Download from: https://github.com/outscal/OpenJobs/raw/main/data/companies_v2.json
"""
import json
import requests
from django.core.management.base import BaseCommand
from apps.jobs.models import Company, Source


OPENJOBS_URL = "https://raw.githubusercontent.com/outscal/OpenJobs/main/data/companies_v2.json"


class Command(BaseCommand):
    help = 'Import companies from OpenJobs companies_v2.json'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=None,
            help='Path to local companies JSON file (optional, downloads if not provided)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of companies to import (for testing)'
        )
    
    def handle(self, *args, **options):
        file_path = options['file']
        limit = options['limit']
        
        if file_path:
            self.stdout.write(f"Loading companies from {file_path}...")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            self.stdout.write("Downloading companies from OpenJobs repository...")
            try:
                response = requests.get(OPENJOBS_URL, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Failed to download: {e}"))
                return
        
        if limit:
            data = data[:limit]
            self.stdout.write(f"Processing {limit} companies (limited)...")
        else:
            self.stdout.write(f"Processing {len(data)} companies...")
        
        companies_added = 0
        companies_updated = 0
        sources_added = 0
        sources_updated = 0
        skipped = 0
        
        for company_data in data:
            company_name = company_data.get('name', '').strip()
            website = company_data.get('website', '').strip()
            ats_links = company_data.get('ats_links', [])

            # Skip if no name or no ATS links
            if not company_name or not ats_links:
                skipped += 1
                continue

            # Generate slug from company name
            from django.utils.text import slugify
            slug = slugify(company_name)

            # Extract domain from website
            if website:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(website).netloc.replace('www.', '')
                except:
                    domain = website
            else:
                domain = ''

            # Process each ATS link (ats_links is a list of URL strings)
            for ats_url in ats_links:
                if not ats_url or not isinstance(ats_url, str):
                    continue
                ats_url = ats_url.strip()

                # Detect ATS platform from URL
                ats_platform = 'unknown'
                if 'greenhouse.io' in ats_url:
                    ats_platform = 'greenhouse'
                elif 'lever.co' in ats_url:
                    ats_platform = 'lever'
                elif 'ashbyhq.com' in ats_url:
                    ats_platform = 'ashby'
                elif 'bamboohr.com' in ats_url:
                    ats_platform = 'bamboohr'
                elif 'myworkdayjobs.com' in ats_url:
                    ats_platform = 'workday'

                # Skip if ATS not supported
                if ats_platform == 'unknown':
                    continue

                # Create or update company
                company, created = Company.objects.update_or_create(
                    slug=slug,
                    defaults={
                        'name': company_name,
                        'domain': domain,
                        'website': website,
                        'careers_page_url': ats_url,
                    }
                )

                if created:
                    companies_added += 1
                else:
                    companies_updated += 1

                # Create source for scraping (unique per ATS platform)
                source_slug = f"{slug}-{ats_platform}"
                source, created = Source.objects.update_or_create(
                    slug=source_slug,
                    defaults={
                        'name': f"{company_name} ({ats_platform.title()})",
                        'url': ats_url,
                        'ats_platform': ats_platform,
                        'is_active': True,
                    }
                )

                if created:
                    sources_added += 1
                else:
                    sources_updated += 1

                # Only process first supported ATS link per company
                break
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Import complete!\n"
                f"Companies: {companies_added} added, {companies_updated} updated\n"
                f"Sources: {sources_added} added, {sources_updated} updated\n"
                f"Skipped: {skipped} (missing required fields)"
            )
        )