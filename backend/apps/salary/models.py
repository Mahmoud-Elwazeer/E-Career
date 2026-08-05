"""
Salary Intelligence Models

This module defines models for salary data, market rates, and compensation insights.
"""

import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import UUIDModel, TimeStampedModel
from apps.jobs.models import Job
from apps.skills.models import Skill

logger = logging.getLogger(__name__)


class SalaryData(UUIDModel):
    """
    Aggregated salary data from job postings.
    
    This model stores salary information extracted from job postings,
    used for market rate calculations and salary benchmarking.
    """
    
    # Job reference
    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name='salary_data',
        db_index=True
    )
    
    # Salary information
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum salary (annualized)"
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum salary (annualized)"
    )
    salary_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="ISO 4217 currency code (e.g., USD, EUR, EGP)"
    )
    
    # Salary frequency
    FREQUENCY_CHOICES = [
        ('yearly', 'Yearly'),
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
        ('hourly', 'Hourly'),
    ]
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='yearly',
        db_index=True
    )
    
    # Source information
    source = models.CharField(
        max_length=50,
        blank=True,
        help_text="'job_posting', 'user_reported', 'employer_input'"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this salary has been verified"
    )
    
    # Normalized annual salary (for calculations)
    annualized_salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annualized minimum salary"
    )
    annualized_salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annualized maximum salary"
    )
    
    # Metadata
    extracted_at = models.DateTimeField(null=True, blank=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "salary_data"
        verbose_name = "Salary Data"
        verbose_name_plural = "Salary Data"
    
    def __str__(self):
        return f"{self.job.title}: {self.salary_currency} {self.salary_min} - {self.salary_max}"
    
    def annualize_salary(self):
        """
        Convert salary to annualized value based on frequency.
        """
        if self.frequency == 'yearly':
            self.annualized_salary_min = self.salary_min
            self.annualized_salary_max = self.salary_max
        elif self.frequency == 'monthly':
            self.annualized_salary_min = self.salary_min * 12 if self.salary_min else None
            self.annualized_salary_max = self.salary_max * 12 if self.salary_max else None
        elif self.frequency == 'weekly':
            self.annualized_salary_min = self.salary_min * 52 if self.salary_min else None
            self.annualized_salary_max = self.salary_max * 52 if self.salary_max else None
        elif self.frequency == 'hourly':
            # Assume 40 hours/week, 52 weeks/year
            self.annualized_salary_min = self.salary_min * 40 * 52 if self.salary_min else None
            self.annualized_salary_max = self.salary_max * 40 * 52 if self.salary_max else None


class MarketRate(UUIDModel):
    """
    Market rate data for specific role/location/experience combinations.
    
    This model stores aggregated market salary data used for benchmarking.
    """
    
    # Dimensions
    role = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Job title (e.g., 'Senior Backend Engineer')"
    )
    location = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Location (e.g., 'Dubai, UAE')"
    )
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('entry', 'Entry (0-2 years)'),
            ('junior', 'Junior (2-5 years)'),
            ('mid', 'Mid (5-8 years)'),
            ('senior', 'Senior (8-12 years)'),
            ('lead', 'Lead (12+ years)'),
        ],
        db_index=True
    )
    
    # Currency
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="ISO 4217 currency code"
    )
    
    # Market statistics
    percentile_25 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="25th percentile salary"
    )
    percentile_50 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="50th percentile (median) salary"
    )
    percentile_75 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="75th percentile salary"
    )
    percentile_90 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="90th percentile salary"
    )
    
    # Statistics
    sample_size = models.IntegerField(
        default=1,
        help_text="Number of job postings used for calculation"
    )
    data_last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "market_rate"
        unique_together = [("role", "location", "experience_level")]
        verbose_name = "Market Rate"
        verbose_name_plural = "Market Rates"
    
    def __str__(self):
        return f"{self.role} - {self.location} - {self.experience_level}: {self.currency} {self.percentile_50}"
    
    def get_salary_range(self, percentile: int) -> str:
        """
        Get salary range for a specific percentile.
        
        Args:
            percentile: Percentile (25, 50, 75, 90)
            
        Returns:
            Formatted salary range string
        """
        ranges = {
            25: (self.percentile_25, self.percentile_50),
            50: (self.percentile_50, self.percentile_75),
            75: (self.percentile_75, self.percentile_90),
            90: (self.percentile_90, None),
        }
        
        low, high = ranges.get(percentile, (self.percentile_50, self.percentile_75))
        
        if high:
            return f"{self.currency} {low:,} - {high:,}"
        return f"{self.currency} {low:,}+"


