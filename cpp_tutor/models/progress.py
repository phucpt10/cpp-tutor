"""Progress domain model and constants."""

from __future__ import annotations

from dataclasses import dataclass

STATUS_LOCKED = "LOCKED"
STATUS_UNLOCKED = "UNLOCKED"
STATUS_COMPLETED = "COMPLETED"


@dataclass(slots=True)
class Progress:
    """Represents a student's progress on one topic."""

    id: int | None
    student_id: str
    topic_id: int
    status: str
    score: int

    @staticmethod
    def from_row(row: dict) -> "Progress":
        """Create model from Supabase row."""
        return Progress(
            id=row.get("id"),
            student_id=row["student_id"],
            topic_id=int(row["topic_id"]),
            status=row.get("status", STATUS_LOCKED),
            score=int(row.get("score", 0)),
        )
