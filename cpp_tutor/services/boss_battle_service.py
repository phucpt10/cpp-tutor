"""Boss battle service for generation, evaluation, and persistence."""

from __future__ import annotations

import json
from pathlib import Path

from cpp_tutor.database.supabase_client import SupabaseRepository
from cpp_tutor.models.boss_battle import BossBattle, BossBattleAttemptResult
from cpp_tutor.models.quiz import QuizQuestion
from cpp_tutor.services.llm_router import LLMRouter


class BossBattleService:
    """Provide boss battle generation, grading, and persistence."""

    def __init__(
        self,
        repo: SupabaseRepository | None = None,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self.repo = repo or SupabaseRepository()
        self.llm_router = llm_router or LLMRouter()
        prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
        self.boss_prompt_path = prompts_dir / "boss_battle_prompt.txt"
        self.evaluation_prompt_path = prompts_dir / "boss_battle_evaluation_prompt.txt"

    def generate_boss_battle(self, topic_id: int, topic_title: str) -> BossBattle:
        """Generate and persist a boss battle for the selected topic."""
        boss_row = self._get_boss_row(topic_id)
        template = self.boss_prompt_path.read_text(encoding="utf-8")
        response = self.llm_router.generate_text(
            user_prompt=template.replace("{topic}", topic_title),
            system_prompt="You are a strict JSON generator for boss battle assessments.",
            temperature=0.2,
            max_tokens=2200,
        )
        try:
            payload = self._extract_json(response.text)
            provider_used = response.provider_used
        except Exception:  # noqa: BLE001
            payload = self._fallback_boss_payload(topic_title)
            provider_used = f"fallback:{response.provider_used or 'unknown'}"

        questions = self._parse_questions(payload.get("questions", []))
        coding = payload.get("coding_challenge", {})
        update_payload = {
            "mcq_payload": payload.get("questions", []),
            "coding_title": str(coding.get("title", "Boss Coding Challenge")).strip(),
            "coding_description": str(coding.get("description", "")).strip(),
            "coding_starter_code": str(coding.get("starter_code", "")).strip(),
            "coding_expected_concepts": str(coding.get("expected_concepts", "")).strip(),
            "provider_used": provider_used,
        }
        self.repo.update("boss_battles", update_payload, id=boss_row["id"])
        return BossBattle(
            id=int(boss_row["id"]),
            topic_id=topic_id,
            title=boss_row.get("title", f"{topic_title} Boss"),
            difficulty=boss_row.get("difficulty", "Intermediate"),
            questions=questions,
            coding_title=update_payload["coding_title"],
            coding_description=update_payload["coding_description"],
            coding_starter_code=update_payload["coding_starter_code"],
            coding_expected_concepts=update_payload["coding_expected_concepts"],
            provider_used=provider_used,
        )

    def get_latest_boss_battle(self, topic_id: int) -> BossBattle | None:
        """Return persisted boss battle content if already generated."""
        rows = (
            self.repo.client.table("boss_battles")
            .select("*")
            .eq("topic_id", topic_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return None
        row = rows[0]
        questions_payload = row.get("mcq_payload") or []
        if not questions_payload or not row.get("coding_title"):
            return None
        return BossBattle(
            id=int(row["id"]),
            topic_id=int(row["topic_id"]),
            title=row.get("title", "Boss Battle"),
            difficulty=row.get("difficulty", "Intermediate"),
            questions=self._parse_questions(questions_payload),
            coding_title=row.get("coding_title", "Boss Coding Challenge"),
            coding_description=row.get("coding_description", ""),
            coding_starter_code=row.get("coding_starter_code", ""),
            coding_expected_concepts=row.get("coding_expected_concepts", ""),
            provider_used=row.get("provider_used"),
        )

    def evaluate_boss_battle(
        self,
        *,
        topic_title: str,
        boss_battle: BossBattle,
        answers: list[str],
        submitted_code: str,
    ) -> BossBattleAttemptResult:
        """Evaluate both MCQ and coding portions of a boss battle."""
        mcq_correct = 0
        for question, answer in zip(boss_battle.questions, answers, strict=False):
            if answer == question.answer:
                mcq_correct += 1
        mcq_score = int((mcq_correct / len(boss_battle.questions)) * 100) if boss_battle.questions else 0

        template = self.evaluation_prompt_path.read_text(encoding="utf-8")
        user_prompt = (
            template.replace("{topic}", topic_title)
            .replace("{boss_title}", boss_battle.title)
            .replace("{coding_title}", boss_battle.coding_title)
            .replace("{coding_description}", boss_battle.coding_description)
            .replace("{expected_concepts}", boss_battle.coding_expected_concepts)
            .replace("{submitted_code}", submitted_code)
        )
        response = self.llm_router.generate_text(
            user_prompt=user_prompt,
            system_prompt="You are a strict JSON evaluator for boss battle coding challenges.",
            temperature=0.1,
            max_tokens=1200,
        )
        payload = self._extract_json(response.text)
        coding_score = int(payload.get("score", 0))
        overall_score = int(round((mcq_score + coding_score) / 2))
        passed = overall_score >= 80
        return BossBattleAttemptResult(
            mcq_score=mcq_score,
            coding_score=coding_score,
            overall_score=overall_score,
            passed=passed,
            coding_feedback=str(payload.get("feedback", "")).strip(),
            strengths=[str(item).strip() for item in payload.get("strengths", [])],
            improvements=[str(item).strip() for item in payload.get("improvements", [])],
        )

    def save_attempt(
        self,
        *,
        student_id: str,
        topic_id: int,
        boss_battle_id: int,
        result: BossBattleAttemptResult,
        provider_used: str,
    ) -> None:
        """Persist one boss battle attempt."""
        feedback_parts = [result.coding_feedback]
        if result.strengths:
            feedback_parts.append("Strengths: " + "; ".join(result.strengths))
        if result.improvements:
            feedback_parts.append("Improvements: " + "; ".join(result.improvements))

        self.repo.insert(
            "boss_battle_attempts",
            {
                "student_id": student_id,
                "topic_id": topic_id,
                "boss_battle_id": boss_battle_id,
                "mcq_score": result.mcq_score,
                "coding_score": result.coding_score,
                "overall_score": result.overall_score,
                "passed": result.passed,
                "coding_feedback": "\n".join(part for part in feedback_parts if part),
                "provider_used": provider_used,
            },
        )

    def has_passed_boss_battle(self, student_id: str, topic_id: int) -> bool:
        """Return True if the student already won the boss battle for the topic."""
        rows = (
            self.repo.client.table("boss_battle_attempts")
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

    def has_boss_seed(self, topic_id: int) -> bool:
        """Return True when a boss battle seed exists for the topic."""
        rows = self.repo.select("boss_battles", "id", topic_id=topic_id)
        return bool(rows)

    def _get_boss_row(self, topic_id: int) -> dict:
        """Fetch boss battle seed row for a topic."""
        rows = self.repo.select("boss_battles", "*", topic_id=topic_id)
        if not rows:
            raise ValueError("Boss battle seed not found for selected topic")
        return rows[0]

    @staticmethod
    def _parse_questions(questions_raw: list[dict]) -> list[QuizQuestion]:
        """Parse and validate boss battle MCQs."""
        if len(questions_raw) != 10:
            raise ValueError("Boss battle must return exactly 10 MCQ questions")
        questions: list[QuizQuestion] = []
        for item in questions_raw:
            options = item.get("options", [])
            answer = item.get("answer", "")
            if len(options) != 4:
                raise ValueError("Each boss battle question must have exactly 4 options")
            if answer not in options:
                raise ValueError("Boss battle answer must match one option")
            questions.append(
                QuizQuestion(
                    question=str(item.get("question", "")).strip(),
                    options=[str(option).strip() for option in options],
                    answer=str(answer).strip(),
                    explanation=str(item.get("explanation", "")).strip(),
                )
            )
        return questions

    @staticmethod
    def _fallback_boss_payload(topic_title: str) -> dict:
        """Return safe boss battle when LLM output is invalid JSON."""
        topic = topic_title.lower()
        
        # Generate 10 fallback MCQ questions
        fallback_questions = [
            {
                "question": "What is the primary use of the topic covered in this chapter?",
                "options": ["Organizing data", "Controlling flow", "Managing memory", "Defining algorithms"],
                "answer": "Organizing data",
                "explanation": "This question tests fundamental understanding of the topic.",
            },
            {
                "question": "Which of the following is a best practice when working with this concept?",
                "options": ["Always use defaults", "Follow naming conventions", "Avoid documentation", "Rush implementation"],
                "answer": "Follow naming conventions",
                "explanation": "Code readability and maintainability are essential.",
            },
            {
                "question": "What common mistake should be avoided?",
                "options": ["Being careful", "Testing thoroughly", "Ignoring edge cases", "Planning ahead"],
                "answer": "Ignoring edge cases",
                "explanation": "Edge cases are where most bugs hide.",
            },
            {
                "question": "How can you improve your code with this technique?",
                "options": ["Make it less readable", "Increase efficiency", "Add random comments", "Remove error handling"],
                "answer": "Increase efficiency",
                "explanation": "Better code is more efficient and maintainable.",
            },
            {
                "question": "What is the expected outcome of properly implementing this concept?",
                "options": ["Slower execution", "More bugs", "Cleaner, more maintainable code", "Random behavior"],
                "answer": "Cleaner, more maintainable code",
                "explanation": "Proper implementation leads to better code quality.",
            },
            {
                "question": "When should you use this approach?",
                "options": ["Never", "Always", "When it solves the problem effectively", "Only on Fridays"],
                "answer": "When it solves the problem effectively",
                "explanation": "Use the right tool for the right problem.",
            },
            {
                "question": "What is a limitation of this method?",
                "options": ["It is perfect", "It has specific use cases", "It is always optimal", "It never works"],
                "answer": "It has specific use cases",
                "explanation": "Every technique has its strengths and limitations.",
            },
            {
                "question": "How does this concept relate to program structure?",
                "options": ["Not at all", "Helps organize logic flow", "Is completely unrelated", "Slows everything down"],
                "answer": "Helps organize logic flow",
                "explanation": "Good structure makes programs easier to understand and maintain.",
            },
            {
                "question": "What should you consider when designing with this technique?",
                "options": ["Ignore performance", "Consider scalability", "Avoid testing", "Skip planning"],
                "answer": "Consider scalability",
                "explanation": "Design for growth and future needs.",
            },
            {
                "question": "What is the role of testing in validating this implementation?",
                "options": ["Testing is not needed", "Verify correct behavior", "Only test on production", "Never validate"],
                "answer": "Verify correct behavior",
                "explanation": "Testing ensures your code works as intended.",
            },
        ]
        
        # Determine coding challenge based on topic
        if "variable" in topic or "constant" in topic or "data type" in topic:
            coding_challenge = {
                "title": "Variable Declarations & Usage",
                "description": "Write a C++ program that declares variables of different data types (int, double, char, string), initializes them, and prints their values. Also declare at least one constant using const.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    // Declare variables and constants here\n    \n    // Print values here\n    \n    return 0;\n}\n",
                "expected_concepts": "variables, constants, data types, input/output",
            }
        elif "operator" in topic:
            coding_challenge = {
                "title": "Operator Calculations",
                "description": "Write a program that takes two integers as input and performs arithmetic operations (addition, subtraction, multiplication, division, modulo). Display all results.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    int a, b;\n    cout << \"Enter two integers: \";\n    cin >> a >> b;\n    \n    // Perform operations and print results\n    \n    return 0;\n}\n",
                "expected_concepts": "operators, arithmetic, input/output",
            }
        elif "decision" in topic or "if" in topic or "condition" in topic:
            coding_challenge = {
                "title": "Grade Evaluation System",
                "description": "Write a program that reads a student's score (0-100) and prints the corresponding grade: A (90-100), B (80-89), C (70-79), D (60-69), F (below 60). Use if-else statements.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    int score;\n    cout << \"Enter score: \";\n    cin >> score;\n    \n    // Determine and print grade\n    \n    return 0;\n}\n",
                "expected_concepts": "if-else, conditions, logic",
            }
        elif "loop" in topic or "repetition" in topic or "while" in topic or "for" in topic:
            coding_challenge = {
                "title": "Multiplication Table Generator",
                "description": "Write a program that reads an integer N and prints its multiplication table from 1 to 10 using a loop.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    int n;\n    cout << \"Enter a number: \";\n    cin >> n;\n    \n    // Print multiplication table using a loop\n    \n    return 0;\n}\n",
                "expected_concepts": "loops, iteration, multiplication",
            }
        elif "array" in topic:
            coding_challenge = {
                "title": "Array Operations",
                "description": "Write a program that reads 5 integers into an array, finds and prints the maximum, minimum, and average values.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    int arr[5];\n    \n    // Read 5 integers\n    for (int i = 0; i < 5; i++) {\n        cout << \"Enter integer \" << i+1 << \": \";\n        cin >> arr[i];\n    }\n    \n    // Find max, min, average and print\n    \n    return 0;\n}\n",
                "expected_concepts": "arrays, loops, aggregation",
            }
        elif "string" in topic:
            coding_challenge = {
                "title": "String Manipulation",
                "description": "Write a program that reads a string and counts vowels, consonants, and spaces. Print the results.",
                "starter_code": "#include <iostream>\n#include <string>\nusing namespace std;\n\nint main() {\n    string input;\n    cout << \"Enter a string: \";\n    getline(cin, input);\n    \n    // Count vowels, consonants, spaces\n    \n    return 0;\n}\n",
                "expected_concepts": "strings, character analysis, loops",
            }
        else:
            coding_challenge = {
                "title": "Review & Practice",
                "description": "Write a C++ program that demonstrates the key concepts learned in this chapter. Include appropriate comments explaining your logic.",
                "starter_code": "#include <iostream>\nusing namespace std;\n\nint main() {\n    // Your implementation here\n    \n    return 0;\n}\n",
                "expected_concepts": "chapter review, core concepts, best practices",
            }
        
        return {
            "questions": fallback_questions,
            "coding_challenge": coding_challenge,
        }

    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        """Extract JSON object from raw LLM output."""
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