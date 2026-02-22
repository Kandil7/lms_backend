"""Create or update a user from CLI arguments.

Examples:
    python scripts/create_user.py --email instructor@example.com --password StrongPass123 --full-name "Instructor One" --role instructor
    python scripts/create_user.py --email instructor@example.com --password StrongPass123 --full-name "Instructor One" --role instructor --update-existing
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys

# Keep script runnable from repository root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import session_scope
from app.core.model_registry import load_all_models
from app.core.permissions import Role
from app.core.security import hash_password
from app.modules.users.repositories.user_repository import UserRepository


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(
        "Expected boolean value (true/false/1/0/yes/no)"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or update a user account (student/instructor/admin)."
    )
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--full-name", required=True, help="User full name")
    parser.add_argument(
        "--role",
        required=True,
        choices=[Role.STUDENT.value, Role.INSTRUCTOR.value, Role.ADMIN.value],
        help="User role",
    )
    parser.add_argument(
        "--is-active",
        type=_parse_bool,
        default=True,
        help="Whether user is active (default: true)",
    )
    parser.add_argument(
        "--verify-email",
        type=_parse_bool,
        default=True,
        help="Set email_verified_at when creating/updating user (default: true)",
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Update role/password/name if user already exists",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    load_all_models()

    email = args.email.strip().lower()
    full_name = args.full_name.strip()
    role = args.role
    password_hash = hash_password(args.password)
    email_verified_at = datetime.now(UTC) if args.verify_email else None

    with session_scope() as db:
        repo = UserRepository(db)
        existing = repo.get_by_email(email)

        if existing and not args.update_existing:
            print(
                f"User already exists: {email}. "
                "Use --update-existing to update this account."
            )
            return

        if existing:
            repo.update(
                existing,
                full_name=full_name,
                role=role,
                password_hash=password_hash,
                is_active=args.is_active,
                email_verified_at=email_verified_at,
            )
            print(f"Updated user: {email} (role={role})")
            return

        repo.create(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            is_active=args.is_active,
            email_verified_at=email_verified_at,
        )
        print(f"Created user: {email} (role={role})")


if __name__ == "__main__":
    main()
