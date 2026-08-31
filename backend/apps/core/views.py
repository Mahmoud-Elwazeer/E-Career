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

            code = serializer.validated_data['code']

            import requests as http_requests
            from django.conf import settings as django_settings

            client_id = getattr(django_settings, 'GITHUB_CLIENT_ID', '') or ''
            client_secret = getattr(django_settings, 'GITHUB_CLIENT_SECRET', '') or ''
            if not client_id or not client_secret:
                return Response({
                    'success': False,
                    'error': 'GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.',
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            token_resp = http_requests.post(
                'https://github.com/login/oauth/access_token',
                json={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code,
                },
                headers={'Accept': 'application/json'},
                timeout=15,
            )
            token_data = token_resp.json()
            access_token = token_data.get('access_token')
            if not access_token:
                return Response({
                    'success': False,
                    'error': token_data.get('error_description', 'Failed to obtain GitHub access token'),
                }, status=status.HTTP_400_BAD_REQUEST)

            gh_user_resp = http_requests.get(
                'https://api.github.com/user',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/vnd.github+json',
                },
                timeout=15,
            )
            gh_user = gh_user_resp.json()

            conn, created = GitHubConnection.objects.update_or_create(
                github_id=str(gh_user['id']),
                defaults={
                    'user': request.user,
                    'username': gh_user.get('login', ''),
                    'access_token': access_token,
                    'refresh_token': token_data.get('refresh_token', ''),
                    'avatar_url': gh_user.get('avatar_url', ''),
                    'profile_url': gh_user.get('html_url', ''),
                    'email': gh_user.get('email', '') or '',
                    'name': gh_user.get('name', '') or '',
                },
            )

            return Response({
                'success': True,
                'data': GitHubConnectionSerializer(conn).data,
                'created': created,
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
            
            analysis = PortfolioAnalysis.objects.create(
                user=request.user,
                url=url,
                status='analyzing',
            )

            import requests as http_requests
            try:
                page_resp = http_requests.get(url, timeout=15, headers={
                    'User-Agent': 'E-Career Portfolio Analyzer/1.0',
                })
                page_text = page_resp.text[:8000]
            except Exception:
                page_text = f"(Could not fetch {url})"

            try:
                from apps.intelligence.career_ai import career_ai_service as bedrock_service
                prompt = (
                    f"Analyze this portfolio/project page and provide a professional assessment.\n"
                    f"URL: {url}\n\nPage content (truncated):\n{page_text}\n\n"
                    f"Return a JSON object with keys: summary (2-3 sentences), "
                    f"strengths (list of strings), improvements (list of strings), "
                    f"technologies_detected (list of strings), overall_score (1-10)."
                )
                ai_result = bedrock_service.invoke_model(
                    prompt=prompt,
                    system_prompt="You are a technical portfolio reviewer. Return valid JSON only.",
                    max_tokens=1500,
                    temperature=0.3,
                )
                import json
                try:
                    result_data = json.loads(ai_result)
                except (json.JSONDecodeError, TypeError):
                    result_data = {"summary": ai_result, "overall_score": None}

                analysis.status = 'completed'
                analysis.technologies = result_data.get('technologies_detected', [])
                analysis.tech_stack = {
                    'strengths': result_data.get('strengths', []),
                    'improvements': result_data.get('improvements', []),
                }
                score = result_data.get('overall_score')
                if score is not None:
                    analysis.quality_score = min(float(score) / 10.0, 1.0)
                analysis.observations = {
                    'summary': result_data.get('summary', ''),
                    'raw': result_data,
                }
                analysis.save()
            except Exception as exc:
                logger.warning("portfolio_analysis_ai_failed", error=str(exc))
                analysis.status = 'completed'
                analysis.observations = {
                    'summary': f"Portfolio at {url} was recorded. AI analysis unavailable — "
                               "ensure AWS Bedrock model access is configured.",
                }
                analysis.save()

            return Response({
                'success': True,
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
