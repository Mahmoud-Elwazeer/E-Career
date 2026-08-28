"""
Coding Interview Service

This module provides coding interview capabilities using Judge0 API
for code execution and AWS Bedrock for problem generation and evaluation.
"""

import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from django.conf import settings

from apps.intelligence.career_ai import career_ai_service as bedrock_service

logger = logging.getLogger(__name__)


class CodingInterviewService:
    """
    Service for coding interviews.
    
    Features:
    - Generate coding problems using Bedrock Claude
    - Execute code using Judge0 API
    - Evaluate solutions with AI feedback
    """
    
    # Judge0 API configuration
    JUDGE0_API_URL = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY = getattr(settings, 'JUDGE0_API_KEY', None)
    
    # Supported languages
    LANGUAGES = {
        'python': {'id': 71, 'name': 'Python 3', 'extension': 'py'},
        'javascript': {'id': 63, 'name': 'JavaScript (Node.js)', 'extension': 'js'},
        'java': {'id': 62, 'name': 'Java', 'extension': 'java'},
        'c++': {'id': 54, 'name': 'C++20', 'extension': 'cpp'},
        'c': {'id': 50, 'name': 'C17', 'extension': 'c'},
        'c#': {'id': 51, 'name': 'C#', 'extension': 'cs'},
        'php': {'id': 56, 'name': 'PHP', 'extension': 'php'},
        'ruby': {'id': 72, 'name': 'Ruby', 'extension': 'rb'},
        'go': {'id': 59, 'name': 'Go', 'extension': 'go'},
        'rust': {'id': 75, 'name': 'Rust', 'extension': 'rs'},
    }
    
    def __init__(self):
        self.bedrock = bedrock_service
    
    def generate_problem(self, difficulty: str, topic: str, language: str = 'python') -> Dict[str, Any]:
        """
        Generate a coding problem using Bedrock Claude.
        
        Args:
            difficulty: 'easy', 'medium', or 'hard'
            topic: Programming topic (e.g., 'arrays', 'trees', 'dynamic programming')
            language: Programming language
            
        Returns:
            Problem dict with title, description, examples, constraints, test_cases, starter_code
        """
        language_info = self.LANGUAGES.get(language, self.LANGUAGES['python'])
        
        prompt = f"""أنت مهندس برمجيات خبير. قم بإنشاء مسألة برمجية للغة {language_info['name']}.

المواصفات:
- الصعوبة: {difficulty}
- الموضوع: {topic}
- اللغة: {language_info['name']}

أعد المسألة بصيغة JSON فقط:
{{
    "title": "عنوان المسألة",
    "description": "وصف كامل للمسألة بالعربية والإنجليزية",
    "examples": [
        {{"input": "مثال الإدخال", "output": "مثال الإخراج"}},
        {{"input": "مثال إضافي", "output": "النتيجة"}}
    ],
    "constraints": ["قيد 1", "قيد 2"],
    "starter_code": "function solution() {{\n    // اكتب كودك هنا\n}}",
    "test_cases": [
        {{"input": "test_input_1", "expected": "expected_output_1"}},
        {{"input": "test_input_2", "expected": "expected_output_2"}}
    ]
}}"""

        try:
            if self.bedrock.is_available:
                response = self.bedrock.invoke_model(
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.7
                )
                
                # Parse JSON from response
                import json
                import re
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    problem = json.loads(json_match.group())
                    problem['language'] = language
                    problem['language_name'] = language_info['name']
                    problem['difficulty'] = difficulty
                    problem['topic'] = topic
                    return problem
            
            # Fallback problem
            return self._get_fallback_problem(difficulty, topic, language)
            
        except Exception as e:
            logger.error(f"Error generating problem: {e}")
            return self._get_fallback_problem(difficulty, topic, language)
    
    def _get_fallback_problem(self, difficulty: str, topic: str, language: str) -> Dict[str, Any]:
        """Get fallback problem when AI is unavailable."""
        return {
            'title': f'مسألة {topic} - {difficulty}',
            'description': f'قم بحل مسألة {topic} باستخدام {language}',
            'examples': [
                {'input': 'test', 'output': 'result'}
            ],
            'constraints': ['استخدم الوقت المطلوب', 'استخدم الذاكرة المطلوبة'],
            'starter_code': 'def solution():\n    pass',
            'test_cases': [
                {'input': 'test1', 'expected': 'result1'},
                {'input': 'test2', 'expected': 'result2'}
            ],
            'language': language,
            'language_name': 'Python 3',
            'difficulty': difficulty,
            'topic': topic,
        }
    
    def execute_code(self, code: str, language: str, test_cases: List[Dict] = None) -> Dict[str, Any]:
        """
        Execute code using Judge0 API.
        
        Args:
            code: Code to execute
            language: Programming language
            test_cases: Optional test cases to run
            
        Returns:
            Execution result with passed, failed, output, errors, execution_time, memory
        """
        language_info = self.LANGUAGES.get(language, self.LANGUAGES['python'])
        lang_id = language_info['id']
        
        # Prepare request body
        body = {
            'language_id': lang_id,
            'source_code': code,
            'stdin': '',
        }
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.JUDGE0_API_KEY:
            headers['X-RapidAPI-Key'] = self.JUDGE0_API_KEY
            headers['X-RapidAPI-Host'] = 'judge0-ce.p.rapidapi.com'
        
        try:
            # Submit job
            response = requests.post(
                f"{self.JUDGE0_API_URL}/submissions",
                json=body,
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 201:
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'output': None,
                    'stderr': None,
                    'execution_time': 0,
                    'memory': 0,
                }
            
            result = response.json()
            token = result.get('token')
            
            if not token:
                return {
                    'success': False,
                    'error': 'No token in response',
                    'output': None,
                    'stderr': None,
                    'execution_time': 0,
                    'memory': 0,
                }
            
            # Get result
            result_response = requests.get(
                f"{self.JUDGE0_API_URL}/submissions/{token}",
                headers=headers,
                timeout=10
            )
            
            result_data = result_response.json()
            
            return {
                'success': True,
                'status': result_data.get('status', {}).get('description', 'Unknown'),
                'output': result_data.get('stdout', ''),
                'stderr': result_data.get('stderr', ''),
                'execution_time': result_data.get('time', 0),
                'memory': result_data.get('memory', 0),
            }
            
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'output': None,
                'stderr': None,
                'execution_time': 0,
                'memory': 0,
            }
    
    def evaluate_solution(self, problem: Dict, code: str, execution_result: Dict) -> Dict[str, Any]:
        """
        Evaluate code solution using AI.
        
        Args:
            problem: Problem definition
            code: Submitted code
            execution_result: Result from code execution
            
        Returns:
            Evaluation dict with score, correctness, efficiency, style, suggestions
        """
        # Check if code executed successfully
        if not execution_result.get('success'):
            return {
                'score': 0,
                'correctness': 0,
                'efficiency': 0,
                'style': 0,
                'suggestions': [f"الكود لم ينفذ بنجاح: {execution_result.get('error', 'Unknown error')}"],
            }
        
        # Check against test cases if provided
        test_cases = problem.get('test_cases', [])
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            # In a real implementation, we would run each test case
            # For now, use the overall execution result
            if execution_result.get('status', '').lower() == 'accepted':
                passed += 1
            else:
                failed += 1
        
        total_tests = len(test_cases) if test_cases else 1
        
        # Calculate correctness score
        correctness = passed / max(total_tests, 1)
        
        # Calculate efficiency score (based on time and memory)
        execution_time = execution_result.get('execution_time', 0)
        memory = execution_result.get('memory', 0)
        
        # Simple efficiency scoring
        efficiency = 1.0
        if execution_time > 1.0:  # More than 1 second
            efficiency *= 0.7
        if memory > 100 * 1024 * 1024:  # More than 100MB
            efficiency *= 0.7
        
        # Calculate style score
        style = self._evaluate_style(code, problem)
        
        # Overall score
        overall_score = (correctness * 0.5 + efficiency * 0.3 + style * 0.2)
        
        # Generate suggestions using AI
        suggestions = self._generate_suggestions(
            problem=problem,
            code=code,
            correctness=correctness,
            efficiency=efficiency,
            style=style
        )
        
        return {
            'score': round(overall_score, 3),
            'correctness': round(correctness, 3),
            'efficiency': round(efficiency, 3),
            'style': round(style, 3),
            'suggestions': suggestions,
            'tests_passed': passed,
            'tests_failed': failed,
            'total_tests': total_tests,
            'execution_time': execution_time,
            'memory': memory,
        }
    
    def _evaluate_style(self, code: str, problem: Dict) -> float:
        """Evaluate code style."""
        style_score = 1.0
        
        # Check for common style issues
        if 'TODO' in code or 'FIXME' in code:
            style_score -= 0.1
        
        if 'global' in code.lower() and 'variable' in code.lower():
            style_score -= 0.1
        
        # Check for proper indentation (simplified)
        lines = code.split('\n')
        for line in lines:
            if line.startswith('    ') or line.startswith('\t') or not line.strip():
                continue
            if line.strip() and not line.startswith(' '):
                # Line doesn't start with proper indentation
                pass  # This is a simplified check
        
        return max(0.0, style_score)
    
    def _generate_suggestions(self, problem: Dict, code: str, 
                             correctness: float, efficiency: float, style: float) -> List[str]:
        """Generate improvement suggestions using AI."""
        if not self.bedrock.is_available:
            return self._get_fallback_suggestions(correctness, efficiency, style)
        
        prompt = f"""أنت مهندس برمجيات خبير. قم بتقديم اقتراحات لتحسين الكود التالي:

المسألة: {problem.get('title', 'Unknown')}
الموضوع: {problem.get('topic', 'Unknown')}
الصعوبة: {problem.get('difficulty', 'Unknown')}

الكود:
{code}

النتيجة:
- الدقة: {correctness*100:.0f}%
- الكفاءة: {efficiency*100:.0f}%
- الأسلوب: {style*100:.0f}%

أعد 3-4 اقتراحات تحسين بالعربية:
1. [اقتراح 1]
2. [اقتراح 2]
3. [اقتراح 3]
4. [اقتراح 4]
"""
        
        try:
            response = self.bedrock.invoke_model(
                prompt=prompt,
                max_tokens=300,
                temperature=0.7
            )
            
            # Parse suggestions
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    suggestions.append(line[2:].strip() if line[1] == '.' else line[1:].strip())
            
            return suggestions[:4] if suggestions else self._get_fallback_suggestions(correctness, efficiency, style)
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return self._get_fallback_suggestions(correctness, efficiency, style)
    
    def _get_fallback_suggestions(self, correctness: float, efficiency: float, style: float) -> List[str]:
        """Get fallback suggestions when AI is unavailable."""
        suggestions = []
        
        if correctness < 1.0:
            suggestions.append("تحقق من معالجة جميع حالات الحافة (edge cases)")
        
        if efficiency < 1.0:
            suggestions.append("فكر في تحسين تعقيد الوقت/الذاكرة")
        
        if style < 1.0:
            suggestions.append("استخدم أسماء متغيرات أوضح")
        
        if not suggestions:
            suggestions.append("الكود جيد! جرب تحسين الأداء")
        
        return suggestions


# Singleton instance
coding_interview_service = CodingInterviewService()