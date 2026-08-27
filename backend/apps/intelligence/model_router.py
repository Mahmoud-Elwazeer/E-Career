"""
Centralized Model Router.

Determines the appropriate AI model based on task type, complexity,
quality requirements, and cost constraints. No feature should
independently select models — all routing goes through here.
"""
from __future__ import annotations

import structlog
from django.conf import settings
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger()


class TaskType(str, Enum):
    CHAT = "chat"
    CV_PARSING = "cv_parsing"
    JOB_MATCHING = "job_matching"
    INTERVIEW_PREP = "interview_prep"
    COVER_LETTER = "cover_letter"
    SKILL_ANALYSIS = "skill_analysis"
    CONTENT_GENERATION = "content_generation"
    RESEARCH = "research"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    RANKING = "ranking"
    SUMMARY = "summary"
    TRANSLATION = "translation"


class QualityLevel(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    HIGH = "high"


@dataclass
class ModelSelection:
    model_id: str
    model_alias: str
    max_tokens: int
    temperature: float
    reason: str


TASK_MODEL_MAP: dict[TaskType, dict[QualityLevel, str]] = {
    TaskType.CHAT: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "haiku",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.CV_PARSING: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "sonnet",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.JOB_MATCHING: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "haiku",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.INTERVIEW_PREP: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "sonnet",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.COVER_LETTER: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "sonnet",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.SKILL_ANALYSIS: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "haiku",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.CONTENT_GENERATION: {
        QualityLevel.FAST: "sonnet",
        QualityLevel.BALANCED: "sonnet",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.RESEARCH: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "sonnet",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.CLASSIFICATION: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "haiku",
        QualityLevel.HIGH: "haiku",
    },
    TaskType.EXTRACTION: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "haiku",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.RANKING: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "sonnet",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.SUMMARY: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "haiku",
        QualityLevel.HIGH: "sonnet",
    },
    TaskType.TRANSLATION: {
        QualityLevel.FAST: "haiku",
        QualityLevel.BALANCED: "haiku",
        QualityLevel.HIGH: "sonnet",
    },
}

TASK_DEFAULTS: dict[TaskType, dict] = {
    TaskType.CHAT: {"max_tokens": 1024, "temperature": 0.7},
    TaskType.CV_PARSING: {"max_tokens": 3000, "temperature": 0.1},
    TaskType.JOB_MATCHING: {"max_tokens": 512, "temperature": 0.2},
    TaskType.INTERVIEW_PREP: {"max_tokens": 2000, "temperature": 0.5},
    TaskType.COVER_LETTER: {"max_tokens": 1500, "temperature": 0.6},
    TaskType.SKILL_ANALYSIS: {"max_tokens": 1024, "temperature": 0.2},
    TaskType.CONTENT_GENERATION: {"max_tokens": 3000, "temperature": 0.7},
    TaskType.RESEARCH: {"max_tokens": 2000, "temperature": 0.3},
    TaskType.CLASSIFICATION: {"max_tokens": 256, "temperature": 0.1},
    TaskType.EXTRACTION: {"max_tokens": 2000, "temperature": 0.1},
    TaskType.RANKING: {"max_tokens": 1024, "temperature": 0.2},
    TaskType.SUMMARY: {"max_tokens": 512, "temperature": 0.3},
    TaskType.TRANSLATION: {"max_tokens": 2000, "temperature": 0.3},
}


def select_model(
    task: TaskType,
    quality: QualityLevel = QualityLevel.BALANCED,
    context_length: int = 0,
) -> ModelSelection:
    """Select the optimal model for a given task and quality level.

    Uses the cheapest model that reliably satisfies the required quality.
    """
    model_alias = TASK_MODEL_MAP.get(task, {}).get(quality, "haiku")
    defaults = TASK_DEFAULTS.get(task, {"max_tokens": 1024, "temperature": 0.3})

    if context_length > 100000:
        model_alias = "sonnet"

    override = getattr(settings, "AI_MODEL_OVERRIDES", {}).get(task.value)
    if override:
        model_alias = override

    return ModelSelection(
        model_id=_resolve_model_id(model_alias),
        model_alias=model_alias,
        max_tokens=defaults["max_tokens"],
        temperature=defaults["temperature"],
        reason=f"task={task.value}, quality={quality.value}",
    )


def _resolve_model_id(alias: str) -> str:
    """Resolve alias to full Bedrock model ID."""
    from .bedrock_plugin import MODEL_ALIASES
    return MODEL_ALIASES.get(alias, alias)
