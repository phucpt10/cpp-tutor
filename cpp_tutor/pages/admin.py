"""Admin dashboard for classroom progress tracking and analytics."""

from __future__ import annotations

import streamlit as st

from cpp_tutor.services.admin_service import AdminService

# Page config
st.set_page_config(page_title="Admin Dashboard", page_icon="📊", layout="wide")

# Simple auth: check if admin flag in session or env var
def _check_admin_access() -> bool:
    """Verify admin access (simplified for demo)."""
    # In production, integrate with proper role-based access control
    is_admin = st.session_state.get("is_admin", False)
    if not is_admin:
        st.warning("⚠️ Admin access required. Contact instructor.")
        st.stop()
    return True


def _render_admin_dashboard() -> None:
    """Render full admin analytics dashboard."""
    st.title("📊 Admin Dashboard - Class Progress")
    st.caption("Classroom analytics and student progress tracking")

    admin_service = AdminService()

    # Get all data
    class_overview = admin_service.get_class_overview()
    students_progress = admin_service.get_all_students_progress()
    topic_stats = admin_service.get_topic_completion_stats()
    leaderboard_top10 = admin_service.get_leaderboard_top_n(10)

    # Section 1: Class Overview
    st.heading("1️⃣ Class Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", class_overview.total_students)
    col2.metric("Avg XP", f"{class_overview.avg_xp:.0f}")
    col3.metric("Avg Level", f"{class_overview.avg_level:.1f}")
    col4.metric("Avg Score", f"{class_overview.avg_total_score:.1f}%")

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"✅ Most Completed Topic: **{class_overview.top_topic}**")
    with col_b:
        st.warning(f"⚠️ Bottleneck Topic: **{class_overview.bottleneck_topic}**")

    st.divider()

    # Section 2: Student Progress Table
    st.heading("2️⃣ Student Progress Details")
    if students_progress:
        # Prepare dataframe
        student_data = []
        for stat in students_progress:
            student_data.append(
                {
                    "Student Code": stat.student_code,
                    "Full Name": stat.full_name,
                    "Email": stat.email,
                    "XP": stat.xp,
                    "Level": stat.level,
                    "Streak": stat.streak_days,
                    "Total Score": f"{stat.total_score}%",
                    "Quiz Done": stat.quiz_completed,
                    "Practice Passed": stat.practice_passed,
                    "Boss Defeated": stat.boss_defeated,
                    "Achievements": stat.achievements_count,
                }
            )

        st.dataframe(student_data, use_container_width=True, hide_index=True)
    else:
        st.info("No student data available yet.")

    st.divider()

    # Section 3: Topic Completion Heatmap
    st.heading("3️⃣ Topic Completion & Performance")
    if topic_stats:
        topic_data = []
        for stat in topic_stats:
            topic_data.append(
                {
                    "Topic": stat.topic_title,
                    "Completed": stat.completed,
                    "In Progress": stat.in_progress,
                    "Locked": stat.locked,
                    "Completion %": f"{stat.completion_rate:.1f}%",
                    "Avg Score": f"{stat.avg_score:.1f}%",
                }
            )

        st.dataframe(topic_data, use_container_width=True, hide_index=True)
    else:
        st.info("No topic data available.")

    st.divider()

    # Section 4: Leaderboard Top 10
    st.heading("4️⃣ Leaderboard - Top 10")
    if leaderboard_top10:
        leaderboard_data = []
        for entry in leaderboard_top10:
            leaderboard_data.append(
                {
                    "Rank": entry["rank"],
                    "Student Code": entry["student_code"],
                    "Name": entry["full_name"],
                    "Email": entry["email"],
                    "XP": entry["xp"],
                }
            )

        st.dataframe(leaderboard_data, use_container_width=True, hide_index=True)
    else:
        st.info("Leaderboard is empty.")

    st.divider()

    # Section 5: Export Option
    st.heading("5️⃣ Quick Export")
    col_export1, col_export2, col_export3 = st.columns(3)

    with col_export1:
        if st.button("📥 Export Student Progress (CSV)", use_container_width=True):
            import csv
            from io import StringIO

            output = StringIO()
            if students_progress:
                writer = csv.DictWriter(
                    output,
                    fieldnames=[
                        "student_code",
                        "full_name",
                        "email",
                        "xp",
                        "level",
                        "total_score",
                        "quiz_completed",
                        "practice_passed",
                        "boss_defeated",
                        "achievements",
                    ],
                )
                writer.writeheader()
                for stat in students_progress:
                    writer.writerow(
                        {
                            "student_code": stat.student_code,
                            "full_name": stat.full_name,
                            "email": stat.email,
                            "xp": stat.xp,
                            "level": stat.level,
                            "total_score": stat.total_score,
                            "quiz_completed": stat.quiz_completed,
                            "practice_passed": stat.practice_passed,
                            "boss_defeated": stat.boss_defeated,
                            "achievements": stat.achievements_count,
                        }
                    )
            st.download_button(
                label="📥 Download CSV",
                data=output.getvalue(),
                file_name="class_progress.csv",
                mime="text/csv",
            )

    with col_export2:
        if st.button("📊 Export Topic Stats (CSV)", use_container_width=True):
            import csv
            from io import StringIO

            output = StringIO()
            if topic_stats:
                writer = csv.DictWriter(
                    output,
                    fieldnames=[
                        "topic",
                        "completed",
                        "in_progress",
                        "locked",
                        "completion_rate",
                        "avg_score",
                    ],
                )
                writer.writeheader()
                for stat in topic_stats:
                    writer.writerow(
                        {
                            "topic": stat.topic_title,
                            "completed": stat.completed,
                            "in_progress": stat.in_progress,
                            "locked": stat.locked,
                            "completion_rate": f"{stat.completion_rate:.1f}%",
                            "avg_score": f"{stat.avg_score:.1f}%",
                        }
                    )
            st.download_button(
                label="📊 Download CSV",
                data=output.getvalue(),
                file_name="topic_stats.csv",
                mime="text/csv",
            )

    st.divider()
    st.caption("ℹ️ Last updated: Real-time from Supabase database")


if __name__ == "__main__":
    _check_admin_access()
    _render_admin_dashboard()
