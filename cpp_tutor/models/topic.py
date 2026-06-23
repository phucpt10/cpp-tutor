"""Topic domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Topic:
    """Represents one topic in course roadmap."""

    id: int
    title: str
    level: int
    xp_reward: int

    @staticmethod
    def from_row(row: dict) -> "Topic":
        """Create model from Supabase row."""
        return Topic(
            id=int(row["id"]),
            title=row.get("title", ""),
            level=int(row.get("level", 1)),
            xp_reward=int(row.get("xp_reward", 20)),
        )
