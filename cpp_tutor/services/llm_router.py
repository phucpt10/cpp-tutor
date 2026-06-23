"""LLM router with ordered fallback strategy."""

from __future__ import annotations

from dataclasses import dataclass

from cpp_tutor.services.gemini_provider import GeminiProvider
from cpp_tutor.services.groq_provider import GroqProvider
from cpp_tutor.services.llm_provider import LLMProvider
from cpp_tutor.services.openrouter_provider import OpenRouterProvider


@dataclass(slots=True)
class LLMResponse:
    """Router response including provider metadata."""

    text: str
    provider_used: str


class LLMRouter:
    """Route LLM requests with fallback: Gemini -> OpenRouter -> Groq."""

    def __init__(self, providers: list[LLMProvider] | None = None) -> None:
        self.providers = providers or [
            GeminiProvider(),
            OpenRouterProvider(),
            GroqProvider(),
        ]

    def generate_text(
        self,
        *,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 900,
    ) -> LLMResponse:
        """Try providers in order and return first successful response."""
        last_error: Exception | None = None

        for provider in self.providers:
            try:
                text = provider.generate_text(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return LLMResponse(text=text, provider_used=provider.name)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

        if last_error:
            raise RuntimeError(f"All LLM providers failed. Last error: {last_error}") from last_error
        raise RuntimeError("All LLM providers failed.")
