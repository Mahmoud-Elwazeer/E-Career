"""Seed ResumeTemplate with default templates for all 6 categories."""
from django.core.management.base import BaseCommand
from apps.resume.models import ResumeTemplate


TEMPLATES = [
    {
        'title': 'Modern Clean',
        'description': 'A clean, modern design with blue accent colors and well-organized sections. Great for tech and startup roles.',
        'category': 'modern',
        'is_premium': False,
        'rating': 4.7,
    },
    {
        'title': 'Modern Gradient',
        'description': 'Sleek design with subtle gradients and contemporary typography. Perfect for product and UX roles.',
        'category': 'modern',
        'is_premium': True,
        'rating': 4.8,
    },
    {
        'title': 'Executive Professional',
        'description': 'Classic serif typography with clean lines. Ideal for senior management and corporate positions.',
        'category': 'professional',
        'is_premium': False,
        'rating': 4.6,
    },
    {
        'title': 'Corporate Standard',
        'description': 'Traditional layout trusted by Fortune 500 hiring managers. Conservative and reliable.',
        'category': 'professional',
        'is_premium': False,
        'rating': 4.5,
    },
    {
        'title': 'Creative Portfolio',
        'description': 'Bold purple accent with creative layout touches. Made for designers, marketers, and creative professionals.',
        'category': 'creative',
        'is_premium': True,
        'rating': 4.8,
    },
    {
        'title': 'Artisan',
        'description': 'Expressive design with color blocks and visual hierarchy. Stands out for creative director and art roles.',
        'category': 'creative',
        'is_premium': True,
        'rating': 4.6,
    },
    {
        'title': 'Academic CV',
        'description': 'Comprehensive layout for publications, research, and teaching experience. Standard for academic applications.',
        'category': 'academic',
        'is_premium': False,
        'rating': 4.5,
    },
    {
        'title': 'Research Scholar',
        'description': 'Structured for grants, publications, and conference presentations. Includes sections for awards and affiliations.',
        'category': 'academic',
        'is_premium': False,
        'rating': 4.4,
    },
    {
        'title': 'Clean Minimal',
        'description': 'Maximum white space, subtle typography. Lets your experience speak for itself.',
        'category': 'minimalist',
        'is_premium': False,
        'rating': 4.7,
    },
    {
        'title': 'Swiss Design',
        'description': 'Grid-based layout inspired by Swiss design principles. Clean, structured, timeless.',
        'category': 'minimalist',
        'is_premium': True,
        'rating': 4.9,
    },
    {
        'title': 'Developer',
        'description': 'Monospace-inspired design with sections for tech stack, GitHub, and open-source contributions.',
        'category': 'technical',
        'is_premium': False,
        'rating': 4.6,
    },
    {
        'title': 'Engineering Pro',
        'description': 'Structured for engineering roles with dedicated sections for certifications, tools, and project metrics.',
        'category': 'technical',
        'is_premium': True,
        'rating': 4.7,
    },
]


class Command(BaseCommand):
    help = 'Seed ResumeTemplate with default templates for all 6 categories'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for tpl in TEMPLATES:
            _, was_created = ResumeTemplate.objects.get_or_create(
                title=tpl['title'],
                defaults=tpl,
            )
            if was_created:
                created += 1
            else:
                skipped += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {created} templates ({skipped} already existed)'))
