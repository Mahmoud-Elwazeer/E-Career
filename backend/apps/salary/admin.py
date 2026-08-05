"""
Salary Intelligence Admin

This module contains Django admin configurations for salary data, market rates, and compensation insights.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import SalaryData, MarketRate, SalaryBenchmark, SalaryInsight, SalaryAlert


@admin.register(SalaryData)
class SalaryDataAdmin(admin.ModelAdmin):
    """Admin for SalaryData model."""
    
    list_display = ['job_title', 'company_name', 'salary_range', 'frequency', 'is_verified', 'extracted_at']
    list_filter = ['frequency', 'is_verified', 'source', 'extracted_at']
    search_fields = ['job__title', 'job__company__name', 'salary_currency']
    readonly_fields = ['last_updated_at', 'annualized_salary_min', 'annualized_salary_max']
    
    def job_title(self, obj):
        return obj.job.title
    job_title.admin_order_field = 'job__title'
    
    def company_name(self, obj):
        return obj.job.company.name if obj.job.company else ''
    company_name.admin_order_field = 'job__company__name'
    
    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_currency} {obj.salary_min:,} - {obj.salary_max:,}"
        elif obj.salary_min:
            return f"{obj.salary_currency} {obj.salary_min:,}+"
        return '-'
    salary_range.short_description = 'Salary'


@admin.register(MarketRate)
class MarketRateAdmin(admin.ModelAdmin):
    """Admin for MarketRate model."""
    
    list_display = ['role', 'location', 'experience_level', 'median_salary', 'sample_size', 'data_last_updated']
    list_filter = ['experience_level', 'currency', 'data_last_updated']
    search_fields = ['role', 'location']
    readonly_fields = ['data_last_updated']
    
    def median_salary(self, obj):
        return f"{obj.currency} {obj.percentile_50:,}"
    median_salary.short_description = 'Median Salary'


@admin.register(SalaryBenchmark)
class SalaryBenchmarkAdmin(admin.ModelAdmin):
    """Admin for SalaryBenchmark model."""
    
    list_display = ['user_email', 'role', 'location', 'percentile_rank', 'is_underpaid', 'calculated_at']
    list_filter = ['is_underpaid', 'experience_level', 'calculated_at']
    search_fields = ['user__email', 'role', 'location']
    readonly_fields = ['calculated_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'


@admin.register(SalaryInsight)
class SalaryInsightAdmin(admin.ModelAdmin):
    """Admin for SalaryInsight model."""
    
    list_display = ['title', 'insight_type', 'user_email', 'priority', 'is_actionable', 'generated_at']
    list_filter = ['insight_type', 'priority', 'is_actionable', 'ai_model', 'generated_at']
    search_fields = ['title', 'description', 'user__email']
    readonly_fields = ['generated_at']
    
    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.admin_order_field = 'user__email'


@admin.register(SalaryAlert)
class SalaryAlertAdmin(admin.ModelAdmin):
    """Admin for SalaryAlert model."""
    
    list_display = ['title', 'alert_type', 'user_email', 'impact', 'is_read', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'impact', 'is_read', 'is_resolved', 'created_at']
    search_fields = ['title', 'description', 'user__email']
    readonly_fields = ['created_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'
    
    actions = ['mark_as_read', 'mark_as_resolved']
    
    @admin.action(description='Mark selected alerts as read')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    
    @admin.action(description='Mark selected alerts as resolved')
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)