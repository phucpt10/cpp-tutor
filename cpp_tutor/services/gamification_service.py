"""Gamification foundation service for adventure progression systems."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from cpp_tutor.database.supabase_client import SupabaseRepository
from cpp_tutor.utils.xp_calculator import level_from_xp, title_from_level


@dataclass(slots=True)
class LoginRewardResult:
    """Daily login reward outcome."""

    awarded: bool
    xp_awarded: int
    streak_days: int
    energy: int


class GamificationService:
    """Provide reusable game systems shared by Streamlit pages and services."""

    DAILY_LOGIN_XP = 5
    STREAK_BONUS_XP = 100
    DAILY_ENERGY = 100

    def __init__(self, repo: SupabaseRepository | None = None) -> None:
        self.repo = repo or SupabaseRepository()

    def bootstrap_foundation(self, student_id: str) -> None:
        """Ensure gamification foundation records exist for a student."""
        self.repo.upsert("skill_tree_progress", {"student_id": student_id}, on_conflict="student_id")
        self.repo.upsert("leaderboard", {"student_id": student_id, "xp": 0, "rank": 0}, on_conflict="student_id")
        self._ensure_daily_quests(student_id)
        self.refresh_leaderboard()

    def handle_login(self, student_id: str) -> LoginRewardResult:
        """Process daily login reward, streak update, and daily resource reset."""
        self.bootstrap_foundation(student_id)
        student = self._get_student_row(student_id)

        today = date.today()
        last_login_raw = student.get("last_login_date")
        last_login = date.fromisoformat(last_login_raw) if last_login_raw else None
        streak_days = int(student.get("streak_days", 0))
        awarded = False
        xp_awarded = 0

        if last_login != today:
            awarded = True
            xp_awarded += self.DAILY_LOGIN_XP
            if last_login == today - timedelta(days=1):
                streak_days += 1
            else:
                streak_days = 1

            if streak_days > 0 and streak_days % 7 == 0:
                xp_awarded += self.STREAK_BONUS_XP
                self._grant_achievement(student_id, "7-Day Streak")

            new_xp = int(student.get("xp", 0)) + xp_awarded
            new_level = level_from_xp(new_xp)
            self.repo.update(
                "students",
                {
                    "xp": new_xp,
                    "level": new_level,
                    "streak_days": streak_days,
                    "energy": self.DAILY_ENERGY,
                    "last_login_date": today.isoformat(),
                },
                id=student_id,
            )
            self.repo.insert(
                "xp_logs",
                {
                    "student_id": student_id,
                    "topic_id": 1,
                    "action": f"DAILY_LOGIN_{today.isoformat()}",
                    "xp_delta": xp_awarded,
                },
            )
            self.increment_daily_quest(student_id, "LOGIN")
        else:
            self.repo.update(
                "students",
                {
                    "energy": self.DAILY_ENERGY,
                    "level": level_from_xp(int(student.get("xp", 0))),
                },
                id=student_id,
            )

        self._ensure_daily_quests(student_id)
        self.refresh_leaderboard()
        refreshed = self._get_student_row(student_id)
        return LoginRewardResult(
            awarded=awarded,
            xp_awarded=xp_awarded,
            streak_days=int(refreshed.get("streak_days", 0)),
            energy=int(refreshed.get("energy", self.DAILY_ENERGY)),
        )

    def sync_student_state(self, student_id: str) -> None:
        """Synchronize derived state such as level and leaderboard from current XP."""
        student = self._get_student_row(student_id)
        xp = int(student.get("xp", 0))
        self.repo.update("students", {"level": level_from_xp(xp)}, id=student_id)
        self._ensure_daily_quests(student_id)
        self.refresh_leaderboard()
        self._check_foundation_achievements(student_id)

    def get_overview(self, student_id: str) -> dict:
        """Return minimal gamification overview for dashboard and profile."""
        student = self._get_student_row(student_id)
        level = int(student.get("level", level_from_xp(int(student.get("xp", 0)))))
        achievements = (
            self.repo.client.table("student_achievements")
            .select("earned_at, achievements(name, description, badge_icon)")
            .eq("student_id", student_id)
            .order("earned_at", desc=True)
            .execute()
            .data
            or []
        )
        quests = (
            self.repo.client.table("daily_quests")
            .select("*")
            .eq("student_id", student_id)
            .eq("quest_date", date.today().isoformat())
            .order("id")
            .execute()
            .data
            or []
        )
        leaderboard = (
            self.repo.client.table("leaderboard")
            .select("xp, rank, students(full_name, student_code, level)")
            .order("rank")
            .limit(10)
            .execute()
            .data
            or []
        )
        skill_tree = (
            self.repo.client.table("skill_tree_progress")
            .select("syntax_score, problem_solving_score, debugging_score, memory_management_score, oop_score")
            .eq("student_id", student_id)
            .limit(1)
            .execute()
            .data
            or [{}]
        )[0]

        return {
            "level": level,
            "title": title_from_level(level),
            "streak_days": int(student.get("streak_days", 0)),
            "energy": int(student.get("energy", self.DAILY_ENERGY)),
            "achievements": achievements,
            "daily_quests": quests,
            "leaderboard": leaderboard,
            "skill_tree": skill_tree,
            "world_map": self._world_map(),
        }

    def register_theory_read(self, student_id: str) -> None:
        """Advance quest progress after reading theory."""
        self.increment_daily_quest(student_id, "THEORY")
        self._check_foundation_achievements(student_id)

    def register_quiz_result(self, student_id: str, topic_title: str, score: int) -> None:
        """Advance quest progress, skill tree, and achievements after a quiz."""
        if score >= 80:
            self.increment_daily_quest(student_id, "QUIZ")
        self._update_skill_tree(student_id, topic_title, score)
        self._check_foundation_achievements(student_id)
        self.refresh_leaderboard()

    def register_coding_exercise_completion(self, student_id: str) -> None:
        """Re-evaluate achievements after passing one coding exercise."""
        self._check_foundation_achievements(student_id)
        self.refresh_leaderboard()

    def register_boss_battle_completion(self, student_id: str) -> None:
        """Grant boss badge and refresh dependent gamification state."""
        self._grant_achievement(student_id, "Boss Conqueror")
        self._check_foundation_achievements(student_id)
        self.refresh_leaderboard()

    def increment_daily_quest(self, student_id: str, quest_type: str, amount: int = 1) -> None:
        """Increment one daily quest and award XP on completion."""
        self._ensure_daily_quests(student_id)
        rows = (
            self.repo.client.table("daily_quests")
            .select("*")
            .eq("student_id", student_id)
            .eq("quest_type", quest_type)
            .eq("quest_date", date.today().isoformat())
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return

        quest = rows[0]
        if quest.get("completed"):
            return

        progress = min(int(quest.get("progress", 0)) + amount, int(quest.get("target", 1)))
        completed = progress >= int(quest.get("target", 1))
        self.repo.update(
            "daily_quests",
            {"progress": progress, "completed": completed},
            id=quest["id"],
        )

        if completed:
            self._award_generic_xp(student_id, int(quest.get("reward_xp", 30)))

    def refresh_leaderboard(self) -> None:
        """Recompute global leaderboard ranks from student XP."""
        students = self.repo.client.table("students").select("id, xp").order("xp", desc=True).execute().data or []
        for rank, row in enumerate(students, start=1):
            self.repo.upsert(
                "leaderboard",
                {
                    "student_id": row["id"],
                    "xp": int(row.get("xp", 0)),
                    "rank": rank,
                },
                on_conflict="student_id",
            )

    def _ensure_daily_quests(self, student_id: str) -> None:
        """Seed today's quests when absent."""
        today = date.today().isoformat()
        quests = [
            {"title": "Today's Quest: Read 1 lesson", "target": 1, "quest_type": "THEORY", "reward_xp": 30},
            {"title": "Today's Quest: Pass 1 quiz", "target": 1, "quest_type": "QUIZ", "reward_xp": 30},
            {"title": "Today's Quest: Log in today", "target": 1, "quest_type": "LOGIN", "reward_xp": 30},
        ]
        for quest in quests:
            self.repo.client.table("daily_quests").upsert(
                {
                    "student_id": student_id,
                    "title": quest["title"],
                    "target": quest["target"],
                    "progress": 0,
                    "reward_xp": quest["reward_xp"],
                    "completed": False,
                    "quest_type": quest["quest_type"],
                    "quest_date": today,
                },
                on_conflict="student_id,quest_type,quest_date",
            ).execute()

    def _check_foundation_achievements(self, student_id: str) -> None:
        """Grant minimal set of achievements supported by current MVP data."""
        completed_topics = self.repo.select("progress", "id, topic_id", student_id=student_id, status="COMPLETED")
        if completed_topics:
            self._grant_achievement(student_id, "First Steps")

        perfect_count = len(
            self.repo.select("xp_logs", "id", student_id=student_id, action="QUIZ_PERFECT")
        )
        if perfect_count >= 5:
            self._grant_achievement(student_id, "Quiz Hero")

        pointer_topic = self.repo.client.table("topics").select("id").eq("title", "Pointers & Pointers - Arrays").limit(1).execute().data or []
        if pointer_topic:
            topic_id = int(pointer_topic[0]["id"])
            pointer_completed = self.repo.select(
                "progress",
                "id",
                student_id=student_id,
                topic_id=topic_id,
                status="COMPLETED",
            )
            if pointer_completed:
                self._grant_achievement(student_id, "Pointer Master")

        coding_pass_count = (
            self.repo.client.table("coding_submissions")
            .select("id", count="exact")
            .eq("student_id", student_id)
            .eq("passed", True)
            .execute()
            .count
            or 0
        )
        if int(coding_pass_count) >= 20:
            self._grant_achievement(student_id, "Coding Warrior")

    def _grant_achievement(self, student_id: str, achievement_name: str) -> None:
        """Grant one named achievement if it exists and is not already earned."""
        achievement_rows = (
            self.repo.client.table("achievements").select("id").eq("name", achievement_name).limit(1).execute().data
            or []
        )
        if not achievement_rows:
            return
        achievement_id = achievement_rows[0]["id"]
        self.repo.client.table("student_achievements").upsert(
            {"student_id": student_id, "achievement_id": achievement_id},
            on_conflict="student_id,achievement_id",
        ).execute()

    def _award_generic_xp(self, student_id: str, xp_delta: int) -> None:
        """Award XP for non-topic gamification events and resync student state."""
        student = self._get_student_row(student_id)
        self.repo.update("students", {"xp": int(student.get("xp", 0)) + xp_delta}, id=student_id)
        self.sync_student_state(student_id)

    def _update_skill_tree(self, student_id: str, topic_title: str, score: int) -> None:
        """Map topic performance to one or more skill tree dimensions."""
        row = (
            self.repo.client.table("skill_tree_progress")
            .select("*")
            .eq("student_id", student_id)
            .limit(1)
            .execute()
            .data
            or [{
                "student_id": student_id,
                "syntax_score": 0,
                "problem_solving_score": 0,
                "debugging_score": 0,
                "memory_management_score": 0,
                "oop_score": 0,
            }]
        )[0]

        payload = {
            "student_id": student_id,
            "syntax_score": int(row.get("syntax_score", 0)),
            "problem_solving_score": int(row.get("problem_solving_score", 0)),
            "debugging_score": int(row.get("debugging_score", 0)),
            "memory_management_score": int(row.get("memory_management_score", 0)),
            "oop_score": int(row.get("oop_score", 0)),
        }
        gain = 10 if score >= 80 else 4
        lower_topic = topic_title.lower()

        if any(keyword in lower_topic for keyword in ["data types", "operators", "decision", "repetition", "enum"]):
            payload["syntax_score"] = min(payload["syntax_score"] + gain, 100)
        if any(keyword in lower_topic for keyword in ["functions", "arrays", "strings", "struct"]):
            payload["problem_solving_score"] = min(payload["problem_solving_score"] + gain, 100)
        if any(keyword in lower_topic for keyword in ["pointers", "memory"]):
            payload["memory_management_score"] = min(payload["memory_management_score"] + gain, 100)
            payload["debugging_score"] = min(payload["debugging_score"] + max(gain // 2, 1), 100)
        if any(keyword in lower_topic for keyword in ["objects", "inheritance", "polymorphism", "encapsulation", "const objects"]):
            payload["oop_score"] = min(payload["oop_score"] + gain, 100)

        self.repo.client.table("skill_tree_progress").upsert(payload, on_conflict="student_id").execute()

    @staticmethod
    def _world_map() -> list[dict[str, str]]:
        """Return static adventure world definitions for minimal UI map."""
        return [
            {"world": "World 1: C Fundamentals", "land": "Variables Village / Data Type Forest / Operator Mountain"},
            {"world": "World 2: Arrays", "land": "Array Kingdom"},
            {"world": "World 3: Functions", "land": "Function Castle"},
            {"world": "World 4: Pointers", "land": "Pointer Dungeon"},
            {"world": "World 5: Structures", "land": "Struct City"},
            {"world": "World 6: OOP", "land": "OOP Empire"},
        ]

    def _get_student_row(self, student_id: str) -> dict:
        """Fetch raw student row for internal gamification operations."""
        rows = self.repo.select("students", "*", id=student_id)
        if not rows:
            raise ValueError("Student not found")
        return rows[0]