"""Quiz generation and evaluation service."""

from __future__ import annotations

import json
from pathlib import Path

from cpp_tutor.models.quiz import QuizQuestion, QuizResult
from cpp_tutor.services.llm_router import LLMResponse, LLMRouter


class QuizService:
    """Generate and evaluate topic-based quizzes."""

    def __init__(self, llm_router: LLMRouter | None = None) -> None:
        self.llm_router = llm_router or LLMRouter()
        self.prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "quiz_prompt.txt"

    def generate_quiz(self, topic: str) -> tuple[list[QuizQuestion], LLMResponse]:
        """Generate exactly 5 multiple-choice questions in JSON format."""
        template = self.prompt_path.read_text(encoding="utf-8")
        user_prompt = template.replace("{topic}", topic)

        response = self.llm_router.generate_text(
            user_prompt=user_prompt,
            system_prompt="You are a strict JSON generator.",
            temperature=0.1,
            max_tokens=1000,
        )
        questions = self._parse_questions(response.text)
        return questions, response

    def evaluate(self, questions: list[QuizQuestion], answers: list[str]) -> QuizResult:
        """Evaluate student answers and return score summary."""
        total = len(questions)
        correct = 0
        for q, answer in zip(questions, answers, strict=False):
            if answer == q.answer:
                correct += 1

        score = int((correct / total) * 100) if total else 0
        return QuizResult(
            score=score,
            correct=correct,
            total=total,
            passed=score >= 80,
        )

    def _parse_questions(self, raw_text: str) -> list[QuizQuestion]:
        """Parse raw LLM output into validated quiz questions."""
        payload = self._extract_json(raw_text)
        questions_raw = payload.get("questions", [])
        if len(questions_raw) != 5:
            raise ValueError("Quiz generator must return exactly 5 questions")

        questions: list[QuizQuestion] = []
        for item in questions_raw:
            options = item.get("options", [])
            answer = item.get("answer", "")
            if len(options) != 4:
                raise ValueError("Each question must have exactly 4 options")
            if answer not in options:
                raise ValueError("Answer must match one of the options")
            questions.append(
                QuizQuestion(
                    question=item.get("question", "").strip(),
                    options=[str(o).strip() for o in options],
                    answer=str(answer).strip(),
                    explanation=item.get("explanation", "").strip(),
                )
            )
        return questions

    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        """Extract JSON object from plain text or fenced markdown block."""
        text = raw_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            lines = [line for line in lines if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in LLM response")

        json_text = text[start : end + 1]
        return json.loads(json_text)
