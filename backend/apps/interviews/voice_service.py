"""
Voice Interview Service

This module provides voice-based interview capabilities using AWS Polly
for text-to-speech and AWS Transcribe for speech-to-text.
"""

import logging
import base64
from typing import Dict, Any, Optional
from io import BytesIO

import boto3
from django.conf import settings

logger = logging.getLogger(__name__)


class VoiceInterviewService:
    """
    Service for voice-based interviews.
    
    Features:
    - Text-to-speech using AWS Polly
    - Speech-to-text using AWS Transcribe
    - Audio processing for interview responses
    """
    
    def __init__(self):
        self.polly_client = boto3.client(
            'polly',
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
        self.transcribe_client = boto3.client(
            'transcribe',
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
        self.s3_client = boto3.client(
            's3',
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
        
        self.aws_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        self.aws_media_prefix = getattr(settings, 'AWS_MEDIA_PREFIX', 'interviews')
    
    def text_to_speech(self, text: str, language: str = 'en') -> Optional[bytes]:
        """
        Convert text to speech using AWS Polly.
        
        Args:
            text: Text to convert to speech
            language: Language code ('en' for English, 'ar' for Arabic)
            
        Returns:
            Audio bytes or None if error
        """
        try:
            # Select voice based on language
            if language == 'ar':
                voice_id = 'Zeina'  # Arabic voice
            else:
                voice_id = 'Matthew'  # English voice
            
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode='en-US' if language == 'en' else 'ar-SA'
            )
            
            return response['AudioStream'].read()
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return None
    
    def speech_to_text(self, audio_bytes: bytes, language: str = 'en') -> Optional[str]:
        """
        Convert speech to text using AWS Transcribe.
        
        Args:
            audio_bytes: Audio data in bytes
            language: Language code ('en' for English, 'ar' for Arabic)
            
        Returns:
            Transcribed text or None if error
        """
        try:
            # Upload audio to S3 first (required for Transcribe)
            import uuid
            import tempfile
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            # Upload to S3
            s3_key = f"{self.aws_media_prefix}/audio_{uuid.uuid4().hex}.mp3"
            self.s3_client.upload_file(tmp_path, self.aws_bucket, s3_key)
            
            # Start transcription job
            job_name = f"interview_{uuid.uuid4().hex[:8]}"
            
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': f"s3://{self.aws_bucket}/{s3_key}"},
                MediaFormat='mp3',
                LanguageCode='en-US' if language == 'en' else 'ar-SA',
                OutputBucketName=self.aws_bucket,
                OutputKey=f"{self.aws_media_prefix}/transcripts/"
            )
            
            # Wait for job completion (simplified - in production use polling)
            import time
            time.sleep(5)  # Wait for transcription
            
            # Get transcription result
            job_response = self.transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            # Download transcript from S3
            transcript_key = f"{self.aws_media_prefix}/transcripts/{job_name}.json"
            transcript_obj = self.s3_client.get_object(
                Bucket=self.aws_bucket,
                Key=transcript_key
            )
            
            import json
            transcript_data = json.loads(transcript_obj['Body'].read())
            
            # Clean up
            self.s3_client.delete_object(Bucket=self.aws_bucket, Key=s3_key)
            
            return transcript_data['results']['transcripts'][0]['transcript']
            
        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            return None
    
    def process_voice_answer(self, session_id: str, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Process a voice answer in an interview session.
        
        1. Transcribe audio to text
        2. Feed to existing interview evaluation service
        3. Generate next question
        4. Convert to speech
        5. Return response
        
        Args:
            session_id: Interview session ID
            audio_bytes: User's audio response
            
        Returns:
            Response dict with transcript, evaluation, next question audio
        """
        from apps.interviews.service import InterviewService
        
        # Step 1: Transcribe audio
        transcript = self.speech_to_text(audio_bytes)
        
        if not transcript:
            return {
                'success': False,
                'error': 'Failed to transcribe audio',
                'transcript': None,
            }
        
        # Step 2: Get interview service and evaluate
        interview_service = InterviewService()
        
        # Get current question from session
        from apps.interviews.models import InterviewSession
        try:
            session = InterviewSession.objects.get(id=session_id)
        except InterviewSession.DoesNotExist:
            return {
                'success': False,
                'error': 'Session not found',
                'transcript': transcript,
            }
        
        # Evaluate the answer
        evaluation = interview_service._evaluate_answer(
            question=session.questions[-1] if session.questions else {},
            answer=transcript,
            user=session.user
        )
        
        # Step 3: Generate next question
        next_question = interview_service._generate_next_question(
            session=session,
            current_question_index=len(session.questions)
        )
        
        # Step 4: Convert next question to speech
        next_question_audio = None
        if next_question:
            next_question_text = next_question.get('question', '')
            next_question_audio = self.text_to_speech(
                next_question_text,
                language='en' if session.mode != 'voice_arabic' else 'ar'
            )
            
            # Convert to base64 for API response
            if next_question_audio:
                next_question_audio = base64.b64encode(next_question_audio).decode('utf-8')
        
        return {
            'success': True,
            'transcript': transcript,
            'evaluation': evaluation,
            'next_question': next_question,
            'next_question_audio': next_question_audio,
        }
    
    def get_question_audio(self, question_text: str, language: str = 'en') -> Optional[bytes]:
        """
        Get audio for a question.
        
        Args:
            question_text: Question text
            language: Language code
            
        Returns:
            Audio bytes or None
        """
        return self.text_to_speech(question_text, language)


# Singleton instance
voice_interview_service = VoiceInterviewService()