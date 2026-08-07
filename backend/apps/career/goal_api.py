"""
Career Goal Setting API

Provides REST API endpoints for managing career goals and actions.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import date

from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.career.models import CareerGoal, CareerGoalAction
from apps.career.serializers import (
    CareerGoalSerializer,
    CareerGoalActionSerializer,
    CareerGoalCreateSerializer,
    CareerGoalActionCreateSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=["Career Goals"])
class CareerGoalListCreateView(APIView):
    """
    GET /api/v1/career/goals/
    POST /api/v1/career/goals/
    
    List and create career goals.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all goals for the current user."""
        goals = CareerGoal.objects.filter(user=request.user).order_by('-created_at')
        serializer = CareerGoalSerializer(goals, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new career goal."""
        serializer = CareerGoalCreateSerializer(
            data=request.data,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        goal = serializer.save()
        
        return Response(
            CareerGoalSerializer(goal).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Career Goals"])
class CareerGoalDetailView(APIView):
    """
    GET /api/v1/career/goals/{id}/
    PUT /api/v1/career/goals/{id}/
    PATCH /api/v1/career/goals/{id}/
    DELETE /api/v1/career/goals/{id}/
    
    Retrieve, update, or delete a specific career goal.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk: str, user) -> Optional[CareerGoal]:
        """Get goal by ID, ensuring ownership."""
        try:
            return CareerGoal.objects.get(pk=pk, user=user)
        except CareerGoal.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """Retrieve a specific goal."""
        goal = self.get_object(pk, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CareerGoalSerializer(goal)
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Update a goal (full update)."""
        goal = self.get_object(pk, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CareerGoalSerializer(
            goal,
            data=request.data,
            partial=False,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        goal = serializer.save()
        
        return Response(CareerGoalSerializer(goal).data)
    
    def patch(self, request, pk):
        """Update a goal (partial update)."""
        goal = self.get_object(pk, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CareerGoalSerializer(
            goal,
            data=request.data,
            partial=True,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        goal = serializer.save()
        
        return Response(CareerGoalSerializer(goal).data)
    
    def delete(self, request, pk):
        """Delete a goal."""
        goal = self.get_object(pk, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        goal.delete()
        return Response(
            {'message': 'Goal deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(tags=["Career Goals"])
class CareerGoalActionListCreateView(APIView):
    """
    GET /api/v1/career/goals/{goal_id}/actions/
    POST /api/v1/career/goals/{goal_id}/actions/
    
    List and create actions for a specific goal.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_goal(self, goal_id: str, user) -> Optional[CareerGoal]:
        """Get goal by ID, ensuring ownership."""
        try:
            return CareerGoal.objects.get(pk=goal_id, user=user)
        except CareerGoal.DoesNotExist:
            return None
    
    def get(self, request, goal_id):
        """List all actions for a goal."""
        goal = self.get_goal(goal_id, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        actions = goal.actions.all().order_by('due_date', '-created_at')
        serializer = CareerGoalActionSerializer(actions, many=True)
        return Response(serializer.data)
    
    def post(self, request, goal_id):
        """Create a new action for a goal."""
        goal = self.get_goal(goal_id, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CareerGoalActionCreateSerializer(
            data={**request.data, 'goal': goal.id},
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        action = serializer.save()
        
        return Response(
            CareerGoalActionSerializer(action).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Career Goals"])
class CareerGoalActionDetailView(APIView):
    """
    GET /api/v1/career/goals/{goal_id}/actions/{id}/
    PUT /api/v1/career/goals/{goal_id}/actions/{id}/
    PATCH /api/v1/career/goals/{goal_id}/actions/{id}/
    DELETE /api/v1/career/goals/{goal_id}/actions/{id}/
    
    Retrieve, update, or delete a specific action.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_goal(self, goal_id: str, user) -> Optional[CareerGoal]:
        """Get goal by ID, ensuring ownership."""
        try:
            return CareerGoal.objects.get(pk=goal_id, user=user)
        except CareerGoal.DoesNotExist:
            return None
    
    def get_action(self, action_id: str, goal: CareerGoal) -> Optional[CareerGoalAction]:
        """Get action by ID, ensuring it belongs to the goal."""
        try:
            return CareerGoalAction.objects.get(pk=action_id, goal=goal)
        except CareerGoalAction.DoesNotExist:
            return None
    
    def get(self, request, goal_id, action_id):
        """Retrieve a specific action."""
        goal = self.get_goal(goal_id, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        action = self.get_action(action_id, goal)
        if not action:
            return Response(
                {'error': 'Action not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CareerGoalActionSerializer(action)
        return Response(serializer.data)
    
    def put(self, request, goal_id, action_id):
        """Update an action (full update)."""
        goal = self.get_goal(goal_id, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        action = self.get_action(action_id, goal)
        if not action:
            return Response(
                {'error': 'Action not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CareerGoalActionSerializer(
            action,
            data=request.data,
            partial=False,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        action = serializer.save()
        
        return Response(CareerGoalActionSerializer(action).data)
    
    def patch(self, request, goal_id, action_id):
        """Update an action (partial update)."""
        goal = self.get_goal(goal_id, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        action = self.get_action(action_id, goal)
        if not action:
            return Response(
                {'error': 'Action not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CareerGoalActionSerializer(
            action,
            data=request.data,
            partial=True,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        action = serializer.save()
        
        return Response(CareerGoalActionSerializer(action).data)
    
    def delete(self, request, goal_id, action_id):
        """Delete an action."""
        goal = self.get_goal(goal_id, request.user)
        if not goal:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        action = self.get_action(action_id, goal)
        if not action:
            return Response(
                {'error': 'Action not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        action.delete()
        return Response(
            {'message': 'Action deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(tags=["Career Goals"])
class CareerGoalMilestoneView(APIView):
    """
    POST /api/v1/career/goals/{goal_id}/milestones/
    
    Add a milestone to a goal.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, goal_id):
        """Add a new milestone to a goal."""
        try:
            goal = CareerGoal.objects.get(pk=goal_id, user=request.user)
        except CareerGoal.DoesNotExist:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        title = request.data.get('title')
        due_date = request.data.get('due_date')
        
        if not title:
            return Response(
                {'error': 'Title is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse due_date if provided
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = date.fromisoformat(due_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        milestone = goal.add_milestone(title, due_date_obj)
        
        return Response(
            {'message': 'Milestone added', 'milestone': milestone},
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Career Goals"])
class CareerGoalCompleteMilestoneView(APIView):
    """
    POST /api/v1/career/goals/{goal_id}/milestones/{milestone_id}/complete/
    
    Mark a milestone as completed.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, goal_id, milestone_id):
        """Mark a milestone as completed."""
        try:
            goal = CareerGoal.objects.get(pk=goal_id, user=request.user)
        except CareerGoal.DoesNotExist:
            return Response(
                {'error': 'Goal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if goal.complete_milestone(milestone_id):
            return Response(
                {'message': 'Milestone completed'}
            )
        else:
            return Response(
                {'error': 'Milestone not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(tags=["Career Goals"])
class CareerGoalProgressView(APIView):
    """
    GET /api/v1/career/goals/progress/
    
    Get overall progress across all goals.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get progress summary for all goals."""
        goals = CareerGoal.objects.filter(user=request.user)
        
        total = goals.count()
        active = goals.filter(status='active').count()
        in_progress = goals.filter(status='in_progress').count()
        completed = goals.filter(status='completed').count()
        
        # Calculate average progress
        avg_progress = 0
        if total > 0:
            avg_progress = sum(g.progress for g in goals) / total
        
        # Get upcoming deadlines
        from datetime import timedelta
        upcoming = goals.filter(
            status__in=['active', 'in_progress'],
            target_date__gte=timezone.now().date(),
            target_date__lte=timezone.now().date() + timedelta(days=30)
        ).order_by('target_date')[:5]
        
        return Response({
            'total': total,
            'active': active,
            'in_progress': in_progress,
            'completed': completed,
            'avg_progress': round(avg_progress, 1),
            'upcoming_deadlines': [
                {
                    'id': g.id,
                    'title': g.title,
                    'target_date': g.target_date.isoformat() if g.target_date else None,
                    'progress': g.progress,
                }
                for g in upcoming
            ],
        })


@extend_schema(tags=["Career Goals"])
class CareerGoalAnalyticsView(APIView):
    """
    GET /api/v1/career/goals/analytics/
    
    Get analytics for goal completion patterns.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get goal analytics."""
        from django.db.models import Avg, Count, Q
        from datetime import timedelta
        
        goals = CareerGoal.objects.filter(user=request.user)
        
        # Completion rate by type
        type_stats = goals.values('goal_type').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            avg_progress=Avg('progress')
        )
        
        # Completion rate by priority
        priority_stats = goals.values('priority').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            avg_progress=Avg('progress')
        )
        
        # Time to completion (for completed goals)
        completed_goals = goals.filter(status='completed', completed_at__isnull=False)
        avg_completion_days = None
        if completed_goals.exists():
            from django.db.models import F
            from django.db.models.functions import ExtractDay
            days_to_complete = completed_goals.annotate(
                days=ExtractDay(F('completed_at') - F('created_at'))
            ).aggregate(avg_days=Avg('days'))
            avg_completion_days = days_to_complete['avg_days']
        
        return Response({
            'by_type': {s['goal_type']: {
                'total': s['total'],
                'completed': s['completed'],
                'completion_rate': round(s['completed'] / s['total'] * 100, 1) if s['total'] > 0 else 0,
                'avg_progress': round(s['avg_progress'] or 0, 1),
            } for s in type_stats},
            'by_priority': {s['priority']: {
                'total': s['total'],
                'completed': s['completed'],
                'completion_rate': round(s['completed'] / s['total'] * 100, 1) if s['total'] > 0 else 0,
                'avg_progress': round(s['avg_progress'] or 0, 1),
            } for s in priority_stats},
            'avg_completion_days': round(avg_completion_days, 1) if avg_completion_days else None,
        })