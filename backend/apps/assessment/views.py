"""
Assessment Platform Views

This module contains Django REST Framework views for assessments, questions, and results.
"""

import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.code_execution import execute_and_grade

from .models import (
    Assessment,
    AssessmentQuestion,
    AssessmentAttempt,
    SkillBadge,
    AssessmentTemplate,
    AssessmentResult,
)
from .serializers import (
    AssessmentSerializer,
    AssessmentCreateSerializer,
    AssessmentQuestionSerializer,
    AssessmentAttemptSerializer,
    AssessmentAttemptCreateSerializer,
    SkillBadgeSerializer,
    AssessmentTemplateSerializer,
    AssessmentResultSerializer,
    AssessmentSubmitSerializer,
    SkillBadgeRequestSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_assessments(request):
    """
    Get assessments for the authenticated user.
    """
    try:
        assessments = Assessment.objects.filter(created_by=request.user)
        return Response({
            'success': True,
            'data': AssessmentSerializer(assessments, many=True).data,
        })
    except Exception as e:
        logger.error("get_user_assessments_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assessment_attempts(request):
    """
    Get assessment attempts for the authenticated user.
    """
    try:
        attempts = AssessmentAttempt.objects.filter(user=request.user).select_related('assessment')
        return Response({
            'success': True,
            'data': AssessmentAttemptSerializer(attempts, many=True).data,
        })
    except Exception as e:
        logger.error("get_assessment_attempts_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_assessment(request):
    """
    Start a new assessment attempt.
    """
    try:
        serializer = AssessmentAttemptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        assessment = serializer.validated_data['assessment']
        
        # Get or create attempt
        attempt, created = AssessmentAttempt.objects.get_or_create(
            user=request.user,
            assessment=assessment,
            attempt_number=1,
            defaults={
                'status': 'in_progress',
                'started_at': timezone.now(),
            }
        )
        
        return Response({
            'success': True,
            'data': AssessmentAttemptSerializer(attempt).data,
        })
    except Exception as e:
        logger.error("start_assessment_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_assessment(request, attempt_id):
    """
    Submit an assessment attempt.
    """
    try:
        attempt = AssessmentAttempt.objects.get(id=attempt_id, user=request.user)
        
        serializer = AssessmentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        answers = serializer.validated_data['answers']
        time_spent = serializer.validated_data.get('time_spent_minutes', 0)
        
        # Calculate score with real grading
        total_questions = attempt.assessment.questions.count()
        correct_answers = 0
        question_scores = {}
        coding_details = {}

        for question in attempt.assessment.questions.all():
            question_id = str(question.id)
            if question_id in answers:
                user_answer = answers[question_id]
                if question.question_type == 'multiple_choice':
                    if user_answer == question.correct_answer:
                        correct_answers += 1
                        question_scores[question_id] = 100
                    else:
                        question_scores[question_id] = 0
                elif question.question_type == 'coding':
                    # Real code execution and grading via Judge0
                    code = user_answer if isinstance(user_answer, str) else user_answer.get('code', '')
                    language = (
                        user_answer.get('language', 'python')
                        if isinstance(user_answer, dict)
                        else 'python'
                    )
                    test_cases = question.test_cases or []
                    try:
                        grading_result = execute_and_grade(code, language, test_cases)
                        coding_details[question_id] = grading_result
                        # Award full point if all tests pass, partial otherwise
                        question_scores[question_id] = int(grading_result['score'] * 100)
                        if grading_result['passed']:
                            correct_answers += 1
                        else:
                            # Partial credit: count as correct if >= 50% tests pass
                            if grading_result['score'] >= 0.5:
                                correct_answers += grading_result['score']
                    except Exception as grading_err:
                        logger.error(f"Coding grading failed for question {question_id}: {grading_err}")
                        question_scores[question_id] = 0
                else:
                    question_scores[question_id] = 0
            else:
                question_scores[question_id] = 0

        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
        passed = score >= attempt.assessment.passing_score
        
        # Update attempt
        attempt.answers = answers
        attempt.score = score
        attempt.passed = passed
        attempt.status = 'graded'
        attempt.submitted_at = timezone.now()
        attempt.time_spent_minutes = time_spent
        attempt.save()
        
        # Generate AI-powered analysis of the submission
        try:
            from apps.intelligence.career_ai import career_ai_service
            ai_analysis = career_ai_service.generate_assessment_feedback(
                answers=answers,
                scores=question_scores,
                coding_details=coding_details,
                passed=passed,
                overall_score=score,
            )
        except Exception as ai_err:
            logger.warning(f"AI analysis generation failed, using fallback: {ai_err}")
            ai_analysis = {
                'strengths': ['Problem solving', 'Technical knowledge'] if passed else ['Attempted all questions'],
                'weaknesses': ['Time management'] if time_spent > 60 else [],
                'recommendations': ['Practice more coding challenges'] if not passed else ['Keep up the good work'],
                'summary': f"Score: {score}%. {'Passed' if passed else 'Did not pass'}.",
            }

        # Create result
        AssessmentResult.objects.create(
            attempt=attempt,
            total_score=score,
            max_score=100,
            question_scores=question_scores,
            time_per_question={str(q.id): time_spent // max(total_questions, 1) for q in attempt.assessment.questions.all()},
            ai_analysis=ai_analysis,
        )
        
        return Response({
            'success': True,
            'data': {
                'attempt_id': str(attempt.id),
                'score': score,
                'passed': passed,
                'total_questions': total_questions,
                'correct_answers': correct_answers,
            },
        })
    except AssessmentAttempt.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Assessment attempt not found',
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("submit_assessment_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_badges(request):
    """
    Get skill badges for the authenticated user.
    """
    try:
        badges = SkillBadge.objects.filter(user=request.user).select_related('skill')
        return Response({
            'success': True,
            'data': SkillBadgeSerializer(badges, many=True).data,
        })
    except Exception as e:
        logger.error("get_skill_badges_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_skill_badge(request):
    """
    Create a skill badge for the authenticated user.
    """
    try:
        serializer = SkillBadgeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        skill_id = serializer.validated_data['skill_id']
        level = serializer.validated_data.get('level', 'verified')
        
        # Create badge
        badge = SkillBadge.objects.create(
            user=request.user,
            skill_id=skill_id,
            level=level,
            verification_method='assessment',
            score=serializer.validated_data.get('score', 100),
        )
        
        return Response({
            'success': True,
            'data': SkillBadgeSerializer(badge).data,
        })
    except Exception as e:
        logger.error("create_skill_badge_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_assessment_templates(request):
    """
    Get assessment templates (public).
    """
    try:
        templates = AssessmentTemplate.objects.filter(status='public')
        return Response({
            'success': True,
            'data': AssessmentTemplateSerializer(templates, many=True).data,
        })
    except Exception as e:
        logger.error("get_assessment_templates_failed", error=str(e))
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssessmentViewSet(APIView):
    """Viewset for Assessment model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get assessments."""
        try:
            assessments = Assessment.objects.filter(created_by=request.user)
            return Response({
                'success': True,
                'data': AssessmentSerializer(assessments, many=True).data,
            })
        except Exception as e:
            logger.error("get_assessments_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create assessment."""
        try:
            serializer = AssessmentCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            assessment = Assessment.objects.create(
                created_by=request.user,
                **serializer.validated_data
            )
            
            return Response({
                'success': True,
                'data': AssessmentSerializer(assessment).data,
            })
        except Exception as e:
            logger.error("create_assessment_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssessmentQuestionViewSet(APIView):
    """Viewset for AssessmentQuestion model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get assessment questions."""
        try:
            questions = AssessmentQuestion.objects.filter(assessment__created_by=request.user)
            return Response({
                'success': True,
                'data': AssessmentQuestionSerializer(questions, many=True).data,
            })
        except Exception as e:
            logger.error("get_assessment_questions_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssessmentAttemptViewSet(APIView):
    """Viewset for AssessmentAttempt model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get assessment attempts."""
        try:
            attempts = AssessmentAttempt.objects.filter(user=request.user)
            return Response({
                'success': True,
                'data': AssessmentAttemptSerializer(attempts, many=True).data,
            })
        except Exception as e:
            logger.error("get_assessment_attempts_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SkillBadgeViewSet(APIView):
    """Viewset for SkillBadge model."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get skill badges."""
        try:
            badges = SkillBadge.objects.filter(user=request.user)
            return Response({
                'success': True,
                'data': SkillBadgeSerializer(badges, many=True).data,
            })
        except Exception as e:
            logger.error("get_skill_badges_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssessmentTemplateViewSet(APIView):
    """Viewset for AssessmentTemplate model."""
    
    def get(self, request):
        """Get assessment templates."""
        try:
            templates = AssessmentTemplate.objects.filter(status='public')
            return Response({
                'success': True,
                'data': AssessmentTemplateSerializer(templates, many=True).data,
            })
        except Exception as e:
            logger.error("get_assessment_templates_failed", error=str(e))
            return Response({
                'success': False,
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)