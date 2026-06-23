"""Student domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Student:
    """Represents one learner profile."""

    id: str
    student_code: str
    email: str
    full_name: str
    xp: int
    level: int
    streak_days: int
    energy: int
    total_score: int
    last_login_date: str | None
    class_name: str | None = None

    @staticmethod
    def from_row(row: dict) -> "Student":
        """Create model from Supabase row."""
        return Student(
            id=row["id"],
            student_code=row.get("student_code", ""),
            email=row.get("email", ""),
            full_name=row.get("full_name", "Student"),
            xp=int(row.get("xp", 0)),
            level=int(row.get("level", 1)),
            streak_days=int(row.get("streak_days", 0)),
            energy=int(row.get("energy", 100)),
            total_score=int(row.get("total_score", 0)),
            last_login_date=row.get("last_login_date"),
            class_name=row.get("class"),
        )
