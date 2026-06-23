"""Admin service for classroom progress tracking and statistics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cpp_tutor.database.supabase_client import SupabaseRepository


@dataclass(slots=True)
class StudentProgressStat:
    """Student progress and score snapshot."""

    student_id: str
    student_code: str
    full_name: str
    email: str
    xp: int
    level: int
    streak_days: int
    energy: int
    total_score: int
    quiz_completed: int
    practice_passed: int
    boss_defeated: int
    achievements_count: int


@dataclass(slots=True)
class TopicCompletionStat:
    """Per-topic completion statistics across class."""

    topic_id: int
    topic_title: str
    total_students: int
    completed: int
    in_progress: int
    locked: int
    completion_rate: float
    avg_score: float


@dataclass(slots=True)
class ClassOverviewStat:
    """Aggregate classroom statistics."""

    total_students: int
    avg_xp: float
    avg_level: float
    avg_total_score: float
    top_topic: str
    bottleneck_topic: str


class AdminService:
    """Provide admin-level analytics and reporting."""

    def __init__(self, repo: SupabaseRepository | None = None) -> None:
        self.repo = repo or SupabaseRepository()

    def get_all_students_progress(self) -> list[StudentProgressStat]:
        """Fetch all students with their progress metrics."""
        # Get all students
        students = self.repo.select("students", "*")
        results = []

        for student_row in students:
            student_id = student_row.get("id")

            # Count completed quizzes
            quiz_completed = len(
                self.repo.select(
                    "progress",
                    "id",
                    student_id=student_id,
                    status="COMPLETED",
                )
            )

            # Count practice passes
            practice_passed = len(
                self.repo.select(
                    "coding_submissions",
                    "id",
                    student_id=student_id,
                    passed=True,
                )
            )

            # Count boss defeats
            boss_defeated = len(
                self.repo.select(
                    "boss_battle_attempts",
                    "id",
                    student_id=student_id,
                    passed=True,
                )
            )

            # Count achievements
            achievements_count = len(
                self.repo.select(
                    "student_achievements",
                    "id",
                    student_id=student_id,
                )
            )

            results.append(
                StudentProgressStat(
                    student_id=student_id,
                    student_code=student_row.get("student_code", ""),
                    full_name=student_row.get("full_name", ""),
                    email=student_row.get("email", ""),
                    xp=int(student_row.get("xp", 0)),
                    level=int(student_row.get("level", 1)),
                    streak_days=int(student_row.get("streak_days", 0)),
                    energy=int(student_row.get("energy", 100)),
                    total_score=int(student_row.get("total_score", 0)),
                    quiz_completed=quiz_completed,
                    practice_passed=practice_passed,
                    boss_defeated=boss_defeated,
                    achievements_count=achievements_count,
                )
            )

        return sorted(results, key=lambda x: x.xp, reverse=True)

    def get_topic_completion_stats(self) -> list[TopicCompletionStat]:
        """Get per-topic completion rates and average scores."""
        topics = self.repo.select("topics", "id,title")
        total_students = len(self.repo.select("students", "id"))
        results = []

        for topic_row in topics:
            topic_id = topic_row.get("id")
            topic_title = topic_row.get("title", "")

            # Get completion counts
            progress_rows = self.repo.select("progress", "status,score", topic_id=topic_id)
            completed = sum(1 for p in progress_rows if p.get("status") == "COMPLETED")
            in_progress = sum(1 for p in progress_rows if p.get("status") == "UNLOCKED")
            locked = sum(1 for p in progress_rows if p.get("status") == "LOCKED")

            # Average score
            scores = [int(p.get("score", 0)) for p in progress_rows if p.get("status") == "COMPLETED"]
            avg_score = sum(scores) / len(scores) if scores else 0.0

            completion_rate = (completed / total_students * 100) if total_students > 0 else 0.0

            results.append(
                TopicCompletionStat(
                    topic_id=topic_id,
                    topic_title=topic_title,
                    total_students=total_students,
                    completed=completed,
                    in_progress=in_progress,
                    locked=locked,
                    completion_rate=completion_rate,
                    avg_score=avg_score,
                )
            )

        return sorted(results, key=lambda x: x.completion_rate, reverse=True)

    def get_class_overview(self) -> ClassOverviewStat:
        """Get aggregate class statistics."""
        students = self.repo.select("students", "xp,level,total_score")
        topics = self.repo.select("topics", "id,title")
        total_students = len(students)

        if total_students == 0:
            return ClassOverviewStat(
                total_students=0,
                avg_xp=0.0,
                avg_level=1.0,
                avg_total_score=0.0,
                top_topic="N/A",
                bottleneck_topic="N/A",
            )

        avg_xp = sum(int(s.get("xp", 0)) for s in students) / total_students
        avg_level = sum(int(s.get("level", 1)) for s in students) / total_students
        avg_total_score = sum(int(s.get("total_score", 0)) for s in students) / total_students

        # Find top and bottleneck topics
        topic_stats = self.get_topic_completion_stats()
        top_topic = topic_stats[0].topic_title if topic_stats else "N/A"
        bottleneck_topic = topic_stats[-1].topic_title if topic_stats else "N/A"

        return ClassOverviewStat(
            total_students=total_students,
            avg_xp=avg_xp,
            avg_level=avg_level,
            avg_total_score=avg_total_score,
            top_topic=top_topic,
            bottleneck_topic=bottleneck_topic,
        )

    def get_leaderboard_top_n(self, n: int = 10) -> list[dict[str, Any]]:
        """Get top N students by XP."""
        leaderboard = self.repo.client.table("leaderboard").select("*").order("xp", desc=True).limit(n).execute()
        rows = leaderboard.data or []

        # Enhance with student info
        result = []
        for row in rows:
            student = self.repo.select("students", "student_code,full_name,email", id=row.get("student_id"))
            if student:
                student_info = student[0]
                result.append(
                    {
                        "rank": len(result) + 1,
                        "student_code": student_info.get("student_code", ""),
                        "full_name": student_info.get("full_name", ""),
                        "xp": row.get("xp", 0),
                        "email": student_info.get("email", ""),
                    }
                )

        return result
