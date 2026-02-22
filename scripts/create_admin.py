"""Create an admin user from environment variables.

Usage:
    python scripts/create_admin.py
"""

import os
from pathlib import Path
import sys
from datetime import UTC, datetime

# Keep script runnable from repository root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import session_scope
from app.core.model_registry import load_all_models
from app.modules.users.repositories.user_repository import UserRepository
from app.core.security import hash_password


def main() -> None:
    load_all_models()

    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "AdminPass123")
    full_name = os.getenv("ADMIN_FULL_NAME", "System Admin")

    with session_scope() as db:
        repo = UserRepository(db)
        existing = repo.get_by_email(email)
        if existing:
            print(f"Admin user already exists: {email}")
            return

        repo.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="admin",
            is_active=True,
            email_verified_at=datetime.now(UTC),
        )

    print(f"Created admin user: {email}")


if __name__ == "__main__":
    main()
