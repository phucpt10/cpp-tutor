"""Groq provider implementation using OpenAI-compatible API."""

from __future__ import annotations

import requests

from cpp_tutor.config import settings
from cpp_tutor.services.llm_provider import LLMProvider


class GroqProvider(LLMProvider):
    """Last fallback provider using Groq."""

    name = "groq"

    def generate_text(
        self,
        *,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 900,
    ) -> str:
        if not settings.groq_api_key:
            raise ValueError("Missing GROQ_API_KEY")

        payload = {
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful tutor."},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Groq returned no choices")

        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            raise RuntimeError("Groq returned empty content")

        return content
