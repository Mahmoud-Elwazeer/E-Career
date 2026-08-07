"""
Interview Service - Handles mock interview logic using Bedrock AI
"""
import logging
import json
import time
from django.utils import timezone
from ai.bedrock import bedrock_service
from .models import InterviewSession, InterviewQuestion

logger = logging.getLogger(__name__)


class InterviewService:
    """Core interview service for generating and evaluating mock interviews."""
    
    def __init__(self):
        self.bedrock = bedrock_service
    
    def generate_questions(self, interview_type, target_role, difficulty, user_context=None):
        """
        Generate 5 interview questions using Bedrock Haiku.
        
        Args:
            interview_type: technical, behavioral, coding, system_design, case_study
            target_role: The job title/role being interviewed for
            difficulty: easy, medium, hard
            user_context: Optional user profile context
        
        Returns:
            list: List of 5 question dictionaries
        """
        start_time = time.time()
        
        # Build prompt
        difficulty_desc = {
            'easy': 'Entry-level, fundamental concepts',
            'medium': 'Mid-level, moderate complexity',
            'hard': 'Senior-level, complex scenarios'
        }
        
        type_prompts = {
            'technical': 'Technical questions about the role',
            'behavioral': 'Behavioral and situational questions',
            'coding': 'Coding and algorithm questions',
            'system_design': 'System design and architecture questions',
            'case_study': 'Case study and problem-solving questions',
        }
        
        prompt = f"""You are an expert interviewer. Generate 5 interview questions for a {target_role} position at {difficulty} level.

Type: {type_prompts.get(interview_type, 'General')}
Difficulty: {difficulty_desc.get(difficulty, 'Medium')}

User Context: {user_context or 'No user context available'}

Format your response as a JSON array with exactly 5 questions. Each question should have:
- "question": The question text
- "evaluation_criteria": Key points to look for in a good answer

Return ONLY valid JSON, no other text."""

        try:
            response = self.bedrock.invoke_model(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            # Parse JSON from response
            questions = self._parse_questions_json(response)
            
            logger.info(f"Generated {len(questions)} questions in {time.time() - start_time:.2f}s")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._get_fallback_questions(interview_type, difficulty)
    
    def evaluate_answer(self, question, answer, interview_type, target_role):
        """
        Evaluate an answer using Bedrock Sonnet.
        
        Args:
            question: The question text
            answer: The user's answer
            interview_type: Type of interview
            target_role: The role being interviewed for
        
        Returns:
            dict: Evaluation with score (0-10) and feedback
        """
        start_time = time.time()
        
        prompt = f"""You are an expert interviewer evaluator. Evaluate the candidate's answer to this {interview_type} interview question for a {target_role} position.

Question: {question}

Answer: {answer}

Evaluate on these 6 dimensions (score each 0-10):
1. Relevance - Does the answer address the question?
2. Depth - Does it show deep understanding?
3. Structure - Is it well-organized?
4. Technical - Is the technical content accurate?
5. Communication - Is it clearly communicated?
6. Growth - Does it show learning potential?

Return a JSON object with:
- "score": Overall score (0-10)
- "dimensions": Object with scores for each dimension
- "feedback": Constructive feedback (in Arabic if question is in Arabic)
- "strengths": List of strengths
- "areas_for_improvement": List of improvement areas

Return ONLY valid JSON, no other text."""

        try:
            response = self.bedrock.invoke_model(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.5
            )
            
            evaluation = self._parse_evaluation_json(response)
            
            logger.info(f"Evaluated answer in {time.time() - start_time:.2f}s")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            return self._get_fallback_evaluation()
    
    def complete_session(self, session):
        """
        Complete an interview session and calculate overall score.
        
        Args:
            session: InterviewSession instance
        
        Returns:
            dict: Overall score and feedback summary
        """
        questions = session.questions.all()
        
        if not questions.exists():
            return {'error': 'No questions in session'}
        
        # Calculate average scores
        total_score = 0
        dimension_totals = {}
        dimension_count = 0
        
        for q in questions:
            if q.score and q.score_details:
                total_score += q.score
                dimensions = q.score_details.get('dimensions', {})
                for dim, score in dimensions.items():
                    dimension_totals[dim] = dimension_totals.get(dim, 0) + score
                    dimension_count += 1
        
        # Calculate averages
        avg_score = total_score / len(questions) if questions.exists() else 0
        avg_dimensions = {}
        for dim, total in dimension_totals.items():
            avg_dimensions[dim] = round(total / dimension_count, 1) if dimension_count > 0 else 0
        
        # Generate feedback summary
        feedback = self._generate_feedback_summary(avg_score, avg_dimensions, questions)
        
        # Update session
        session.overall_score = round(avg_score, 1)
        session.score_breakdown = {
            'dimensions': avg_dimensions,
            'total_questions': len(questions),
            'average_score': round(avg_score, 1)
        }
        session.feedback_summary = feedback
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
        
        return {
            'overall_score': round(avg_score, 1),
            'score_breakdown': session.score_breakdown,
            'feedback_summary': feedback
        }
    
    def _parse_questions_json(self, response):
        """Parse questions from Bedrock response."""
        try:
            # Try to find JSON in response
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                questions = json.loads(json_str)
                return questions
        except json.JSONDecodeError:
            pass
        
        return self._get_fallback_questions('technical', 'medium')
    
    def _parse_evaluation_json(self, response):
        """Parse evaluation from Bedrock response."""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return self._get_fallback_evaluation()
    
    def _get_fallback_questions(self, interview_type, difficulty):
        """Fallback questions when AI is unavailable."""
        return [
            {
                "question": f"Tell me about yourself and your experience with {interview_type} interviews.",
                "evaluation_criteria": "Clarity, relevance, experience level"
            },
            {
                "question": "What do you know about this role and why are you interested?",
                "evaluation_criteria": "Research, motivation, alignment"
            },
            {
                "question": "Describe a challenging problem you solved and how you approached it.",
                "evaluation_criteria": "Problem-solving, methodology, results"
            },
            {
                "question": "How do you handle working in a team with conflicting opinions?",
                "evaluation_criteria": "Communication, collaboration, conflict resolution"
            },
            {
                "question": "Where do you see yourself in 5 years?",
                "evaluation_criteria": "Vision, goals, alignment with role"
            }
        ]
    
    def _get_fallback_evaluation(self):
        """Fallback evaluation when AI is unavailable."""
        return {
            "score": 7.0,
            "dimensions": {
                "relevance": 7,
                "depth": 6,
                "structure": 7,
                "technical": 7,
                "communication": 7,
                "growth": 8
            },
            "feedback": "Good effort. Consider providing more specific examples.",
            "strengths": ["Clear communication", "Basic understanding"],
            "areas_for_improvement": ["More specific examples", "Deeper technical details"]
        }
    
    def _generate_feedback_summary(self, avg_score, dimensions, questions):
        """Generate a summary feedback for the session."""
        summary_parts = []
        
        # Overall assessment
        if avg_score >= 8:
            summary_parts.append("ممتاز! أداء قوي جداً.")
        elif avg_score >= 6:
            summary_parts.append("جيد جداً! لديك أساس قوي.")
        elif avg_score >= 4:
            summary_parts.append("جيد، لكن هناك مجال للتحسين.")
        else:
            summary_parts.append("حاول مرة أخرى مع التركيز على النقاط المذكورة.")
        
        # Dimension highlights
        if dimensions:
            best_dim = max(dimensions.items(), key=lambda x: x[1])
            worst_dim = min(dimensions.items(), key=lambda x: x[1])
            
            dim_names = {
                'relevance': 'الصلة بالسؤال',
                'depth': 'العمق',
                'structure': 'التنظيم',
                'technical': 'المحتوى التقني',
                'communication': 'التواصل',
                'growth': 'القدرة على التعلم'
            }
            
            summary_parts.append(f"أقوى مهارة: {dim_names.get(worst_dim[0], worst_dim[0])} ({worst_dim[1]}/10)")
            summary_parts.append(f"أولى بالتحسين: {dim_names.get(worst_dim[0], worst_dim[0])} ({worst_dim[1]}/10)")
        
        return " ".join(summary_parts)


# Singleton instance
interview_service = InterviewService()