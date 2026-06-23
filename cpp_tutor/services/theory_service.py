"""Theory generation service."""

from __future__ import annotations

from pathlib import Path

from cpp_tutor.services.llm_router import LLMResponse, LLMRouter


class TheoryService:
    """Generate lessons from topic via routed LLM providers."""

    def __init__(self, llm_router: LLMRouter | None = None) -> None:
        self.llm_router = llm_router or LLMRouter()
        self.prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "theory_prompt.txt"

    def generate_theory(self, topic: str) -> LLMResponse:
        """Generate markdown lesson in under 500 words."""
        template = self.prompt_path.read_text(encoding="utf-8")
        user_prompt = template.replace("{topic}", topic)

        system_prompt = (
            "You are an expert C programming tutor for first-year students. "
            "Keep explanations concise, practical, and beginner-friendly."
        )
        return self.llm_router.generate_text(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=900,
        )
