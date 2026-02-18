"""phase 1 remaining critical indexes

Revision ID: 0005_phase1_remaining_indexes
Revises: 0004_phase1_quiz_indexes
Create Date: 2026-02-18
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_phase1_remaining_indexes"
down_revision: str | None = "0004_phase1_quiz_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add index on lesson_id for lesson_progress table (critical for analytics and progress tracking)
    op.create_index(
        "ix_lesson_progress_lesson_id",
        "lesson_progress",
        ["lesson_id"],
        if_not_exists=True,
    )
    
    # Add index on status for enrollments table (critical for analytics queries)
    op.create_index(
        "ix_enrollments_status",
        "enrollments",
        ["status"],
        if_not_exists=True,
    )
    
    # Add composite index on enrollment_id, quiz_id for quiz_attempts (for efficient attempt lookup)
    op.create_index(
        "ix_quiz_attempts_enrollment_quiz",
        "quiz_attempts",
        ["enrollment_id", "quiz_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_quiz_attempts_enrollment_quiz", table_name="quiz_attempts", if_exists=True)
    op.drop_index("ix_enrollments_status", table_name="enrollments", if_exists=True)
    op.drop_index("ix_lesson_progress_lesson_id", table_name="lesson_progress", if_exists=True)