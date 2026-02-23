"""Create an instructor user from environment variables.

Usage:
    python scripts/create_instructor.py
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
import sys

# Keep script runnable from repository root.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import session_scope
from app.core.model_registry import load_all_models
from app.core.security import hash_password
from app.modules.users.repositories.user_repository import UserRepository


def _parse_bool_env(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "y", "on"}


def main() -> None:
    load_all_models()

    email = os.getenv("INSTRUCTOR_EMAIL", "instructor@example.com").strip().lower()
    password = os.getenv("INSTRUCTOR_PASSWORD", "InstructorPass123")
    full_name = os.getenv("INSTRUCTOR_FULL_NAME", "Course Instructor")
    update_existing = _parse_bool_env(os.getenv("INSTRUCTOR_UPDATE_EXISTING"), default=False)
    verify_email = _parse_bool_env(os.getenv("INSTRUCTOR_VERIFY_EMAIL"), default=True)
    is_active = _parse_bool_env(os.getenv("INSTRUCTOR_IS_ACTIVE"), default=True)
    email_verified_at = datetime.now(UTC) if verify_email else None

    with session_scope() as db:
        repo = UserRepository(db)
        existing = repo.get_by_email(email)

        if existing and not update_existing:
            print(
                f"Instructor already exists: {email}. "
                "Set INSTRUCTOR_UPDATE_EXISTING=true to update this account."
            )
            return

        if existing:
            repo.update(
                existing,
                full_name=full_name,
                role="instructor",
                password_hash=hash_password(password),
                is_active=is_active,
                email_verified_at=email_verified_at,
            )
            print(f"Updated instructor user: {email}")
            return

        repo.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="instructor",
            is_active=is_active,
            email_verified_at=email_verified_at,
        )
        print(f"Created instructor user: {email}")


if __name__ == "__main__":
    main()
