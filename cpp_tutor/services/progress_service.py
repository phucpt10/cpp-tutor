"""Progress and gamification service."""

from __future__ import annotations

from datetime import datetime, timezone

from postgrest.exceptions import APIError

from cpp_tutor.database.supabase_client import SupabaseRepository
from cpp_tutor.models.progress import STATUS_COMPLETED, STATUS_LOCKED, STATUS_UNLOCKED
from cpp_tutor.models.student import Student
from cpp_tutor.models.topic import Topic
from cpp_tutor.services.gamification_service import GamificationService
from cpp_tutor.utils.xp_calculator import level_from_xp


class ProgressService:
    """Manage student profile, progress status, and XP operations."""

    def __init__(self, repo: SupabaseRepository | None = None) -> None:
        self.repo = repo or SupabaseRepository()
        self.gamification_service = GamificationService(self.repo)

    def bootstrap_student(
        self,
        *,
        user_id: str,
        email: str,
        student_code: str,
        full_name: str,
        class_name: str = "",
    ) -> None:
        """Ensure student row has required profile fields and initial progress exists."""
        if not student_code.strip() or not full_name.strip() or not email.strip():
            raise ValueError("Student code, email, and full name are required")

        existing = self.repo.select("students", "*", id=user_id)
        if not existing:
            insert_data = {
                "id": user_id,
                "student_code": student_code.strip(),
                "email": email,
                "full_name": full_name.strip(),
                "xp": 0,
                "level": 1,
                "streak_days": 0,
                "energy": 100,
                "total_score": 0,
            }
            if class_name.strip():
                insert_data["class"] = class_name.strip()
            self.repo.insert("students", insert_data)
        else:
            update_data = {
                "student_code": student_code.strip(),
                "email": email,
                "full_name": full_name.strip(),
                "level": level_from_xp(int(existing[0].get("xp", 0))),
            }
            if class_name.strip():
                update_data["class"] = class_name.strip()
            self.repo.update(
                "students",
                update_data,
                id=user_id,
            )

        topics = self.list_topics()
        progress_rows = self.repo.select("progress", "*", student_id=user_id)
        progress_by_topic = {int(row["topic_id"]): row for row in progress_rows}

        for idx, topic in enumerate(topics):
            if topic.id in progress_by_topic:
                continue
            status = STATUS_UNLOCKED if idx == 0 else STATUS_LOCKED
            self.repo.insert(
                "progress",
                {
                    "student_id": user_id,
                    "topic_id": topic.id,
                    "status": status,
                    "score": 0,
                },
            )

        try:
            self.gamification_service.bootstrap_foundation(user_id)
        except APIError as exc:
            # Allow learning flow to continue when optional gamification tables are blocked by RLS.
            if not self._is_rls_error(exc):
                raise

    @staticmethod
    def _is_rls_error(exc: APIError) -> bool:
        """Return True when Supabase rejects write due to row-level security."""
        payload = getattr(exc, "args", [None])
        if payload and isinstance(payload[0], dict):
            if str(payload[0].get("code", "")) == "42501":
                return True
            message = str(payload[0].get("message", "")).lower()
            return "row-level security" in message
        return "row-level security" in str(exc).lower()

    def get_student(self, student_id: str) -> Student:
        """Return student profile."""
        rows = self.repo.select("students", "*", id=student_id)
        if not rows:
            raise ValueError("Student not found")
        return Student.from_row(rows[0])

    def list_topics(self) -> list[Topic]:
        """Return all topics ordered by id."""
        rows = self.repo.client.table("topics").select("*").order("id").execute().data or []
        return [Topic.from_row(row) for row in rows]

    def get_progress_map(self, student_id: str) -> dict[int, dict]:
        """Return progress rows indexed by topic_id."""
        rows = self.repo.select("progress", "*", student_id=student_id)
        return {int(row["topic_id"]): row for row in rows}

    def get_topics_with_progress(self, student_id: str) -> list[dict]:
        """Aggregate topic metadata with learner progress."""
        topics = self.list_topics()
        progress_map = self.get_progress_map(student_id)

        result: list[dict] = []
        for topic in topics:
            progress = progress_map.get(topic.id)
            status = progress["status"] if progress else STATUS_LOCKED
            score = int(progress.get("score", 0)) if progress else 0
            result.append(
                {
                    "id": topic.id,
                    "title": topic.title,
                    "level": topic.level,
                    "xp_reward": topic.xp_reward,
                    "status": status,
                    "score": score,
                }
            )
        return result

    def mark_quiz_result(self, student_id: str, topic_id: int, score: int) -> None:
        """Persist quiz score and unlock next topic when passed."""
        is_pass = score >= 80
        status = STATUS_COMPLETED if is_pass else STATUS_UNLOCKED

        payload = {
            "status": status,
            "score": score,
        }
        if is_pass:
            payload["completed_at"] = datetime.now(timezone.utc).isoformat()

        self.repo.update(
            "progress",
            payload,
            student_id=student_id,
            topic_id=topic_id,
        )

        self._sync_total_score(student_id)
        topic = next((topic for topic in self.list_topics() if topic.id == topic_id), None)
        if topic:
            self.gamification_service.register_quiz_result(student_id, topic.title, score)

        if is_pass:
            self._unlock_next_topic(student_id, topic_id)

    def _unlock_next_topic(self, student_id: str, topic_id: int) -> None:
        """Unlock the next topic only if currently locked."""
        topics = self.list_topics()
        ordered_ids = [topic.id for topic in topics]
        if topic_id not in ordered_ids:
            return

        idx = ordered_ids.index(topic_id)
        if idx + 1 >= len(ordered_ids):
            return

        next_topic_id = ordered_ids[idx + 1]
        next_row = self.repo.select(
            "progress",
            "*",
            student_id=student_id,
            topic_id=next_topic_id,
        )
        if not next_row:
            return
        if next_row[0].get("status") == STATUS_LOCKED:
            self.repo.update(
                "progress",
                {"status": STATUS_UNLOCKED},
                student_id=student_id,
                topic_id=next_topic_id,
            )

    def award_xp_once(self, student_id: str, topic_id: int, action: str, xp_amount: int) -> bool:
        """Award XP idempotently by checking xp_logs unique key."""
        existing = self.repo.select(
            "xp_logs",
            "*",
            student_id=student_id,
            topic_id=topic_id,
            action=action,
        )
        if existing:
            return False

        student = self.get_student(student_id)
        self.repo.update("students", {"xp": student.xp + xp_amount}, id=student_id)
        self.repo.insert(
            "xp_logs",
            {
                "student_id": student_id,
                "topic_id": topic_id,
                "action": action,
                "xp_delta": xp_amount,
            },
        )
        self.gamification_service.sync_student_state(student_id)
        if action == "THEORY_READ":
            self.gamification_service.register_theory_read(student_id)
        return True

    def has_read_theory(self, student_id: str, topic_id: int) -> bool:
        """Return True when learner completed theory-read step for a topic."""
        rows = self.repo.select(
            "xp_logs",
            "id",
            student_id=student_id,
            topic_id=topic_id,
            action="THEORY_READ",
        )
        return bool(rows)

    def _sync_total_score(self, student_id: str) -> None:
        """Recalculate and persist cumulative topic score for one student."""
        rows = self.repo.select("progress", "score", student_id=student_id)
        total_score = sum(int(row.get("score", 0)) for row in rows)
        self.repo.update("students", {"total_score": total_score}, id=student_id)
