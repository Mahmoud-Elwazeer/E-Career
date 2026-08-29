"""
Core app views for Rule Engine, Feature Flags, and GitHub Integration.
"""

import structlog
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Rule, FeatureFlag, GitHubConnection, PortfolioAnalysis
from .serializers import (
    RuleSerializer,
    RuleTestSerializer,
    FeatureFlagSerializer,
    GitHubConnectionSerializer,
    PortfolioAnalysisSerializer,
    GitHubConnectSerializer,
    PortfolioAnalyzeSerializer,
)
from .rule_engine import RuleEngine, get_seed_rules

logger = structlog.get_logger()


# ============================================================================
# Health Check Views
# ============================================================================

class HealthCheckView(APIView):
    """Simple health check endpoint."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Check database
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            return Response({
                "success": True,
                "data": {
                    "status": "healthy",
                    "database": "ok"
                },
                "message": "Service is running.",
                "errors": None
            })
        except Exception as e:
            return Response({
                "success": False,
                "data": None,
                "message": "Service unhealthy",
                "errors": [str(e)]
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class DetailedHealthCheckView(APIView):
    """Detailed health check with all services."""
    permission_classes = [AllowAny]

    def get(self, request):
        checks = {}

        # Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks['database'] = {'status': 'ok'}
        except Exception as e:
            checks['database'] = {'status': 'error', 'message': str(e)}

        # Redis
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                checks['redis'] = {'status': 'ok'}
            else:
                checks['redis'] = {'status': 'error', 'message': 'Cache read failed'}
        except Exception as e:
            checks['redis'] = {'status': 'error', 'message': str(e)}

        # Overall status
        overall = 'healthy' if all(c.get('status') == 'ok' for c in checks.values()) else 'degraded'

        return Response({
            "success": True,
            "data": {
                "status": overall,
                "checks": checks
            },
            "message": f"Service is {overall}",
            "errors": None
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rules(request):
    """Get all rules for authenticated user."""
    try:
        rules = Rule.objects.all()
        serializer = RuleSerializer(rules, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
        })
    except Exception as e:
        logger.error("get_rules_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_rules(request):
    """Test rules against a context."""
    try:
        serializer = RuleTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        context = serializer.validated_data.get('context', {})
        stop_on_first = serializer.validated_data.get('stop_on_first', False)
        
        rules = Rule.objects.filter(is_active=True)
        engine = RuleEngine(context=context)
        results = engine.evaluate_rules(rules, stop_on_first=stop_on_first)
        
        return Response({
            'success': True,
            'context': context,
            'stop_on_first': stop_on_first,
            'results': [r.to_dict() for r in results],
            'executed_actions': engine.execute_actions(),
        })
    except Exception as e:
        logger.error("test_rules_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feature_flags(request):
    """Get all feature flags with user-specific availability."""
    try:
        flags = FeatureFlag.objects.all()
        serializer = FeatureFlagSerializer(flags, many=True, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data,
        })
    except Exception as e:
        logger.error("get_feature_flags_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_feature_flag(request, key: str):
    """Check if a specific feature flag is enabled for the user."""
    try:
        flag = FeatureFlag.objects.filter(key=key).first()
        
        if not flag:
            return Response({
                'success': False,
                'error': f"Feature flag '{key}' not found",
            }, status=status.HTTP_404_NOT_FOUND)
        
        is_enabled = flag.is_available_for_user(request.user)
        
        return Response({
            'success': True,
            'key': key,
            'is_enabled': is_enabled,
            'flag': FeatureFlagSerializer(flag, context={'request': request}).data,
        })
    except Exception as e:
        logger.error("check_feature_flag_failed", key=key, error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def github_connections(request):
    """Get or create GitHub connections for authenticated user."""
    if request.method == 'GET':
        try:
            connections = GitHubConnection.objects.filter(user=request.user)
            serializer = GitHubConnectionSerializer(connections, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
            })
        except Exception as e:
            logger.error("get_github_connections_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = GitHubConnectSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # TODO: Implement GitHub OAuth flow
            # For now, return placeholder response
            return Response({
                'success': True,
                'message': 'GitHub OAuth flow not yet implemented',
                'data': serializer.validated_data,
            })
        except Exception as e:
            logger.error("create_github_connection_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def portfolio_analyses(request):
    """Get or create portfolio analyses for authenticated user."""
    if request.method == 'GET':
        try:
            analyses = PortfolioAnalysis.objects.filter(user=request.user)
            serializer = PortfolioAnalysisSerializer(analyses, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
            })
        except Exception as e:
            logger.error("get_portfolio_analyses_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            serializer = PortfolioAnalyzeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            url = serializer.validated_data['url']
            
            # Create analysis record
            analysis = PortfolioAnalysis.objects.create(
                user=request.user,
                url=url,
                status='analyzing',
            )
            
            # TODO: Implement portfolio analysis
            # For now, return placeholder response
            return Response({
                'success': True,
                'message': 'Portfolio analysis started',
                'data': PortfolioAnalysisSerializer(analysis).data,
            })
        except Exception as e:
            logger.error("create_portfolio_analysis_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seed_rules(request):
    """Seed initial rules into the database."""
    try:
        seed_data = get_seed_rules()
        
        created_count = 0
        for rule_data in seed_data:
            rule, created = Rule.objects.get_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )
            if created:
                created_count += 1
        
        return Response({
            'success': True,
            'message': f"Seeded {created_count} new rules",
            'total_rules': len(seed_data),
        })
    except Exception as e:
        logger.error("seed_rules_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RuleViewSet(APIView):
    """Viewset for Rule model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all rules."""
        return get_rules(request)
    
    def post(self, request):
        """Test rules against context."""
        return test_rules(request)


class FeatureFlagViewSet(APIView):
    """Viewset for FeatureFlag model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all feature flags."""
        return get_feature_flags(request)


class GitHubConnectionViewSet(APIView):
    """Viewset for GitHubConnection model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's GitHub connections."""
        return github_connections(request)
    
    def post(self, request):
        """Connect GitHub account."""
        return github_connections(request)


