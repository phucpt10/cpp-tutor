"""Profile page with XP details and activity logs."""

from __future__ import annotations

import streamlit as st

from cpp_tutor.database.supabase_client import SupabaseRepository
from cpp_tutor.services.gamification_service import GamificationService
from cpp_tutor.services.progress_service import ProgressService
from cpp_tutor.utils.auth_guard import require_authentication
from cpp_tutor.utils.xp_calculator import level_from_xp, title_from_level

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

user = require_authentication()
service = ProgressService()
gamification_service = GamificationService()
repo = SupabaseRepository()
student = service.get_student(user["id"])
topic_rows = service.get_topics_with_progress(user["id"])
game_overview = gamification_service.get_overview(user["id"])

st.title("Student Profile")
st.write(f"Student Code: {student.student_code}")
st.write(f"Email: {student.email}")
st.write(f"Full Name: {student.full_name}")
if student.class_name:
    st.write(f"Class: {student.class_name}")
st.write(f"XP: {student.xp}")
st.write(f"Level: {level_from_xp(student.xp)} - {title_from_level(student.level)}")
st.write(f"Streak Days: {student.streak_days}")
st.write(f"Energy: {student.energy}")
st.write(f"Total Score: {student.total_score}")

st.subheader("Topic Scores")
st.dataframe(
    [
        {
            "topic_id": row["id"],
            "topic": row["title"],
            "status": row["status"],
            "score": row["score"],
        }
        for row in topic_rows
    ],
    use_container_width=True,
)

st.subheader("Achievements")
achievement_rows = []
for row in game_overview["achievements"]:
    achievement = row.get("achievements") or {}
    achievement_rows.append(
        {
            "badge": achievement.get("badge_icon", ""),
            "name": achievement.get("name", ""),
            "description": achievement.get("description", ""),
            "earned_at": row.get("earned_at", ""),
        }
    )
if achievement_rows:
    st.dataframe(achievement_rows, use_container_width=True)
else:
    st.info("No achievements yet")

st.subheader("Skill Tree")
skill_tree = game_overview["skill_tree"]
skill_labels = {
    "syntax_score": "Syntax",
    "problem_solving_score": "Problem Solving",
    "debugging_score": "Debugging",
    "memory_management_score": "Memory Management",
    "oop_score": "OOP",
}
for key, label in skill_labels.items():
    value = int(skill_tree.get(key, 0))
    st.progress(value / 100, text=f"{label}: {value}/100")

logs = (
    repo.client.table("xp_logs")
    .select("action, xp_delta, created_at, topic_id")
    .eq("student_id", user["id"])
    .order("created_at", desc=True)
    .limit(20)
    .execute()
    .data
    or []
)

st.subheader("Recent XP Events")
if logs:
    st.dataframe(logs, use_container_width=True)
else:
    st.info("No XP events yet")
