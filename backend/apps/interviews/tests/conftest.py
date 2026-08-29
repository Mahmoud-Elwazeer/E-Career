"""
Interview test fixtures — mock AI services so tests don't need Bedrock.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_interview_ai(monkeypatch):
    """Mock all AI-dependent services used by interview endpoints."""

    # Mock generate_questions
    fake_questions = [
        {"question": f"Test question {i}", "evaluation_criteria": "clarity"}
        for i in range(1, 6)
    ]
    monkeypatch.setattr(
        "apps.interviews.service.interview_service.generate_questions",
        lambda **kw: fake_questions,
    )

    # Mock evaluate_answer
    monkeypatch.setattr(
        "apps.interviews.service.interview_service.evaluate_answer",
        lambda **kw: {
            "score": 85,
            "feedback": "Good answer.",
            "dimensions": {"clarity": 80, "depth": 90},
        },
    )

    # Mock complete_session
    monkeypatch.setattr(
        "apps.interviews.service.interview_service.complete_session",
        lambda session: {
            "overall_score": 82,
            "score_breakdown": {"technical": 85, "communication": 80},
            "feedback_summary": "Strong performance overall.",
        },
    )

    # Mock voice services
    monkeypatch.setattr(
        "apps.interviews.voice_service.voice_interview_service.speech_to_text",
        lambda audio_bytes: "Transcribed answer text",
    )
    monkeypatch.setattr(
        "apps.interviews.voice_service.voice_interview_service.text_to_speech",
        lambda text: b"fake-audio-bytes",
    )

    # Mock coding service
    with patch("apps.interviews.coding_service.CodingInterviewService") as mock_cls:
        inst = MagicMock()
        inst.generate_problem.return_value = {
            "id": "prob-1",
            "title": "Two Sum",
            "problem": "Given an array...",
            "difficulty": "medium",
            "test_cases": [{"input": "[2,7,11,15], 9", "expected": "[0,1]"}],
        }
        inst.execute_code.return_value = {
            "status": "success",
            "result": [{"passed": True}],
        }
        inst.evaluate_solution.return_value = {
            "score": 90,
            "feedback": "Clean solution.",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
        }
        mock_cls.return_value = inst
        yield


@pytest.fixture(autouse=True)
def mock_career_brain_signal(monkeypatch):
    """Prevent CareerBrain sync from calling Bedrock on InterviewSession save."""
    monkeypatch.setattr(
        "apps.career.tasks.sync_career_brain.delay",
        lambda user_id: None,
    )
