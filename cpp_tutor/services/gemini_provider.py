"""Gemini provider implementation using Google Generative Language REST API."""

from __future__ import annotations

import requests

from cpp_tutor.config import settings
from cpp_tutor.services.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):
    """Primary LLM provider backed by Gemini."""

    name = "gemini"

    def generate_text(
        self,
        *,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 900,
    ) -> str:
        if not settings.gemini_api_key:
            raise ValueError("Missing GEMINI_API_KEY")

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )

        prompt = f"{system_prompt}\n\n{user_prompt}".strip()
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        response = requests.post(
            endpoint,
            json=payload,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts or "text" not in parts[0]:
            raise RuntimeError("Gemini returned empty content")

        return parts[0]["text"].strip()
