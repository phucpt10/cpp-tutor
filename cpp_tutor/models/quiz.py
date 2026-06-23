"""Quiz data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class QuizQuestion:
    """One multiple-choice quiz question."""

    question: str
    options: list[str]
    answer: str
    explanation: str


@dataclass(slots=True)
class QuizResult:
    """Quiz result summary returned to UI and persistence layers."""

    score: int
    correct: int
    total: int
    passed: bool
