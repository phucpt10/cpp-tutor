"""XP and level calculation helpers."""

from __future__ import annotations


def level_from_xp(xp: int) -> int:
    """Map XP to level using the project rule set."""
    if xp >= 1000:
        return 5
    if xp >= 600:
        return 4
    if xp >= 300:
        return 3
    if xp >= 100:
        return 2
    return 1


def title_from_level(level: int) -> str:
    """Return adventure title for current level."""
    titles = {
        1: "Novice",
        2: "Explorer",
        3: "Apprentice",
        4: "Developer",
        5: "Master",
    }
    return titles.get(level, "Master")


def next_level_target(level: int) -> int | None:
    """Return target XP for the next level, None when max level reached."""
    targets = {
        1: 100,
        2: 300,
        3: 600,
        4: 1000,
    }
    return targets.get(level)


def progress_to_next_level(xp: int) -> tuple[int, int, int | None]:
    """Return current level, progress points, and target points for current bracket."""
    level = level_from_xp(xp)
    if level == 1:
        return level, xp, 100
    if level == 2:
        return level, xp - 100, 200
    if level == 3:
        return level, xp - 300, 300
    if level == 4:
        return level, xp - 600, 400
    return level, 0, None