class PortfolioAnalysisViewSet(APIView):
    """Viewset for PortfolioAnalysis model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's portfolio analyses."""
        return portfolio_analyses(request)
    
    def post(self, request):
        """Analyze portfolio URL."""
        return portfolio_analyses(request)


# ============================================================================
# GDPR Compliance Views
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_user_data(request):
    """
    Export all user data in GDPR-compliant format.
    
    Returns:
        JSON with all user data organized by category
    """
    try:
        from .gdpr_service import GDPRService
        service = GDPRService(request.user)
        export_data = service.export_user_data()
        
        return Response({
            'success': True,
            'data': export_data,
        })
    except Exception as e:
        logger.error("export_user_data_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_user_data(request):
    """
    Delete all user data in a GDPR-compliant manner.
    
    This permanently deletes all user data.
    
    Returns:
        Dictionary with deletion results
    """
    try:
        from .gdpr_service import GDPRService
        service = GDPRService(request.user)
        deletion_results = service.delete_user_data()
        
        return Response({
            'success': True,
            'message': 'User data deleted successfully',
            'data': deletion_results,
        })
    except Exception as e:
        logger.error("delete_user_data_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def anonymize_user_data(request):
    """
    Anonymize user data instead of deleting it (for analytics retention).
    
    This preserves analytics data while removing personally identifiable information.
    
    Returns:
        Dictionary with anonymization results
    """
    try:
        from .gdpr_service import GDPRService
        service = GDPRService(request.user)
        anonymization_results = service.delete_user_data_anonymized()
        
        return Response({
            'success': True,
            'message': 'User data anonymized successfully',
            'data': anonymization_results,
        })
    except Exception as e:
        logger.error("anonymize_user_data_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GDPRDataExportViewSet(APIView):
    """Viewset for GDPR data export."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Export user data."""
        try:
            from .gdpr_service import GDPRService
            service = GDPRService(request.user)
            export_data = service.export_user_data()
            # Flatten the response to provide top-level keys expected by clients
            categories = export_data.get('data_categories', {})
            user_info = {
                'id': export_data.get('user_id'),
                'email': export_data.get('email'),
                'created_at': export_data.get('created_at'),
                'last_login': export_data.get('last_login'),
            }
            response_data = {
                'success': True,
                'data': export_data,
                'user': user_info,
                'career_profile': categories.get('career_profile'),
                'career_goals': categories.get('career_goals', []),
                'career_learning': categories.get('learning_history', []),
                'career_brain': categories.get('career_brain'),
                'talent_scores': categories.get('talent_scores'),
                'interview_sessions': categories.get('interview_sessions', []),
                'user_skills': categories.get('user_skills', []),
                'job_applications': categories.get('job_applications', []),
                'export_date': export_data.get('export_date'),
            }
            return Response(response_data)
        except Exception as e:
            logger.error("export_user_data_failed", error=str(e))
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GDPRDataDeletionViewSet(APIView):
    """Viewset for GDPR data deletion."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Delete user data."""
        try:
            from .gdpr_service import GDPRService
            service = GDPRService(request.user)
            deletion_results = service.delete_user_data()
            return Response({'success': True, 'message': 'User data deleted successfully', 'data': deletion_results})
        except Exception as e:
            logger.error("delete_user_data_failed", error=str(e))
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GDPRDataAnonymizationViewSet(APIView):
    """Viewset for GDPR data anonymization."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Anonymize user data."""
        try:
            from .gdpr_service import GDPRService
            service = GDPRService(request.user)
            anonymization_results = service.delete_user_data_anonymized()
            return Response({'success': True, 'message': 'User data anonymized successfully', 'data': anonymization_results})
        except Exception as e:
            logger.error("anonymize_user_data_failed", error=str(e))
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
