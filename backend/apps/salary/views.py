"""
Salary Intelligence Views

This module contains Django REST Framework views for salary data, market rates, and compensation insights.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SalaryData, MarketRate, SalaryBenchmark, SalaryInsight, SalaryAlert
from .serializers import (
    SalaryDataSerializer,
    MarketRateSerializer,
    SalaryBenchmarkSerializer,
    SalaryInsightSerializer,
    SalaryAlertSerializer,
    SalaryBenchmarkRequestSerializer,
    MarketRateSearchSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_salary_benchmark(request):
    """
    Get salary benchmark for the authenticated user.
    
    Query Parameters:
    - role: Job title
    - location: Location
    - experience_level: Experience level
    - salary_min: User's minimum salary
    - salary_max: User's maximum salary
    """
    try:
        serializer = SalaryBenchmarkRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        role = serializer.validated_data['role']
        location = serializer.validated_data['location']
        experience_level = serializer.validated_data.get('experience_level', 'mid')
        salary_min = serializer.validated_data.get('salary_min')
        salary_max = serializer.validated_data.get('salary_max')
        
        # Get market rate
        market_rate = MarketRate.objects.filter(
            role__icontains=role,
            location__icontains=location,
            experience_level=experience_level
        ).first()
        
        if not market_rate:
            return Response({
                'success': False,
                'error': 'No market rate data available for this role/location/experience combination',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate benchmark
        percentile_rank = 50  # Default
        
        if salary_min and salary_max:
            market_median = float(market_rate.percentile_50)
            user_median = (float(salary_min) + float(salary_max)) / 2
            
            # Calculate percentile rank
            if market_median > 0:
                percentile_rank = min(99, max(1, int((user_median / market_median) * 50)))
        
        # Determine if underpaid
        if salary_min:
            market_25th = float(market_rate.percentile_25)
            if float(salary_min) < market_25th:
                is_underpaid = 'yes'
            elif float(salary_min) < float(market_rate.percentile_50):
                is_underpaid = 'maybe'
            elif float(salary_min) > float(market_rate.percentile_75):
                is_underpaid = 'above'
            else:
                is_underpaid = 'fair'
        else:
            is_underpaid = 'fair'
        
        # Generate negotiation tips
        negotiation_tips = []
        if is_underpaid in ['yes', 'maybe']:
            negotiation_tips.append({
                'type': 'salary_negotiation',
                'title': 'You may be underpaid',
                'description': f'Your salary is below the 25th percentile for this role. Consider negotiating.',
                'priority': 'high',
            })
        
        if is_underpaid == 'above':
            negotiation_tips.append({
                'type': 'salary_review',
                'title': 'You are above market',
                'description': 'Your salary is competitive. Consider asking for a raise.',
                'priority': 'medium',
            })
        
        # Create or update benchmark
        benchmark, created = SalaryBenchmark.objects.update_or_create(
            user=request.user,
            role=role,
            location=location,
            experience_level=experience_level,
            defaults={
                'user_salary_min': salary_min,
                'user_salary_max': salary_max,
                'market_median': market_rate.percentile_50,
                'market_25th': market_rate.percentile_25,
                'market_75th': market_rate.percentile_75,
                'percentile_rank': percentile_rank,
                'is_underpaid': is_underpaid,
                'negotiation_tips': negotiation_tips,
            }
        )
        
        return Response({
            'success': True,
            'data': {
                'role': role,
                'location': location,
                'experience_level': experience_level,
                'market_median': str(market_rate.percentile_50),
                'market_25th': str(market_rate.percentile_25),
                'market_75th': str(market_rate.percentile_75),
                'percentile_rank': percentile_rank,
                'is_underpaid': is_underpaid,
                'negotiation_tips': negotiation_tips,
            },
        })
        
    except Exception as e:
        logger.error("get_salary_benchmark_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_market_rates(request):
    """
    Get market rates for a specific role/location/experience combination.
    
    Query Parameters:
    - role: Job title
    - location: Location
    - experience_level: Experience level
    """
    try:
        serializer = MarketRateSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        role = serializer.validated_data.get('role')
        location = serializer.validated_data.get('location')
        experience_level = serializer.validated_data.get('experience_level')
        
        # Build query
        query = MarketRate.objects.all()
        
        if role:
            query = query.filter(role__icontains=role)
        if location:
            query = query.filter(location__icontains=location)
        if experience_level:
            query = query.filter(experience_level=experience_level)
        
        market_rates = query[:20]  # Limit to 20 results
        
        return Response({
            'success': True,
            'data': MarketRateSerializer(market_rates, many=True).data,
        })
        
    except Exception as e:
        logger.error("get_market_rates_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_salary_insights(request):
    """
    Get salary insights for the authenticated user.
    """
    try:
        insights = SalaryInsight.objects.filter(user=request.user).order_by('-generated_at')[:10]
        
        return Response({
            'success': True,
            'data': SalaryInsightSerializer(insights, many=True).data,
        })
        
    except Exception as e:
        logger.error("get_salary_insights_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_salary_alerts(request):
    """
    Get salary alerts for the authenticated user.
    """
    try:
        alerts = SalaryAlert.objects.filter(user=request.user).order_by('-created_at')
        
        return Response({
            'success': True,
            'data': SalaryAlertSerializer(alerts, many=True).data,
        })
        
    except Exception as e:
        logger.error("get_salary_alerts_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_alert_as_read(request, alert_id):
    """
    Mark a salary alert as read.
    """
    try:
        alert = SalaryAlert.objects.get(id=alert_id, user=request.user)
        alert.is_read = True
        alert.save()
        
        return Response({
            'success': True,
            'message': 'Alert marked as read',
        })
        
    except SalaryAlert.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Alert not found',
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("mark_alert_as_read_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalaryDataViewSet(APIView):
    """Viewset for SalaryData model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's salary data."""
        try:
            salary_data = SalaryData.objects.filter(job__user=request.user)
            return Response({
                'success': True,
                'data': SalaryDataSerializer(salary_data, many=True).data,
            })
        except Exception as e:
            logger.error("get_salary_data_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketRateViewSet(APIView):
    """Viewset for MarketRate model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get market rates."""
        try:
            market_rates = MarketRate.objects.all()
            return Response({
                'success': True,
                'data': MarketRateSerializer(market_rates, many=True).data,
            })
        except Exception as e:
            logger.error("get_market_rates_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalaryBenchmarkViewSet(APIView):
    """Viewset for SalaryBenchmark model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's salary benchmarks."""
        try:
            benchmarks = SalaryBenchmark.objects.filter(user=request.user)
            return Response({
                'success': True,
                'data': SalaryBenchmarkSerializer(benchmarks, many=True).data,
            })
        except Exception as e:
            logger.error("get_salary_benchmarks_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalaryInsightViewSet(APIView):
    """Viewset for SalaryInsight model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's salary insights."""
        try:
            insights = SalaryInsight.objects.filter(user=request.user)
            return Response({
                'success': True,
                'data': SalaryInsightSerializer(insights, many=True).data,
            })
        except Exception as e:
            logger.error("get_salary_insights_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalaryAlertViewSet(APIView):
    """Viewset for SalaryAlert model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's salary alerts."""
        try:
            alerts = SalaryAlert.objects.filter(user=request.user)
            return Response({
                'success': True,
                'data': SalaryAlertSerializer(alerts, many=True).data,
            })
        except Exception as e:
            logger.error("get_salary_alerts_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)