"""
Shared Code Execution Utility

Uses Piston (open-source, free public API, no key required) as the primary
code execution engine. Falls back to Judge0 if JUDGE0_API_KEY is configured.
Piston API: https://github.com/engineer-man/piston
"""

import logging
import time
from typing import Dict, Any, List

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

PISTON_API_URL = getattr(settings, 'PISTON_API_URL', 'https://emkc.org/api/v2/piston')

JUDGE0_API_URL = getattr(settings, 'JUDGE0_API_URL', 'https://judge0-ce.p.rapidapi.com')
JUDGE0_API_KEY = getattr(settings, 'JUDGE0_API_KEY', None)

PISTON_LANGUAGES = {
    'python': ('python', '3.10'),
    'python3': ('python', '3.10'),
    'javascript': ('javascript', '18.15'),
    'java': ('java', '15.0'),
    'c++': ('c++', '10.2'),
    'cpp': ('c++', '10.2'),
    'c': ('c', '10.2'),
    'c#': ('csharp', '6.12'),
    'csharp': ('csharp', '6.12'),
    'php': ('php', '8.2'),
    'ruby': ('ruby', '3.0'),
    'go': ('go', '1.16'),
    'rust': ('rust', '1.68'),
}

JUDGE0_LANGUAGE_IDS = {
    'python': 71, 'python3': 71, 'javascript': 63, 'java': 62,
    'c++': 54, 'cpp': 54, 'c': 50, 'c#': 51, 'csharp': 51,
    'php': 56, 'ruby': 72, 'go': 59, 'rust': 75,
}

STATUS_ACCEPTED = 3
STATUS_IN_QUEUE = 1
STATUS_PROCESSING = 2


def _execute_piston(source_code: str, language: str, stdin: str = '') -> Dict[str, Any]:
    """Execute code via Piston (free, no API key)."""
    lang, version = PISTON_LANGUAGES.get(language.lower(), ('python', '3.10'))
    body = {
        'language': lang,
        'version': version,
        'files': [{'content': source_code}],
        'stdin': stdin,
    }
    try:
        resp = requests.post(
            f"{PISTON_API_URL}/execute",
            json=body,
            timeout=15,
        )
        if resp.status_code != 200:
            return {'error': f'Piston HTTP {resp.status_code}', 'status_id': -1}

        data = resp.json()
        run = data.get('run', {})
        compile_out = data.get('compile', {})

        exit_code = run.get('code', -1)
        return {
            'status_id': STATUS_ACCEPTED if exit_code == 0 else 7,
            'status_description': 'Accepted' if exit_code == 0 else f'Exit code {exit_code}',
            'stdout': (run.get('stdout') or '').strip(),
            'stderr': (run.get('stderr') or '').strip(),
            'compile_output': (compile_out.get('stderr') or '').strip(),
            'time': None,
            'memory': None,
        }
    except requests.RequestException as exc:
        logger.error("piston_request_failed error=%s", exc)
        return {'error': str(exc), 'status_id': -1}


def _execute_judge0(source_code: str, language: str, stdin: str = '',
                    expected_output: str = None, timeout_sec: int = 15) -> Dict[str, Any]:
    """Execute code via Judge0 (requires JUDGE0_API_KEY)."""
    headers = {'Content-Type': 'application/json'}
    if JUDGE0_API_KEY:
        headers['X-RapidAPI-Key'] = JUDGE0_API_KEY
        headers['X-RapidAPI-Host'] = 'judge0-ce.p.rapidapi.com'

    language_id = JUDGE0_LANGUAGE_IDS.get(language.lower(), 71)
    body = {'language_id': language_id, 'source_code': source_code, 'stdin': stdin}
    if expected_output is not None:
        body['expected_output'] = expected_output

    try:
        resp = requests.post(
            f"{JUDGE0_API_URL}/submissions?base64_encoded=false&wait=false",
            json=body, headers=headers, timeout=10,
        )
        if resp.status_code not in (200, 201):
            return {'error': f'Judge0 HTTP {resp.status_code}', 'status_id': -1}

        token = resp.json().get('token')
        if not token:
            return {'error': 'No token from Judge0', 'status_id': -1}

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            time.sleep(1)
            poll = requests.get(
                f"{JUDGE0_API_URL}/submissions/{token}?base64_encoded=false&fields=*",
                headers=headers, timeout=10,
            )
            if poll.status_code != 200:
                continue
            data = poll.json()
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

        return {'error': 'Judge0 timed out', 'status_id': -1}
    except requests.RequestException as exc:
        logger.error("judge0_request_failed error=%s", exc)
        return {'error': str(exc), 'status_id': -1}


def _submit_and_wait(source_code: str, language_id: int = None, stdin: str = '',
                     expected_output: str = None, timeout_sec: int = 15,
                     language: str = 'python') -> Dict[str, Any]:
    """Execute code using Piston first, falling back to Judge0 if configured."""
    result = _execute_piston(source_code, language, stdin)

    if result.get('error') and JUDGE0_API_KEY:
        logger.info("piston_failed, falling back to judge0")
        result = _execute_judge0(source_code, language, stdin, expected_output, timeout_sec)

    if expected_output is not None and result.get('status_id') != STATUS_ACCEPTED:
        if result.get('stdout', '').strip() == expected_output.strip():
            result['status_id'] = STATUS_ACCEPTED
            result['status_description'] = 'Accepted'

    return result


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

    details = []
    tests_passed = 0
    tests_total = len(test_cases)

    for idx, tc in enumerate(test_cases):
        stdin = tc.get('input', '')
        expected = tc.get('expected', '').strip()

        result = _submit_and_wait(
            source_code=code,
            language=language,
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
