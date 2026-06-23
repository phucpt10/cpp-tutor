"""Authentication service using student identity (no password required)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from cpp_tutor.database.supabase_client import get_supabase_client


@dataclass(slots=True)
class AuthResult:
    """Simple auth operation result."""

    success: bool
    message: str
    user_id: str | None = None
    email: str | None = None


class AuthService:
    """Identity use-cases for login, profile creation, and logout."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def login(
        self,
        email: str,
        password: str | None = None,
        student_code: str = "",
        full_name: str = "",
        class_name: str = "",
    ) -> AuthResult:
        """Identify student by code/email/name and create profile if missing."""
        del password  # Kept for backward compatibility with old callers.

        email_value = email.strip().lower()
        code_value = student_code.strip()
        name_value = full_name.strip()
        class_value = class_name.strip()

        if not email_value or not code_value or not name_value:
            return AuthResult(
                success=False,
                message="Student code, email, and full name are required",
            )

        try:
            student_rows = (
                self.client.table("students")
                .select("id, student_code, email, full_name, class")
                .eq("student_code", code_value)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
                or []
            )

            if student_rows:
                profile = student_rows[0]
                profile_id = str(profile.get("id", ""))

                update_data = {
                    "email": email_value,
                    "full_name": name_value,
                }
                if class_value:
                    update_data["class"] = class_value

                self.client.table("students").update(
                    update_data
                ).eq("id", profile_id).execute()

                return AuthResult(
                    success=True,
                    message="Login success",
                    user_id=profile_id,
                    email=email_value,
                )

            new_row = self.client.table("students").insert(
                {
                    "id": str(uuid.uuid4()),
                    "student_code": code_value,
                    "email": email_value,
                    "full_name": name_value,
                    "class": class_value or None,
                    "xp": 0,
                    "total_score": 0,
                }
            ).execute().data or []

            created = new_row[0] if new_row else {}
            return AuthResult(
                success=True,
                message="Identity verified. Student profile created.",
                user_id=str(created.get("id", "")),
                email=email_value,
            )
        except Exception as exc:  # noqa: BLE001
            return AuthResult(success=False, message=f"Login failed: {exc}")

    def signup(
        self,
        email: str,
        password: str | None = None,
        student_code: str = "",
        full_name: str = "",
        class_name: str = "",
    ) -> AuthResult:
        """Backward-compatible alias to identity login/create flow."""
        return self.login(
            email=email,
            password=password,
            student_code=student_code,
            full_name=full_name,
            class_name=class_name,
        )

    def logout(self) -> None:
        """No-op logout for identity-only mode."""
        try:
            self.client.auth.sign_out()
        except Exception:  # noqa: BLE001
            pass
