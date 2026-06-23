"""Reusable auth guard for Streamlit pages."""

from __future__ import annotations

import streamlit as st


def require_authentication() -> dict:
    """Ensure user is logged in before rendering page."""
    user = st.session_state.get("user")
    if not user:
        st.warning("Please login to access this page.")
        st.switch_page("app.py")
        st.stop()
    return user
