"""
Interviews API Views
"""
import base64
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import InterviewSession, InterviewQuestion
from .serializers import (
    InterviewSessionSerializer,
    StartInterviewSerializer,
    AnswerQuestionSerializer,
    CompleteInterviewSerializer,
    InterviewHistorySerializer,
    InterviewQuestionSerializer
)
from .service import interview_service
from .voice_service import voice_interview_service

logger = logging.getLogger(__name__)


class InterviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing interview sessions.
    
    list: Get all user's interview sessions
    retrieve: Get a specific interview session with questions
    create: Start a new interview session
    destroy: Delete an interview session
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = InterviewSessionSerializer
    
    def get_queryset(self):
        return InterviewSession.objects.filter(
            user=self.request.user
        ).order_by('-started_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """
        Start a new interview session.
        
        POST /api/v1/interviews/start/
        {
            "interview_type": "technical",
            "target_role": "Software Engineer",
            "difficulty": "medium",
            "mode": "text"
        }
        """
        serializer = StartInterviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interview_type = serializer.validated_data['interview_type']
        target_role = serializer.validated_data['target_role']
        difficulty = serializer.validated_data.get('difficulty', 'medium')
        mode = serializer.validated_data.get('mode', 'text')
        job_id = serializer.validated_data.get('job_id')

        # Build user context
        user_context = self._build_user_context(request.user)

        # If job_id provided, add job context (F5)
        job_context = None
        if job_id:
            from apps.jobs.models import Job
            job = get_object_or_404(Job, id=job_id)
            job_context = f"Job: {job.title} at {job.company.name}\nRequirements: {job.requirements[:300] if job.requirements else job.description[:300]}"

        # Generate questions
        questions = interview_service.generate_questions(
            interview_type=interview_type,
            target_role=target_role,
            difficulty=difficulty,
            user_context=user_context,
            job_context=job_context
        )
        
        # Create session
        session = InterviewSession.objects.create(
            user=request.user,
            interview_type=interview_type,
            target_role=target_role,
            difficulty=difficulty,
            mode=mode,
            status='in_progress'
        )
        
        # Create questions
        for idx, q_data in enumerate(questions, start=1):
            InterviewQuestion.objects.create(
                session=session,
                question_index=idx,
                question_text=q_data.get('question', ''),
                score_details={'evaluation_criteria': q_data.get('evaluation_criteria', '')}
            )
        
        # Notify user that their interview session has started
        try:
            from apps.notifications.service import create_and_deliver_notification
            create_and_deliver_notification(
                user=request.user,
                notification_type='system',
                title='Interview Session Started',
                message=f'Your {interview_type} interview for {target_role} ({difficulty}) has started. Good luck!',
                related_id=str(session.id),
                related_type='interview_session',
                priority='medium',
            )
        except Exception as notif_err:
            logger.warning(f"Failed to create interview start notification: {notif_err}")

        # Get first question
        first_question = session.questions.first()

        return Response({
            'session_id': session.id,
            'interview_type': session.interview_type,
            'target_role': session.target_role,
            'difficulty': session.difficulty,
            'question_count': session.questions.count(),
            'current_question': {
                'id': first_question.id,
                'index': first_question.question_index,
                'question': first_question.question_text
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        """
        Submit an answer for the current question.
        
        POST /api/v1/interviews/{id}/answer/
        {
            "answer": "My answer text here..."
        }
        """
        session = self.get_object()
        
        # Get current question (first unanswered or first question)
        current_question = session.questions.filter(answer_text='').first()
        if not current_question:
            return Response({
                'error': 'All questions answered. Complete the session.',
                'session_id': session.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AnswerQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        answer = serializer.validated_data['answer']
        
        # Save answer
        current_question.answer_text = answer
        current_question.answered_at = timezone.now()
        current_question.save()
        
        # Evaluate answer
        evaluation = interview_service.evaluate_answer(
            question=current_question.question_text,
            answer=answer,
            interview_type=session.interview_type,
            target_role=session.target_role
        )
        
        # Update question with score
        current_question.score = evaluation.get('score', 0)
        current_question.feedback = evaluation.get('feedback', '')
        current_question.score_details = evaluation
        current_question.save()
        
        # Get next question
        next_question = session.questions.filter(answer_text='').first()
        
        return Response({
            'session_id': session.id,
            'question_index': current_question.question_index,
            'score': evaluation.get('score', 0),
            'feedback': evaluation.get('feedback', ''),
            'dimensions': evaluation.get('dimensions', {}),
            'next_question': {
                'id': next_question.id,
                'index': next_question.question_index,
                'question': next_question.question_text
            } if next_question else None
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete the interview session.
        
        POST /api/v1/interviews/{id}/complete/
        """
        session = self.get_object()
        
        # Check if all questions are answered
        unanswered = session.questions.filter(answer_text='').count()
        if unanswered > 0:
            return Response({
                'error': f'{unanswered} questions still unanswered.',
                'session_id': session.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Complete session
        result = interview_service.complete_session(session)
        
        return Response({
            'session_id': session.id,
            'overall_score': result['overall_score'],
            'score_breakdown': result['score_breakdown'],
            'feedback_summary': result['feedback_summary']
        })
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser], url_path='voice-answer')
    def voice_answer(self, request, pk=None):
        """
        Submit a voice answer for the current question.

        POST /api/v1/interviews/{id}/voice-answer/
        Multipart form with 'audio' file field.
        """
        session = self.get_object()

        audio_file = request.FILES.get('audio')
        if not audio_file:
            return Response(
                {'error': 'No audio file provided. Send as "audio" in multipart form.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB
        if audio_file.size > MAX_AUDIO_SIZE:
            return Response(
                {'error': 'Audio file too large. Maximum 25MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ALLOWED_AUDIO_TYPES = {
            'audio/webm', 'audio/wav', 'audio/wave', 'audio/x-wav',
            'audio/mpeg', 'audio/mp3', 'audio/ogg', 'audio/flac',
            'audio/mp4', 'audio/x-m4a', 'video/webm',
        }
        content_type = getattr(audio_file, 'content_type', '')
        if content_type and content_type not in ALLOWED_AUDIO_TYPES:
            return Response(
                {'error': f'Unsupported audio format: {content_type}. Use webm, wav, mp3, or ogg.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        audio_bytes = audio_file.read()

        AUDIO_MAGIC = {
            b'RIFF': 'wav', b'ID3': 'mp3', b'\xff\xfb': 'mp3',
            b'\xff\xf3': 'mp3', b'OggS': 'ogg', b'fLaC': 'flac',
            b'\x1aE\xdf\xa3': 'webm',
        }
        detected = False
        for magic in AUDIO_MAGIC:
            if audio_bytes[:len(magic)] == magic:
                detected = True
                break
        if not detected and len(audio_bytes) > 4:
            return Response(
                {'error': 'File does not appear to be a valid audio format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Transcribe audio
        transcript = voice_interview_service.speech_to_text(audio_bytes)
        if not transcript:
            return Response(
                {'error': 'Failed to transcribe audio. Please try again.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Get current unanswered question
        current_question = session.questions.filter(answer_text='').first()
        if not current_question:
            return Response({
                'error': 'All questions answered. Complete the session.',
                'session_id': session.id
            }, status=status.HTTP_400_BAD_REQUEST)

        # Save transcribed answer
        current_question.answer_text = transcript
        current_question.answered_at = timezone.now()
        current_question.save()

        # Evaluate answer (same logic as text answer action)
        evaluation = interview_service.evaluate_answer(
            question=current_question.question_text,
            answer=transcript,
            interview_type=session.interview_type,
            target_role=session.target_role
        )

        # Update question with score
        current_question.score = evaluation.get('score', 0)
        current_question.feedback = evaluation.get('feedback', '')
        current_question.score_details = evaluation
        current_question.save()

        # Get next question
        next_question = session.questions.filter(answer_text='').first()

        # Generate TTS for next question
        next_question_audio = None
        if next_question:
            audio_data = voice_interview_service.text_to_speech(next_question.question_text)
            if audio_data:
                next_question_audio = base64.b64encode(audio_data).decode('utf-8')

        return Response({
            'session_id': session.id,
            'question_index': current_question.question_index,
            'transcript': transcript,
            'score': evaluation.get('score', 0),
            'feedback': evaluation.get('feedback', ''),
            'dimensions': evaluation.get('dimensions', {}),
            'next_question': {
                'id': next_question.id,
                'index': next_question.question_index,
                'question': next_question.question_text
            } if next_question else None,
            'next_question_audio': next_question_audio,
        })

    @action(detail=True, methods=['get'], url_path='question-audio/(?P<question_index>[0-9]+)')
    def question_audio(self, request, pk=None, question_index=None):
        """
        Get TTS audio for a specific question.

        GET /api/v1/interviews/{id}/question-audio/{question_index}/
        Returns audio/mpeg content.
        """
        session = self.get_object()

        # Find the question
        question = session.questions.filter(question_index=int(question_index)).first()
        if not question:
            return Response(
                {'error': f'Question {question_index} not found in session.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate TTS audio
        audio_data = voice_interview_service.text_to_speech(question.question_text)
        if not audio_data:
            return Response(
                {'error': 'Failed to generate audio.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return HttpResponse(audio_data, content_type='audio/mpeg')

    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get user's interview history.

        GET /api/v1/interviews/history/
        """
        sessions = self.get_queryset()
        serializer = InterviewHistorySerializer(sessions, many=True)
        return Response(serializer.data)
    
    def _build_user_context(self, user):
        """Build user context from profile and career data."""
        context_parts = []
        
        try:
            # Get Rashid profile
            profile = getattr(user, 'rashid_profile', None)
            if profile:
                if profile.current_role:
                    context_parts.append(f"Current role: {profile.current_role}")
                if profile.target_role:
                    context_parts.append(f"Target role: {profile.target_role}")
                if profile.skills:
                    skills = profile.skills[:5] if isinstance(profile.skills, list) else []
                    if skills:
                        context_parts.append(f"Skills: {', '.join(skills)}")
        except Exception:
            pass
        
        return '; '.join(context_parts) if context_parts else None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interview_stats(request):
    """
    Get interview statistics for the user.
    
    GET /api/v1/interviews/stats/
    """
    user = request.user
    
    total_sessions = InterviewSession.objects.filter(user=user).count()
    completed_sessions = InterviewSession.objects.filter(user=user, status='completed').count()
    avg_score = InterviewSession.objects.filter(user=user, overall_score__isnull=False).aggregate(
        avg_score=models.Avg('overall_score')
    )['avg_score'] or 0
    
    # By type
    by_type = InterviewSession.objects.filter(user=user, status='completed').values(
        'interview_type'
    ).annotate(
        count=models.Count('id'),
        avg_score=models.Avg('overall_score')
    )
    
    return Response({
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'avg_score': round(avg_score, 1),
        'by_type': list(by_type)
    })