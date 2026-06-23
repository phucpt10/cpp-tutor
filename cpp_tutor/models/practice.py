"""Practice and coding exercise domain models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CodingExercise:
    """Represents one generated coding practice task."""

    id: int | None
    topic_id: int
    title: str
    description: str
    starter_code: str
    expected_concepts: str
    difficulty: str
    provider_used: str | None = None


@dataclass(slots=True)
class CodingSubmissionResult:
    """Represents AI-evaluated coding submission output."""

    score: int
    passed: bool
    feedback: str
    strengths: list[str]
    improvements: list[str]