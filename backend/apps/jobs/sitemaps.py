"""
Sitemap configuration for job listings.
Generates sitemap.xml for search engine optimization.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.jobs.models import Job, Company


class StaticPagesSitemap(Sitemap):
    """Sitemap for static pages."""
    
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"
    
    def items(self):
        return ['home', 'about', 'contact']
    
    def location(self, item):
        return reverse(item)


class JobSitemap(Sitemap):
    """Sitemap for job listings."""
    
    changefreq = "daily"
    priority = 0.9
    protocol = "https"
    
    def items(self):
        # quality_state is authoritative for visibility, not the legacy
        # status field (status is stale/write-once-rejected - see
        # Job.objects.visible() and apps/jobs/views.py for the same fix).
        return Job.objects.visible().filter(is_expired=False)
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at
    
    def location(self, obj):
        return reverse('job-detail', kwargs={'slug': obj.slug})


class CompanySitemap(Sitemap):
    """Sitemap for company profiles."""
    
    changefreq = "monthly"
    priority = 0.7
    protocol = "https"
    
    def items(self):
        return Company.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at
    
    def location(self, obj):
        return reverse('company-detail', kwargs={'slug': obj.slug})


# Export all sitemaps
sitemaps = {
    'static': StaticPagesSitemap,
    'jobs': JobSitemap,
    'companies': CompanySitemap,
}