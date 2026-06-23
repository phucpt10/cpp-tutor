"""Dashboard page for learning overview."""

from __future__ import annotations

import streamlit as st

from cpp_tutor.services.gamification_service import GamificationService
from cpp_tutor.services.progress_service import ProgressService
from cpp_tutor.utils.auth_guard import require_authentication
from cpp_tutor.utils.xp_calculator import progress_to_next_level

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

user = require_authentication()
progress_service = ProgressService()
gamification_service = GamificationService()
student = progress_service.get_student(user["id"])
rows = progress_service.get_topics_with_progress(user["id"])
game_overview = gamification_service.get_overview(user["id"])

completed = [row for row in rows if row["status"] == "COMPLETED"]
unlocked = [row for row in rows if row["status"] == "UNLOCKED"]

st.title("Learning Dashboard")

login_reward = st.session_state.pop("login_reward", None)
if login_reward and login_reward.get("awarded"):
    st.success(
        f"Daily login reward: +{login_reward['xp_awarded']} XP | Streak: {login_reward['streak_days']} day(s) | Energy reset: {login_reward['energy']}"
    )

col1, col2, col3, col4 = st.columns(4)
col1.metric("Student", student.full_name)
col2.metric("XP", student.xp)
level, progress_points, target_points = progress_to_next_level(student.xp)
col3.metric("Current Level", f"{level} - {game_overview['title']}")
col4.metric("Total Score", student.total_score)

stat1, stat2, stat3 = st.columns(3)
stat1.metric("Completed Topics", len(completed))
stat2.metric("Streak Days", game_overview["streak_days"])
stat3.metric("Energy", game_overview["energy"])

if target_points:
    st.progress(min(progress_points / target_points, 1.0), text=f"Progress to next level: {progress_points}/{target_points} XP")
else:
    st.success("Max level reached")

st.subheader("Topics")
for row in rows:
    icon = "🔒"
    if row["status"] == "UNLOCKED":
        icon = "🔓"
    elif row["status"] == "COMPLETED":
        icon = "✅"

    st.write(f"{icon} {row['title']}  |  Score: {row['score']}%")

st.info(f"Available topics: {len(unlocked)}")

quest_col, board_col = st.columns(2)

with quest_col:
    st.subheader("Today's Quests")
    for quest in game_overview["daily_quests"]:
        target = max(int(quest.get("target", 1)), 1)
        progress = int(quest.get("progress", 0))
        st.write(f"{quest['title']} | Reward: +{quest['reward_xp']} XP")
        st.progress(min(progress / target, 1.0), text=f"{progress}/{target}")

with board_col:
    st.subheader("Leaderboard")
    leaderboard_rows = []
    for row in game_overview["leaderboard"]:
        student_info = row.get("students") or {}
        leaderboard_rows.append(
            {
                "Rank": row.get("rank", 0),
                "Student": student_info.get("full_name", "Unknown"),
                "Code": student_info.get("student_code", ""),
                "Level": student_info.get("level", 1),
                "XP": row.get("xp", 0),
            }
        )
    if leaderboard_rows:
        st.dataframe(leaderboard_rows, use_container_width=True)
    else:
        st.info("Leaderboard will appear after students start earning XP.")

st.subheader("Adventure World Map")
for world in game_overview["world_map"]:
    st.write(f"{world['world']}: {world['land']}")
