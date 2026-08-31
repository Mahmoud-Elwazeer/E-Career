"""
Recommendation API views.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.search.recommendation_engine import get_recommendation_engine


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

    engine = get_recommendation_engine(request.user)
    recommendations = engine.get_recommendations(n_recommendations=limit)

    return Response({
        'success': True,
        'data': {
            'count': len(recommendations),
            'recommendations': recommendations,
        },
    })
