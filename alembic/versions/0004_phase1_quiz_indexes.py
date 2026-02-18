"""phase 1 quiz indexes

Revision ID: 0004_phase1_quiz_indexes
Revises: 0003_phase1_infrastructure_indexes
Create Date: 2026-02-18
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_phase1_quiz_indexes"
down_revision: str | None = "0003_phase1_infrastructure_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_quiz_attempts_quiz_status_submitted_at",
        "quiz_attempts",
        ["quiz_id", "status", "submitted_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_quiz_questions_quiz_type_order",
        "quiz_questions",
        ["quiz_id", "question_type", "order_index"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_quiz_questions_quiz_type_order", table_name="quiz_questions", if_exists=True)
    op.drop_index("ix_quiz_attempts_quiz_status_submitted_at", table_name="quiz_attempts", if_exists=True)
