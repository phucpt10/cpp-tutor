"""Streamlit entrypoint for AI C/C++ Tutor Adventure."""

from __future__ import annotations

import sys
from pathlib import Path

from postgrest.exceptions import APIError
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cpp_tutor.services.auth_service import AuthService
from cpp_tutor.services.gamification_service import GamificationService, LoginRewardResult
from cpp_tutor.services.progress_service import ProgressService

st.set_page_config(page_title="AI C/C++ Tutor Adventure", page_icon="🎓", layout="wide")


def _is_rls_error(exc: Exception) -> bool:
    """Return True when Supabase rejects write due to row-level security policy."""
    if isinstance(exc, APIError):
        payload = getattr(exc, "args", [None])
        if payload and isinstance(payload[0], dict):
            if str(payload[0].get("code", "")) == "42501":
                return True
            return "row-level security" in str(payload[0].get("message", "")).lower()
    return "row-level security" in str(exc).lower()


def _init_session() -> None:
    """Initialize session defaults."""
    st.session_state.setdefault("user", None)
    # Check for admin access via environment or explicit flag
    # In production, integrate with proper role-based access control
    import os
    st.session_state.setdefault("is_admin", os.getenv("ADMIN_MODE", "false").lower() == "true")


def _render_sidebar_nav() -> None:
    """Render custom sidebar navigation menu."""
    with st.sidebar:
        st.markdown("### 🎮 Hành Trình Học Tập")
        
        # Game flow menu - main navigation
        st.markdown("**📚 Khóa Học Chính:**")
        st.page_link("pages/theory.py", label="📘 Học Lý Thuyết", icon="📘")
        st.page_link("pages/quiz.py", label="🧠 Kiểm Tra", icon="🧠")
        st.page_link("pages/practice.py", label="💻 Luyện Code", icon="💻")
        st.page_link("pages/boss_battle.py", label="🐉 Thử Thách Boss", icon="🐉")
        
        st.divider()
        
        # Other features
        st.markdown("**🔍 Theo Dõi Tiến Độ:**")
        st.page_link("pages/dashboard.py", label="📊 Dashboard", icon="📊")
        st.page_link("pages/profile.py", label="👤 Hồ Sơ", icon="👤")
        
        # Admin link (if user has permission)
        if st.session_state.get("is_admin", False):
            st.divider()
            st.markdown("**⚙️ Quản Trị:**")
            st.page_link("pages/admin.py", label="⚙️ Admin Panel", icon="⚙️")
        
        st.divider()
        
        # Help & Info
        st.markdown("**❓ Trợ Giúp:**")
        with st.expander("📖 Hướng Dẫn Chi Tiết"):
            st.markdown("""
            ### 📖 Cách Chơi AI C/C++ Tutor Adventure
            
            **Thứ tự học (Quan trọng):**
            
            1. **📘 Học Lý Thuyết**
               - Lên bài học mới từ đầu
               - Học qua nội dung AI tạo
               - Nhận +10 XP
            
            2. **🧠 Làm Quiz**
               - Kiểm tra hiểu biết (5 câu hỏi)
               - Vượt 80% để mở Practice
               - Nhận +50-100 XP tùy điểm
            
            3. **💻 Luyện Code**
               - Bài tập coding thực hành
               - Giúp ghi nhớ kiến thức
               - Nhận +50 XP
            
            4. **🐉 Thách Thức Boss**
               - 10 MCQ + 1 bài code challenge
               - Điểm >= 80% để chiến thắng
               - Nhận +200 XP và badge
            
            **💡 Mẹo:**
            - Cố gắng vượt qua từng giai đoạn
            - Xem lại Dashboard để kiểm tra tiến độ
            - Nhân XP nhiều → Tăng level nhanh
            """)
        
        st.divider()
        st.caption("v1.0 - AI C/C++ Tutor Adventure")



