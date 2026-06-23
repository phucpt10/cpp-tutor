"""Practice service for coding exercise generation and evaluation."""

from __future__ import annotations

import json
from pathlib import Path

from cpp_tutor.database.supabase_client import SupabaseRepository
from cpp_tutor.models.practice import CodingExercise, CodingSubmissionResult
from cpp_tutor.services.llm_router import LLMRouter


class PracticeService:
    """Provide practice exercise generation, evaluation, and persistence."""

    def __init__(
        self,
        repo: SupabaseRepository | None = None,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self.repo = repo or SupabaseRepository()
        self.llm_router = llm_router or LLMRouter()
        prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
        self.practice_prompt_path = prompts_dir / "practice_prompt.txt"
        self.evaluation_prompt_path = prompts_dir / "practice_evaluation_prompt.txt"

    def generate_exercise(self, topic_id: int, topic_title: str) -> CodingExercise:
        """Generate and persist one practice exercise for the selected topic."""
        template = self.practice_prompt_path.read_text(encoding="utf-8")
        response = self.llm_router.generate_text(
            user_prompt=template.replace("{topic}", topic_title),
            system_prompt="You are a strict JSON generator for beginner C/C++ practice tasks.",
            temperature=0.2,
            max_tokens=1200,
        )
        try:
            payload = self._extract_json(response.text)
            provider_used = response.provider_used
        except Exception:  # noqa: BLE001
            payload = self._fallback_exercise_payload(topic_title)
            provider_used = f"fallback:{response.provider_used or 'unknown'}"
        exercise = CodingExercise(
            id=None,
            topic_id=topic_id,
            title=str(payload.get("title", "Practice Exercise")).strip(),
            description=str(payload.get("description", "")).strip(),
            starter_code=str(payload.get("starter_code", "")).strip(),
            expected_concepts=str(payload.get("expected_concepts", "")).strip(),
            difficulty=str(payload.get("difficulty", "Beginner")).strip() or "Beginner",
            provider_used=provider_used,
        )
        inserted = self.repo.insert(
            "coding_exercises",
            {
                "topic_id": exercise.topic_id,
                "title": exercise.title,
                "description": exercise.description,
                "starter_code": exercise.starter_code,
                "expected_concepts": exercise.expected_concepts,
                "difficulty": exercise.difficulty,
                "provider_used": exercise.provider_used,
            },
        )
        if inserted:
            exercise.id = int(inserted[0]["id"])
        return exercise

    def get_latest_exercise(self, topic_id: int) -> CodingExercise | None:
        """Return the latest generated exercise for a topic, if any."""
        rows = (
            self.repo.client.table("coding_exercises")
            .select("*")
            .eq("topic_id", topic_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return None
        row = rows[0]
        return CodingExercise(
            id=int(row["id"]),
            topic_id=int(row["topic_id"]),
            title=row.get("title", "Practice Exercise"),
            description=row.get("description", ""),
            starter_code=row.get("starter_code", ""),
            expected_concepts=row.get("expected_concepts", ""),
            difficulty=row.get("difficulty", "Beginner"),
            provider_used=row.get("provider_used"),
        )

    def evaluate_submission(
        self,
        *,
        topic_title: str,
        exercise: CodingExercise,
        submitted_code: str,
    ) -> CodingSubmissionResult:
        """Evaluate student code using the LLM router."""
        template = self.evaluation_prompt_path.read_text(encoding="utf-8")
        user_prompt = (
            template.replace("{topic}", topic_title)
            .replace("{title}", exercise.title)
            .replace("{description}", exercise.description)
            .replace("{expected_concepts}", exercise.expected_concepts)
            .replace("{submitted_code}", submitted_code)
        )
        response = self.llm_router.generate_text(
            user_prompt=user_prompt,
            system_prompt="You are a strict but encouraging beginner C/C++ code evaluator. Return JSON only.",
            temperature=0.1,
            max_tokens=1200,
        )
        payload = self._extract_json(response.text)
        return CodingSubmissionResult(
            score=int(payload.get("score", 0)),
            passed=bool(payload.get("passed", False)),
            feedback=str(payload.get("feedback", "")).strip(),
            strengths=[str(item).strip() for item in payload.get("strengths", [])],
            improvements=[str(item).strip() for item in payload.get("improvements", [])],
        )

    def save_submission(
        self,
        *,
        student_id: str,
        topic_id: int,
        exercise_id: int,
        submitted_code: str,
        result: CodingSubmissionResult,
        provider_used: str,
    ) -> None:
        """Persist evaluated coding submission."""
        feedback_parts = [result.feedback]
        if result.strengths:
            feedback_parts.append("Strengths: " + "; ".join(result.strengths))
        if result.improvements:
            feedback_parts.append("Improvements: " + "; ".join(result.improvements))

        self.repo.insert(
            "coding_submissions",
            {
                "student_id": student_id,
                "topic_id": topic_id,
                "exercise_id": exercise_id,
                "submitted_code": submitted_code,
                "score": result.score,
                "feedback": "\n".join(part for part in feedback_parts if part),
                "passed": result.passed,
                "provider_used": provider_used,
            },
        )

    def has_passed_practice(self, student_id: str, topic_id: int) -> bool:
        """Return True when student has a passing practice submission for the topic."""
        rows = (
            self.repo.client.table("coding_submissions")
            .select("id")
            .eq("student_id", student_id)
            .eq("topic_id", topic_id)
            .eq("passed", True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return bool(rows)

    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        """Extract a JSON object from raw LLM output."""
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            lines = [line for line in lines if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in LLM response")
        return json.loads(text[start : end + 1])

    @staticmethod
    def _fallback_exercise_payload(topic_title: str) -> dict:
        """Return a safe beginner exercise when the LLM output is invalid JSON."""
        topic = topic_title.lower()

        if "variable" in topic or "constant" in topic:
            return {
                "title": "Print Variables and Constants",
                "description": "Declare one integer variable and one constant, then print both values.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    // TODO: declare an int variable and a constant\n    return 0;\n}\n",
                "expected_concepts": "variables, constants, output",
                "difficulty": "Beginner",
            }

        if "input" in topic or "output" in topic:
            return {
                "title": "Read and Display Student Info",
                "description": "Read a student's name and age, then print them back in a friendly format.",
                "starter_code": "#include <iostream>\n#include <string>\nusing namespace std;\n\nint main() {\n    string name;\n    int age;\n    // TODO: read name and age, then print them\n    return 0;\n}\n",
                "expected_concepts": "input, output, variables, string",
                "difficulty": "Beginner",
            }

        if "if" in topic or "decision" in topic or "condition" in topic:
            return {
                "title": "Check Pass or Fail",
                "description": "Read a score and print PASS if it is at least 80, otherwise print FAIL.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    int score;\n    // TODO: read score and use if-else\n    return 0;\n}\n",
                "expected_concepts": "if-else, comparison, output",
                "difficulty": "Beginner",
            }

        if "loop" in topic or "repetition" in topic or "for" in topic or "while" in topic:
            return {
                "title": "Print Numbers 1 to 5",
                "description": "Use a loop to print numbers from 1 to 5 on separate lines.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    // TODO: use a loop to print 1 to 5\n    return 0;\n}\n",
                "expected_concepts": "loops, counter, output",
                "difficulty": "Beginner",
            }

        if "array" in topic:
            return {
                "title": "Find the Largest Number",
                "description": "Store 5 integers in an array and print the largest value.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    int numbers[5];\n    // TODO: read 5 numbers and find the largest\n    return 0;\n}\n",
                "expected_concepts": "arrays, loops, comparison",
                "difficulty": "Beginner",
            }

        if "string" in topic:
            return {
                "title": "Count Vowels in a Word",
                "description": "Read a word and count how many vowels it contains.",
                "starter_code": "#include <iostream>\n#include <string>\nusing namespace std;\n\nint main() {\n    string word;\n    // TODO: read a word and count vowels\n    return 0;\n}\n",
                "expected_concepts": "strings, loops, conditionals",
                "difficulty": "Beginner",
            }

        return {
            "title": "Practice the Topic",
            "description": f"Create a simple beginner exercise for the topic: {topic_title}.",
            "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    // TODO: solve the exercise\n    return 0;\n}\n",
            "expected_concepts": topic_title,
            "difficulty": "Beginner",
        }