class SalaryBenchmark(UUIDModel):
    """
    User salary benchmark comparison.
    
    This model stores how a user's salary compares to market rates.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='salary_benchmarks',
        db_index=True
    )
    
    # Comparison dimensions
    role = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    experience_level = models.CharField(max_length=20)
    
    # User's salary
    user_salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    user_salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Market rates
    market_median = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Market median salary"
    )
    market_25th = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Market 25th percentile"
    )
    market_75th = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Market 75th percentile"
    )
    
    # Comparison metrics
    below_market_by = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage below market median"
    )
    percentile_rank = models.IntegerField(
        null=True,
        blank=True,
        help_text="User's percentile rank in market"
    )
    
    # Assessment
    IS_UNDERPAID_CHOICES = [
        ('yes', 'Yes - Significantly underpaid'),
        ('maybe', 'Maybe - Slightly underpaid'),
        ('fair', 'Fair - Around market rate'),
        ('above', 'Above - Above market rate'),
    ]
    is_underpaid = models.CharField(
        max_length=10,
        choices=IS_UNDERPAID_CHOICES,
        default='fair'
    )
    
    # Generated insights
    negotiation_tips = models.JSONField(
        default=list,
        help_text="AI-generated negotiation tips"
    )
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "salary_benchmark"
        verbose_name = "Salary Benchmark"
        verbose_name_plural = "Salary Benchmarks"
    
    def __str__(self):
        return f"{self.user.email} - {self.role}: {self.percentile_rank}th percentile"


class SalaryInsight(UUIDModel):
    """
    AI-generated salary insights for users and employers.
    
    This model stores personalized salary insights generated by AI.
    """
    
    # Target
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='salary_insights',
        db_index=True,
        null=True,
        blank=True
    )
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employer_insights',
        db_index=True,
        null=True,
        blank=True
    )
    
    # Insight type
    INSIGHT_TYPE_CHOICES = [
        ('user_underpaid', 'User is underpaid'),
        ('user_above_market', 'User is above market'),
        ('user_negotiation', 'User should negotiate'),
        ('employer_low_range', 'Employer salary range is too low'),
        ('employer_high_range', 'Employer salary range is competitive'),
    ]
    insight_type = models.CharField(
        max_length=30,
        choices=INSIGHT_TYPE_CHOICES,
        db_index=True
    )
    
    # Content
    title = models.CharField(max_length=200)
    description = models.TextField()
    data_points = models.JSONField(
        default=dict,
        help_text="Data points supporting the insight"
    )
    
    # Actionability
    is_actionable = models.BooleanField(default=True)
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium'
    )
    
    # Generated by AI
    generated_at = models.DateTimeField(auto_now_add=True)
    ai_model = models.CharField(
        max_length=50,
        default='haiku',
        help_text="AI model used to generate insight"
    )
    
    class Meta:
        db_table = "salary_insight"
        verbose_name = "Salary Insight"
        verbose_name_plural = "Salary Insights"
    
    def __str__(self):
        return f"{self.insight_type}: {self.title}"


class SalaryAlert(UUIDModel):
    """
    Salary alert for users when market rates change significantly.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='salary_alerts',
        db_index=True
    )
    
    # Alert type
    ALERT_TYPE_CHOICES = [
        ('market_increase', 'Market rate increased'),
        ('user_below_new_market', 'User salary now below new market'),
        ('new_high_paying_job', 'New high-paying job match'),
    ]
    alert_type = models.CharField(
        max_length=30,
        choices=ALERT_TYPE_CHOICES,
        db_index=True
    )
    
    # Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    impact = models.CharField(
        max_length=20,
        choices=[
            ('minor', 'Minor'),
            ('moderate', 'Moderate'),
            ('significant', 'Significant'),
        ],
        default='moderate'
    )
    
    # Action
    action_url = models.URLField(
        blank=True,
        help_text="URL to take action"
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "salary_alert"
        verbose_name = "Salary Alert"
        verbose_name_plural = "Salary Alerts"
    
    def __str__(self):
        return f"{self.user.email} - {self.alert_type}"