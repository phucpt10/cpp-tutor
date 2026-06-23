"""Centralized application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


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
        """Build settings from environment variables and validate required values."""
        settings = Settings(
            app_env=os.getenv("APP_ENV", "development"),
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
            ),
            groq_model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")),
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
            raise ValueError(f"Missing required environment variables: {missing_csv}")


settings = Settings.from_env()
