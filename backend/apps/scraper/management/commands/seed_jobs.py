"""
Generate realistic demo jobs for the E-Career platform.
Covers Egyptian/MENA market: Cairo, Alexandria, Dubai, Riyadh, Remote.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from apps.jobs.models import Job, Company, Source, Tag
import random
import uuid
from datetime import timedelta

COMPANIES = [
    {'name': 'Vodafone Egypt', 'industry': 'Telecommunications', 'website': 'https://careers.vodafone.com.eg'},
    {'name': 'Amazon MENA', 'industry': 'Technology', 'website': 'https://amazon.jobs'},
    {'name': 'Careem', 'industry': 'Technology', 'website': 'https://careers.careem.com'},
    {'name': 'Valeo Egypt', 'industry': 'Automotive', 'website': 'https://valeo.com/en/careers'},
    {'name': 'Orange Egypt', 'industry': 'Telecommunications', 'website': 'https://orange.jobs'},
    {'name': 'Instabug', 'industry': 'Technology', 'website': 'https://instabug.com/careers'},
    {'name': 'Swvl', 'industry': 'Transportation', 'website': 'https://swvl.com/careers'},
    {'name': 'Fawry', 'industry': 'Fintech', 'website': 'https://fawry.com/careers'},
    {'name': 'Noon', 'industry': 'E-commerce', 'website': 'https://noon.com/careers'},
    {'name': 'Talabat', 'industry': 'Food Delivery', 'website': 'https://talabat.com/careers'},
    {'name': 'McKinsey Cairo', 'industry': 'Consulting', 'website': 'https://mckinsey.com/careers'},
    {'name': 'PwC Middle East', 'industry': 'Consulting', 'website': 'https://pwc.com/me/careers'},
    {'name': 'Microsoft Egypt', 'industry': 'Technology', 'website': 'https://careers.microsoft.com'},
    {'name': 'IBM Egypt', 'industry': 'Technology', 'website': 'https://ibm.com/careers'},
    {'name': 'Dell Technologies Egypt', 'industry': 'Technology', 'website': 'https://dell.com/careers'},
    {'name': 'Banque Misr', 'industry': 'Banking', 'website': 'https://banquemisr.com/careers'},
    {'name': 'CIB Egypt', 'industry': 'Banking', 'website': 'https://cibeg.com/careers'},
    {'name': 'Orascom', 'industry': 'Construction', 'website': 'https://orascom.com/careers'},
    {'name': 'Si-Ware Systems', 'industry': 'Hardware', 'website': 'https://si-ware.com/careers'},
    {'name': 'Eventum', 'industry': 'Events', 'website': 'https://eventum.com.eg/careers'},
]

JOB_TEMPLATES = [
    # Engineering
    {'title': 'Senior Backend Engineer', 'tags': ['Python', 'Django', 'PostgreSQL', 'AWS'], 'salary_min': 25000, 'salary_max': 50000},
    {'title': 'Frontend Developer', 'tags': ['React', 'TypeScript', 'Tailwind'], 'salary_min': 15000, 'salary_max': 35000},
    {'title': 'Full Stack Developer', 'tags': ['Node.js', 'React', 'MongoDB'], 'salary_min': 20000, 'salary_max': 45000},
    {'title': 'DevOps Engineer', 'tags': ['Docker', 'Kubernetes', 'AWS', 'CI/CD'], 'salary_min': 30000, 'salary_max': 60000},
    {'title': 'Mobile Developer (Flutter)', 'tags': ['Flutter', 'Dart', 'Firebase'], 'salary_min': 18000, 'salary_max': 40000},
    {'title': 'Data Engineer', 'tags': ['Python', 'Spark', 'Airflow', 'SQL'], 'salary_min': 25000, 'salary_max': 55000},
    {'title': 'Machine Learning Engineer', 'tags': ['Python', 'TensorFlow', 'PyTorch'], 'salary_min': 30000, 'salary_max': 65000},
    {'title': 'QA Engineer', 'tags': ['Selenium', 'Python', 'API Testing'], 'salary_min': 12000, 'salary_max': 25000},
    {'title': 'iOS Developer', 'tags': ['Swift', 'SwiftUI', 'Xcode'], 'salary_min': 20000, 'salary_max': 45000},
    {'title': 'Android Developer', 'tags': ['Kotlin', 'Jetpack Compose', 'Firebase'], 'salary_min': 18000, 'salary_max': 40000},
    # Product/Design
    {'title': 'Product Manager', 'tags': ['Product Strategy', 'Agile', 'Analytics'], 'salary_min': 25000, 'salary_max': 55000},
    {'title': 'UX/UI Designer', 'tags': ['Figma', 'User Research', 'Prototyping'], 'salary_min': 15000, 'salary_max': 35000},
    {'title': 'Technical Product Owner', 'tags': ['Scrum', 'JIRA', 'Technical Writing'], 'salary_min': 22000, 'salary_max': 45000},
    # Business
    {'title': 'Digital Marketing Manager', 'tags': ['SEO', 'Google Ads', 'Social Media'], 'salary_min': 12000, 'salary_max': 30000},
    {'title': 'Business Development Manager', 'tags': ['Sales', 'B2B', 'CRM'], 'salary_min': 18000, 'salary_max': 40000},
    {'title': 'Financial Analyst', 'tags': ['Excel', 'Financial Modeling', 'SQL'], 'salary_min': 15000, 'salary_max': 35000},
    {'title': 'HR Manager', 'tags': ['Recruitment', 'Performance Management', 'HRIS'], 'salary_min': 15000, 'salary_max': 30000},
    {'title': 'Operations Manager', 'tags': ['Logistics', 'Process Improvement', 'KPIs'], 'salary_min': 20000, 'salary_max': 45000},
    # Entry Level
    {'title': 'Junior Software Developer', 'tags': ['JavaScript', 'Python', 'Git'], 'salary_min': 8000, 'salary_max': 15000},
    {'title': 'Customer Support Specialist', 'tags': ['Communication', 'CRM', 'English'], 'salary_min': 6000, 'salary_max': 12000},
]

LOCATIONS = ['Cairo, Egypt', 'Alexandria, Egypt', 'Giza, Egypt', 'Dubai, UAE', 'Riyadh, Saudi Arabia', 'Remote']
EXPERIENCE_LEVELS = ['entry', 'mid', 'senior', 'lead']
LOCATION_TYPES = ['remote', 'onsite', 'hybrid']
EMPLOYMENT_TYPES = ['full_time', 'part_time', 'contract', 'internship', 'freelance']


class Command(BaseCommand):
    help = 'Seed 200+ realistic job listings for the MENA market'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=200, help='Number of jobs to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing seeded jobs first')
    
    def handle(self, *args, **options):
        count = options['count']
        
        if options['clear']:
            Job.objects.filter(source__name='seed_data').delete()
            self.stdout.write('Cleared existing seeded jobs')
        
        # Create or get seed source
        source, _ = Source.objects.get_or_create(
            name='seed_data',
            defaults={'url': 'https://jobs.usamif.com', 'type': 'manual', 'is_active': True}
        )
        
        # Create companies
        companies = []
        for c in COMPANIES:
            company, _ = Company.objects.get_or_create(
                name=c['name'],
                defaults={
                    'industry': c['industry'],
                    'website': c['website'],
                    'is_active': True,
                    'slug': c['name'].lower().replace(' ', '-').replace('(', '').replace(')', ''),
                }
            )
            companies.append(company)
        
        # Create tags
        tags_cache = {}
        for template in JOB_TEMPLATES:
            for tag_name in template['tags']:
                if tag_name not in tags_cache:
                    tag, _ = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'category': 'skill', 'slug': slugify(tag_name)}
                    )
                    tags_cache[tag_name] = tag
        
        # Generate jobs
        created = 0
        for i in range(count):
            template = random.choice(JOB_TEMPLATES)
            company = random.choice(companies)
            location = random.choice(LOCATIONS)
            exp = random.choice(EXPERIENCE_LEVELS)
            location_type = random.choice(LOCATION_TYPES)
            employment_type = random.choice(EMPLOYMENT_TYPES)
            
            # Vary salary based on location
            multiplier = 1.0
            if 'Dubai' in location or 'Riyadh' in location:
                multiplier = 2.5
            elif 'Egypt' in location:
                multiplier = 1.0
            
            posted_days_ago = random.randint(1, 30)
            
            title_str = f"{template['title']} - {company.name}"
            slug = slugify(f"{title_str}-{uuid.uuid4().hex[:8]}")

            job = Job.objects.create(
                title=title_str,
                slug=slug,
                company=company,
                source=source,
                location=location,
                location_type=location_type,
                experience_level=exp,
                employment_type=employment_type,
                salary_min=int(template['salary_min'] * multiplier),
                salary_max=int(template['salary_max'] * multiplier),
                salary_currency='EGP' if 'Egypt' in location else ('AED' if 'UAE' in location else 'SAR'),
                description=f"We are looking for a {template['title']} to join {company.name} in {location}. This is a {exp}-level position. You will work on challenging projects and grow your skills with our team.",
                source_url=f"https://jobs.usamif.com/view/{i}",
                direct_apply_url=f"{company.website}/apply/{i}",
                status='active',
                posted_at=timezone.now() - timedelta(days=posted_days_ago),
                deadline=timezone.now() + timedelta(days=60 - posted_days_ago),
            )
            
            # Add tags
            for tag_name in template['tags']:
                job.tags.add(tags_cache[tag_name])
            
            created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created} jobs across {len(companies)} companies'))