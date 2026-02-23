"""Add assignments and submissions tables

Revision ID: 0008_add_assignments_submissions
Revises: 0007_add_users_mfa_enabled
Create Date: 2026-02-22
"""

from collections.abc import Sequence

from alembic import op

from app.core.database import Base

# Ensure model modules are imported so metadata contains every table.
import app.modules.auth.models  # noqa: F401
import app.modules.certificates.models  # noqa: F401
import app.modules.courses.models  # noqa: F401
import app.modules.enrollments.models  # noqa: F401
import app.modules.files.models  # noqa: F401
import app.modules.quizzes.models  # noqa: F401
import app.modules.users.models  # noqa: F401
import app.modules.assignments.models.models  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "0008_add_assignments_submissions"
down_revision: str | None = "0007_add_users_mfa_enabled"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)