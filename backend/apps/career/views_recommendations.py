"""
Recommendation API views.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .recommendation_engine import recommendation_engine


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """
    Get personalized job recommendations for the authenticated user.

    GET /api/v1/career/recommendations/?limit=20

    Returns hybrid recommendations combining:
    - Content-based matching (skills, roles, location)
    - Collaborative filtering (similar users' behavior)
    - Recency boost for new postings
    """
    limit = int(request.query_params.get('limit', 20))
    limit = min(limit, 50)

    recommendations = recommendation_engine.get_recommendations(request.user, limit=limit)

    return Response({
        'success': True,
        'count': len(recommendations),
        'data': recommendations,
    })
