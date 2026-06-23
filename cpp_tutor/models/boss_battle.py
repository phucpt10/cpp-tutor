"""Boss battle domain models."""

from __future__ import annotations

from dataclasses import dataclass

from cpp_tutor.models.quiz import QuizQuestion


@dataclass(slots=True)
class BossBattle:
    """Represents one generated boss battle."""

    id: int | None
    topic_id: int
    title: str
    difficulty: str
    questions: list[QuizQuestion]
    coding_title: str
    coding_description: str
    coding_starter_code: str
    coding_expected_concepts: str
    provider_used: str | None = None


@dataclass(slots=True)
class BossBattleAttemptResult:
    """Represents evaluated boss battle result."""

    mcq_score: int
    coding_score: int
    overall_score: int
    passed: bool
    coding_feedback: str
    strengths: list[str]
    improvements: list[str]