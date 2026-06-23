"""Centralized application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

try:
    import streamlit as st
except Exception:  # noqa: BLE001
    st = None

load_dotenv()


def _get_secret(name: str, default: str = "") -> str:
    """Read config value from ENV first, then Streamlit secrets."""
    env_value = os.getenv(name)
    if env_value is not None and str(env_value).strip():
        return str(env_value)

    if st is not None:
        try:
            secret_value = st.secrets.get(name)
            if secret_value is not None and str(secret_value).strip():
                return str(secret_value)
        except Exception:  # noqa: BLE001
            pass

    return default


def _get_int(name: str, default: int) -> int:
    """Read int config safely from ENV or Streamlit secrets."""
    raw_value = _get_secret(name, str(default))
    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    app_env: str
    supabase_url: str
    supabase_anon_key: str
    gemini_api_key: str
    openrouter_api_key: str
    groq_api_key: str
    gemini_model: str
    openrouter_model: str
    groq_model: str
    request_timeout_seconds: int

    @staticmethod
    def from_env() -> "Settings":
        """Build settings from environment variables/secrets and validate required values."""
        settings = Settings(
            app_env=_get_secret("APP_ENV", "development"),
            supabase_url=_get_secret("SUPABASE_URL", ""),
            supabase_anon_key=_get_secret("SUPABASE_ANON_KEY", ""),
            gemini_api_key=_get_secret("GEMINI_API_KEY", ""),
            openrouter_api_key=_get_secret("OPENROUTER_API_KEY", ""),
            groq_api_key=_get_secret("GROQ_API_KEY", ""),
            gemini_model=_get_secret("GEMINI_MODEL", "gemini-1.5-flash"),
            openrouter_model=_get_secret(
                "OPENROUTER_MODEL",
                "meta-llama/llama-3.3-70b-instruct:free",
            ),
            groq_model=_get_secret("GROQ_MODEL", "llama-3.1-8b-instant"),
            request_timeout_seconds=_get_int("REQUEST_TIMEOUT_SECONDS", 10),
        )
        settings._validate()
        return settings

    def _validate(self) -> None:
        """Validate required settings for core app dependencies."""
        required = {
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_ANON_KEY": self.supabase_anon_key,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            missing_csv = ", ".join(missing)
            raise ValueError(
                "Missing required environment variables: "
                f"{missing_csv}. On Streamlit Cloud, set these in App Settings -> Secrets."
            )


settings = Settings.from_env()
