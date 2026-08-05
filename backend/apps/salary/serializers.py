"""
Salary Intelligence Serializers

This module defines DRF serializers for salary data, market rates, and compensation insights.
"""

from rest_framework import serializers
from django.conf import settings
from .models import SalaryData, MarketRate, SalaryBenchmark, SalaryInsight, SalaryAlert


class SalaryDataSerializer(serializers.ModelSerializer):
    """Serializer for SalaryData model."""
    
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    
    class Meta:
        model = SalaryData
        fields = [
            'id',
            'job',
            'job_title',
            'company_name',
            'salary_min',
            'salary_max',
            'salary_currency',
            'frequency',
            'source',
            'is_verified',
            'annualized_salary_min',
            'annualized_salary_max',
            'extracted_at',
            'last_updated_at',
        ]
        read_only_fields = ['last_updated_at']


class MarketRateSerializer(serializers.ModelSerializer):
    """Serializer for MarketRate model."""
    
    class Meta:
        model = MarketRate
        fields = [
            'id',
            'role',
            'location',
            'experience_level',
            'currency',
            'percentile_25',
            'percentile_50',
            'percentile_75',
            'percentile_90',
            'sample_size',
            'data_last_updated',
        ]
        read_only_fields = ['data_last_updated']


class SalaryBenchmarkSerializer(serializers.ModelSerializer):
    """Serializer for SalaryBenchmark model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = SalaryBenchmark
        fields = [
            'id',
            'user',
            'user_email',
            'role',
            'location',
            'experience_level',
            'user_salary_min',
            'user_salary_max',
            'market_median',
            'market_25th',
            'market_75th',
            'below_market_by',
            'percentile_rank',
            'is_underpaid',
            'negotiation_tips',
            'calculated_at',
        ]
        read_only_fields = ['calculated_at']


class SalaryInsightSerializer(serializers.ModelSerializer):
    """Serializer for SalaryInsight model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    employer_email = serializers.EmailField(source='employer.email', read_only=True)
    
    class Meta:
        model = SalaryInsight
        fields = [
            'id',
            'user',
            'user_email',
            'employer',
            'employer_email',
            'insight_type',
            'title',
            'description',
            'data_points',
            'is_actionable',
            'priority',
            'generated_at',
            'ai_model',
        ]
        read_only_fields = ['generated_at']


class SalaryAlertSerializer(serializers.ModelSerializer):
    """Serializer for SalaryAlert model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = SalaryAlert
        fields = [
            'id',
            'user',
            'user_email',
            'alert_type',
            'title',
            'description',
            'impact',
            'action_url',
            'is_read',
            'is_resolved',
            'created_at',
        ]
        read_only_fields = ['created_at']


class SalaryBenchmarkRequestSerializer(serializers.Serializer):
    """Serializer for salary benchmark request."""
    
    role = serializers.CharField()
    location = serializers.CharField()
    experience_level = serializers.CharField()
    salary_min = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    salary_max = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    currency = serializers.CharField(default='USD')


class MarketRateSearchSerializer(serializers.Serializer):
    """Serializer for market rate search."""
    
    role = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    experience_level = serializers.CharField(required=False)