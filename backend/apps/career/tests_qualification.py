"""Tests for the Talent Qualification contract (Phase B, §11). Offline via stubs."""
from types import SimpleNamespace

from apps.career.qualification_service import QualificationService


class _Res:
    def __init__(self, value, confidence):
        self.value = value
        self.confidence = confidence


def _svc_with(scores):
    svc = QualificationService()
    svc._dimension_scores = lambda profile: scores  # inject deterministic scores
    return svc


def test_insufficient_evidence_when_fewer_than_two_backed():
    svc = _svc_with({"skill_score": _Res(0.8, 0.9)})  # only 1 backed
    r = svc.qualify(SimpleNamespace(skills=[]))
    assert r.qualification_state == "insufficient_evidence"


def test_qualified_when_strong_and_backed():
    svc = _svc_with({
        "skill_score": _Res(0.8, 0.9),
        "experience_score": _Res(0.75, 0.8),
        "education_score": _Res(0.7, 0.6),
        "portfolio_score": _Res(0.7, 0.6),
        "interview_score": _Res(0.7, 0.6),
    })
    r = svc.qualify(SimpleNamespace(skills=["python"]))
    assert r.qualification_state == "qualified"
    assert len(r.evidence) >= 2
    assert r.missing_evidence == []


def test_partially_qualified_midrange():
    svc = _svc_with({
        "skill_score": _Res(0.5, 0.7),
        "experience_score": _Res(0.45, 0.6),
    })
    r = svc.qualify(SimpleNamespace(skills=["python"]))
    assert r.qualification_state in ("partially_qualified", "not_qualified")
    # 3 dimensions missing evidence → surfaced
    assert r.missing_evidence


def test_low_scores_not_qualified():
    svc = _svc_with({
        "skill_score": _Res(0.2, 0.6),
        "experience_score": _Res(0.1, 0.6),
    })
    r = svc.qualify(SimpleNamespace(skills=["python"]))
    assert r.qualification_state == "not_qualified"


def test_weak_confidence_counts_as_missing():
    svc = _svc_with({
        "skill_score": _Res(0.8, 0.1),   # below MIN_EVIDENCE_CONFIDENCE
        "experience_score": _Res(0.8, 0.1),
    })
    r = svc.qualify(SimpleNamespace(skills=["python"]))
    assert r.qualification_state == "insufficient_evidence"


def test_job_family_relevance_computed_when_requested():
    svc = _svc_with({
        "skill_score": _Res(0.8, 0.9),
        "experience_score": _Res(0.8, 0.9),
    })
    r = svc.qualify(SimpleNamespace(skills=["python", "backend"]),
                    target_job_family="backend engineer")
    assert r.job_family_relevance is not None
    assert r.job_family_relevance > 0
