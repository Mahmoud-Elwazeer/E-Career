"""
Shared Code Execution Utility

Wraps Judge0 API integration so both apps/assessment and apps/interviews
can execute and grade code against test cases.
"""

import logging
import time
from typing import Dict, Any, List

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Judge0 API configuration
JUDGE0_API_URL = getattr(settings, 'JUDGE0_API_URL', 'https://judge0-ce.p.rapidapi.com')
JUDGE0_API_KEY = getattr(settings, 'JUDGE0_API_KEY', None)

# Supported languages mapping (language name -> Judge0 language id)
LANGUAGE_IDS = {
    'python': 71,
    'python3': 71,
    'javascript': 63,
    'java': 62,
    'c++': 54,
    'cpp': 54,
    'c': 50,
    'c#': 51,
    'csharp': 51,
    'php': 56,
    'ruby': 72,
    'go': 59,
    'rust': 75,
}

# Judge0 submission statuses
STATUS_ACCEPTED = 3
STATUS_WRONG_ANSWER = 4
STATUS_TIME_LIMIT = 5
STATUS_COMPILATION_ERROR = 6
STATUS_RUNTIME_ERROR = 7  # covers SIGSEGV, SIGXFSZ, SIGFPE, SIGABRT, NZEC, Other
STATUS_IN_QUEUE = 1
STATUS_PROCESSING = 2


def _get_headers() -> Dict[str, str]:
    """Build headers for Judge0 API requests."""
    headers = {'Content-Type': 'application/json'}
    if JUDGE0_API_KEY:
        headers['X-RapidAPI-Key'] = JUDGE0_API_KEY
        headers['X-RapidAPI-Host'] = 'judge0-ce.p.rapidapi.com'
    return headers


def _get_language_id(language: str) -> int:
    """Resolve language string to Judge0 language id."""
    return LANGUAGE_IDS.get(language.lower(), 71)  # default to Python 3


def _submit_and_wait(source_code: str, language_id: int, stdin: str = '',
                     expected_output: str = None, timeout_sec: int = 15) -> Dict[str, Any]:
    """
    Submit code to Judge0, poll until completion, and return result dict.

    Returns:
        {status_id, status_description, stdout, stderr, compile_output, time, memory}
    """
    headers = _get_headers()
    body = {
        'language_id': language_id,
        'source_code': source_code,
        'stdin': stdin,
    }
    if expected_output is not None:
        body['expected_output'] = expected_output

    try:
        resp = requests.post(
            f"{JUDGE0_API_URL}/submissions?base64_encoded=false&wait=false",
            json=body,
            headers=headers,
            timeout=10,
        )
        if resp.status_code not in (200, 201):
            return {'error': f'Judge0 submit error: HTTP {resp.status_code}', 'status_id': -1}

        token = resp.json().get('token')
        if not token:
            return {'error': 'No token received from Judge0', 'status_id': -1}

        # Poll for result
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            time.sleep(1)
            poll_resp = requests.get(
                f"{JUDGE0_API_URL}/submissions/{token}?base64_encoded=false&fields=*",
                headers=headers,
                timeout=10,
            )
            if poll_resp.status_code != 200:
                continue
            data = poll_resp.json()
            status_id = data.get('status', {}).get('id', 0)
            if status_id not in (STATUS_IN_QUEUE, STATUS_PROCESSING):
                return {
                    'status_id': status_id,
                    'status_description': data.get('status', {}).get('description', ''),
                    'stdout': (data.get('stdout') or '').strip(),
                    'stderr': (data.get('stderr') or '').strip(),
                    'compile_output': (data.get('compile_output') or '').strip(),
                    'time': data.get('time'),
                    'memory': data.get('memory'),
                }

        return {'error': 'Judge0 execution timed out', 'status_id': -1}

    except requests.RequestException as exc:
        logger.error(f"Judge0 request failed: {exc}")
        return {'error': str(exc), 'status_id': -1}


def execute_and_grade(code: str, language: str, test_cases: list) -> dict:
    """
    Execute code against test cases and return grading result.

    Args:
        code: Source code submitted by the user.
        language: Programming language name (e.g. 'python', 'javascript').
        test_cases: List of dicts, each with 'input' and 'expected' keys.

    Returns:
        {
            'passed': bool,          # True if ALL test cases passed
            'tests_passed': int,
            'tests_total': int,
            'score': float,          # 0.0 - 1.0
            'details': list,         # per-test results
        }
    """
    if not test_cases:
        # No test cases defined — cannot grade, assume pass
        return {
            'passed': True,
            'tests_passed': 0,
            'tests_total': 0,
            'score': 1.0,
            'details': [],
        }

    language_id = _get_language_id(language)
    details = []
    tests_passed = 0
    tests_total = len(test_cases)

    for idx, tc in enumerate(test_cases):
        stdin = tc.get('input', '')
        expected = tc.get('expected', '').strip()

        result = _submit_and_wait(
            source_code=code,
            language_id=language_id,
            stdin=stdin,
            expected_output=expected,
        )

        if result.get('error'):
            details.append({
                'test_index': idx,
                'passed': False,
                'error': result['error'],
                'input': stdin,
                'expected': expected,
                'actual': None,
            })
            continue

        actual_output = result.get('stdout', '').strip()
        status_id = result.get('status_id', -1)

        # Judge0 returns status_id 3 (Accepted) when expected_output matches stdout
        test_passed = (status_id == STATUS_ACCEPTED)

        # Fallback: if Judge0 didn't check expected_output, do string comparison
        if status_id != STATUS_ACCEPTED and actual_output == expected:
            test_passed = True

        if test_passed:
            tests_passed += 1

        details.append({
            'test_index': idx,
            'passed': test_passed,
            'input': stdin,
            'expected': expected,
            'actual': actual_output,
            'status': result.get('status_description', ''),
            'time': result.get('time'),
            'memory': result.get('memory'),
            'stderr': result.get('stderr', ''),
            'compile_output': result.get('compile_output', ''),
        })

    score = tests_passed / tests_total if tests_total > 0 else 0.0

    return {
        'passed': tests_passed == tests_total,
        'tests_passed': tests_passed,
        'tests_total': tests_total,
        'score': score,
        'details': details,
    }