def _render_logged_in_home() -> None:
    """Render home view after authentication."""
    user = st.session_state["user"]
    st.title("AI C/C++ Tutor Adventure")
    st.caption("Phase 1 MVP - Theory, Quiz, Progress, XP, Authentication")

    # Hướng dẫn (expandable section ở đầu)
    with st.expander("📖 Hướng dẫn chơi", expanded=False):
        st.markdown("""
        **Cách chơi AI C/C++ Tutor Adventure:**
        
        1. **📘 Theory (Học Lý Thuyết)** - Bắt đầu ở đây!
           - Học kiến thức cơ bản C/C++ qua các bài lý thuyết do AI tạo
           - Nhận +10 XP khi hoàn thành bài học

        2. **🧠 Quiz (Kiểm Tra Hiểu Biết)**
           - Làm bài kiểm tra 5 câu trắc nghiệm sau khi học lý thuyết
           - Vượt qua 80% để mở khóa bài luyện tập
           - Nhận XP dựa trên điểm số (tối đa +100 XP)

        3. **💻 Practice (Luyện Code)**
           - Làm bài tập coding sau khi vượt qua Quiz
           - Thử thách bản thân viết code theo yêu cầu
           - Nhận +50 XP khi hoàn thành

        4. **🐉 Boss Battle (Trận Chiến Cuối Cùng)**
           - Sau khi hoàn thành Practice, hãy thách thức Boss!
           - 10 câu hỏi trắc nghiệm + 1 bài coding challenge
           - Nhận +200 XP nếu chiến thắng

        **💡 Mẹo:** Theo thứ tự Theory → Quiz → Practice → Boss Battle để tiến bộ nhanh nhất!
        """)

    st.success(f"Logged in as: {user['email']}")
    
    # Display student info
    info_cols = st.columns([1, 1, 1])
    with info_cols[0]:
        st.write(f"**Student Code:** {user.get('student_code', 'N/A')}")
    with info_cols[1]:
        st.write(f"**Full Name:** {user.get('full_name', 'N/A')}")
    with info_cols[2]:
        if user.get('class'):
            st.write(f"**Class:** {user.get('class', 'N/A')}")
    
    st.markdown("---")

    # Menu chính theo thứ tự game
    st.subheader("🎮 Bắt Đầu Học Tập")
    c1, c2, c3, c4 = st.columns(4)
    c1.page_link("pages/theory.py", label="📘 Theory", icon="📘")
    c2.page_link("pages/quiz.py", label="🧠 Quiz", icon="🧠")
    c3.page_link("pages/practice.py", label="💻 Practice", icon="💻")
    c4.page_link("pages/boss_battle.py", label="🐉 Boss Battle", icon="🐉")

    st.markdown("---")

    # Chức năng khác
    st.subheader("🔧 Chức Năng Khác")
    c5, c6 = st.columns(2)
    c5.page_link("pages/dashboard.py", label="📊 Dashboard", icon="📊")
    c6.page_link("pages/profile.py", label="👤 Profile", icon="👤")

    # Admin link nếu có quyền
    if st.session_state.get("is_admin", False):
        st.divider()
        st.page_link("pages/admin.py", label="⚙️ Admin Dashboard", icon="⚙️")

    st.markdown("---")

    # Logout button (cuối cùng)
    if st.button("Logout", type="secondary"):
        AuthService().logout()
        st.session_state["user"] = None
        st.rerun()


def _render_auth_form() -> None:
    """Render identity form (no password required)."""
    auth_service = AuthService()
    progress_service = ProgressService()
    gamification_service = GamificationService()

    st.title("AI C/C++ Tutor Adventure")
    st.caption("Nhập MSSV, email, họ tên, lớp để định danh trước khi bắt đầu học")

    with st.form("identity_form"):
        student_code = st.text_input("Student Code (MSSV)")
        email = st.text_input("Email")
        full_name = st.text_input("Full Name (Họ Tên)")
        class_name = st.text_input("Class (Lớp)")
        submitted = st.form_submit_button("Bắt đầu học", type="primary")

    if submitted:
        result = auth_service.login(
            email=email.strip(),
            student_code=student_code.strip(),
            full_name=full_name.strip(),
            class_name=class_name.strip(),
        )
        if result.success and result.user_id and result.email:
            progress_service.bootstrap_student(
                user_id=result.user_id,
                email=result.email,
                student_code=student_code.strip(),
                full_name=full_name.strip(),
                class_name=class_name.strip(),
            )
            try:
                login_reward = gamification_service.handle_login(result.user_id)
            except Exception as exc:  # noqa: BLE001
                if _is_rls_error(exc):
                    login_reward = LoginRewardResult(
                        awarded=False,
                        xp_awarded=0,
                        streak_days=0,
                        energy=100,
                    )
                    st.warning(
                        "Supabase RLS đang chặn một số bảng gamification. "
                        "Bạn vẫn có thể học, nhưng quest/leaderboard có thể chưa cập nhật."
                    )
                else:
                    raise
            st.session_state["user"] = {
                "id": result.user_id,
                "email": result.email,
                "student_code": student_code.strip(),
                "full_name": full_name.strip(),
                "class": class_name.strip(),
            }
            st.session_state["login_reward"] = {
                "awarded": login_reward.awarded,
                "xp_awarded": login_reward.xp_awarded,
                "streak_days": login_reward.streak_days,
                "energy": login_reward.energy,
            }
            st.success("Định danh thành công")
            st.rerun()
        else:
            st.error(result.message)


_init_session()
_render_sidebar_nav()

if st.session_state.get("user"):
    _render_logged_in_home()
else:
    _render_auth_form()
