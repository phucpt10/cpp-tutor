"""Abstractions for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Provider contract for text generation."""

    name: str

    @abstractmethod
    def generate_text(
        self,
        *,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 900,
    ) -> str:
        """Generate text from one provider."""
        raise NotImplementedError
