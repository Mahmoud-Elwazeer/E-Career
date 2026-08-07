"""
Career Intelligence Views

This module contains API views for:
- Talent score retrieval and calculation
- Score breakdowns and explanations
- Score trends and history
"""

from __future__ import annotations

import structlog
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.career.scoring_engine import ScoringEngine
from apps.career.models import TalentScore, CareerProfile, CareerUserSkill, CareerLearning, InterviewSession, CareerBrain
from apps.career.serializers import (
    TalentScoreSerializer,
    ScoreBreakdownSerializer,
    ScoreTrendSerializer,
    CareerBrainSerializer,
)

logger = structlog.get_logger()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_talent_scores(request):
    """
    Get all talent scores for the authenticated user.
    
    Returns:
        - All 8 dimension scores with breakdowns
        - Explanations for each dimension
        - Recommended actions
        - Historical trends
    """
    try:
        # Get or create talent score
        talent_score, created = TalentScore.objects.get_or_create(
            user=request.user,
            defaults={
                'overall_score': 0.0,
                'skill_score': 0.0,
                'experience_score': 0.0,
                'education_score': 0.0,
                'portfolio_score': 0.0,
                'interview_score': 0.0,
                'growth_score': 0.0,
                'communication_score': 0.0,
                'ai_confidence': 0.5,
            }
        )
        
        # Calculate scores if not already calculated
        if created or talent_score.overall_score == 0.0:
            engine = ScoringEngine(request.user)
            result = engine.calculate_and_save()
            talent_score.refresh_from_db()
        
        serializer = TalentScoreSerializer(talent_score)
        
        return Response({
            "success": True,
            "data": serializer.data,
        })
        
    except Exception as e:
        logger.error("get_talent_scores_failed", error=str(e))
        return Response({
            "success": False,
            "error": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_score_breakdown(request, dimension: str):
    """
    Get detailed breakdown for a specific score dimension.
    
    Dimensions:
    - skill_score
    - experience_score
    - education_score
    - portfolio_score
    - growth_score
    - communication_score
    - interview_score
    - ai_confidence
    
    Args:
        dimension: The score dimension to breakdown
        
    Returns:
        - Score value
        - Confidence level
        - Grade (A-F)
        - Evidence items
        - Explanation
        - Recommended actions
        - Sub-factor breakdown
    """
    valid_dimensions = [
        'skill_score', 'experience_score', 'education_score',
        'portfolio_score', 'growth_score', 'communication_score',
        'interview_score', 'ai_confidence'
    ]
    
    if dimension not in valid_dimensions:
        return Response({
            "success": False,
            "error": f"Invalid dimension. Must be one of: {', '.join(valid_dimensions)}",
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        engine = ScoringEngine(request.user)
        
        # Get the appropriate calculation method
        method_map = {
            'skill_score': engine.calculate_skill_score,
            'experience_score': engine.calculate_experience_score,
            'education_score': engine.calculate_education_score,
            'portfolio_score': engine.calculate_portfolio_score,
            'growth_score': engine.calculate_growth_score,
            'communication_score': engine.calculate_communication_score,
            'interview_score': engine.calculate_interview_score,
            'ai_confidence': engine.calculate_ai_confidence,
        }
        
        result = method_map[dimension]()
        
        return Response({
            "success": True,
            "data": result.to_dict(),
        })
        
    except Exception as e:
        logger.error("get_score_breakdown_failed", dimension=dimension, error=str(e))
        return Response({
            "success": False,
            "error": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_score_trends(request):
    """
    Get score trends over time.
    
    Returns:
        - Historical score data
        - Trend direction (improving/stable/declining)
        - Score changes by dimension
    """
    try:
        # Get talent score history
        talent_score = TalentScore.objects.filter(user=request.user).first()
        
        if not talent_score or not talent_score.score_history:
            return Response({
                "success": True,
                "data": {
                    "trends": [],
                    "current_scores": {},
                    "trend_direction": "insufficient_data",
                }
            })
        
        # Calculate trends
        history = talent_score.score_history
        if len(history) < 2:
            return Response({
                "success": True,
                "data": {
                    "trends": history,
                    "current_scores": history[-1].get("dimensions", {}) if history else {},
                    "trend_direction": "insufficient_data",
                }
            })
        
        # Calculate trend for each dimension
        current = history[-1]
        previous = history[-2]
        
        trends = []
        for dim in current.get("dimensions", {}):
            current_val = current["dimensions"][dim]
            prev_val = previous.get("dimensions", {}).get(dim, current_val)
            
            if current_val > prev_val + 0.05:
                direction = "improving"
            elif current_val < prev_val - 0.05:
                direction = "declining"
            else:
                direction = "stable"
            
            trends.append({
                "dimension": dim,
                "current_value": current_val,
                "previous_value": prev_val,
                "change": round(current_val - prev_val, 3),
                "direction": direction,
            })
        
        # Determine overall trend
        improving_count = sum(1 for t in trends if t["direction"] == "improving")
        declining_count = sum(1 for t in trends if t["direction"] == "declining")
        
        if improving_count > declining_count + 2:
            overall_trend = "improving"
        elif declining_count > improving_count + 2:
            overall_trend = "declining"
        else:
            overall_trend = "stable"
        
        return Response({
            "success": True,
            "data": {
                "trends": history,
                "current_scores": current.get("dimensions", {}),
                "trend_direction": overall_trend,
                "dimension_trends": trends,
            }
        })
        
    except Exception as e:
        logger.error("get_score_trends_failed", error=str(e))
        return Response({
            "success": False,
            "error": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recalculate_scores(request):
    """
    Trigger recalculation of all talent scores.
    
    This is an async operation - scores will be recalculated in the background.
    
    Returns:
        - Task status
        - Estimated completion time
    """
    try:
        from apps.career.tasks import recalculate_talent_score
        
        # Trigger background task
        recalculate_talent_score.delay(request.user.id)
        
        return Response({
            "success": True,
            "message": "Score recalculation started. You will receive a notification when complete.",
        })
        
    except Exception as e:
        logger.error("recalculate_scores_failed", error=str(e))
        return Response({
            "success": False,
            "error": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_scores_with_actions(request):
    """
    Get all scores with recommended actions.
    
    Returns:
        - All 8 dimension scores
        - Explanations
        - Recommended actions for improvement
        - Priority ranking
    """
    try:
        engine = ScoringEngine(request.user)
        all_scores = engine.calculate_all_scores()
        composite_result = engine.calculate_composite_score()
        
        # Collect all actions
        all_actions = []
        for dimension, result in all_scores.items():
            for action in result.actions:
                action["dimension"] = dimension
                all_actions.append(action)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        all_actions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
        
        return Response({
            "success": True,
            "data": {
                "overall_score": composite_result.value,
                "overall_grade": composite_result.grade,
                "dimensions": {
                    k: v.to_dict() for k, v in all_scores.items()
                },
                "explanations": engine._build_explanations(all_scores),
                "actions": all_actions,
                "confidence": composite_result.confidence,
            }
        })
        
    except Exception as e:
        logger.error("get_all_scores_with_actions_failed", error=str(e))
        return Response({
            "success": False,
            "error": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TalentScoreViewSet(APIView):
    """
    ViewSet for managing talent scores.
    
    Actions:
    - GET: Retrieve all scores
    - POST: Trigger recalculation
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all talent scores."""
        return get_talent_scores(request)
    
    def post(self, request):
        """Trigger score recalculation."""
        return recalculate_scores(request)


class ScoreBreakdownViewSet(APIView):
    """
    ViewSet for score breakdowns.
    
    Actions:
    - GET: Get detailed breakdown for a dimension
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, dimension=None):
        """Get breakdown for a specific dimension."""
        if not dimension:
            return Response({
                "success": False,
                "error": "Dimension parameter required",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return get_score_breakdown(request, dimension)


class ScoreTrendsViewSet(APIView):
    """
    ViewSet for score trends.
    
    Actions:
    - GET: Get historical trends
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get score trends."""
        return get_score_trends(request)


class CareerBrainView(APIView):
    """
    Career Brain API endpoint.
    
    Provides access to the user's career context and memory.
    
    Actions:
    - GET: Get career brain data
    - POST: Update career brain data
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get career brain for the authenticated user."""
        from apps.career.models import CareerBrain
        from apps.career.serializers import CareerBrainSerializer
        
        try:
            career_brain = CareerBrain.objects.get(user=request.user)
            serializer = CareerBrainSerializer(career_brain)
            return Response(serializer.data)
        except CareerBrain.DoesNotExist:
            return Response(
                {'error': 'Career brain not found. Please complete your profile first.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Update career brain for the authenticated user."""
        from apps.career.models import CareerBrain
        from apps.career.serializers import CareerBrainSerializer
        
        career_brain, created = CareerBrain.objects.get_or_create(user=request.user)
        serializer = CareerBrainSerializer(career_brain, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)


# ============================================================================
# Profile Completeness API
# ============================================================================


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_completeness(request):
    """
    Get profile completeness score for the authenticated user.
    
    Returns:
        - Overall completeness score (0-100)
        - Breakdown by dimension
        - Missing fields
        - Recommendations
    """
    try:
        from apps.career.completeness_calculator import calculate_profile_completeness
        
        career_profile = request.user.career_profile
        result = calculate_profile_completeness(career_profile)
        
        return Response({
            'success': True,
            'data': result,
        })
    except Exception as e:
        logger.error("get_profile_completeness_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recalculate_profile_completeness(request):
    """
    Recalculate and update profile completeness score.
    
    Returns:
        - Updated completeness score
    """
    try:
        from apps.career.completeness_calculator import calculate_profile_completeness
        
        career_profile = request.user.career_profile
        result = calculate_profile_completeness(career_profile)
        
        # Update the profile's completeness score
        career_profile.completeness_score = result['score'] / 100.0
        career_profile.save(update_fields=['completeness_score'])
        
        return Response({
            'success': True,
            'data': result,
        })
    except Exception as e:
        logger.error("recalculate_profile_completeness_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Skill Gap Analysis API
# ============================================================================


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_gap_analysis(request):
    """
    Get skill gap analysis for the authenticated user.
    
    Returns:
        - Overall gap score
        - Gaps by target role
        - Missing skills
        - Recommendations
    """
    try:
        from apps.career.skill_gap_analysis import analyze_skill_gaps
        
        result = analyze_skill_gaps(request.user)
        
        return Response({
            'success': True,
            'data': result,
        })
    except Exception as e:
        logger.error("get_skill_gap_analysis_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
