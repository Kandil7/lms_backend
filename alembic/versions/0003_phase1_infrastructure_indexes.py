"""phase 1 infrastructure indexes

Revision ID: 0003_phase1_infrastructure_indexes
Revises: 0002_phase1_security_and_performance
Create Date: 2026-02-18
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_phase1_infrastructure_indexes"
down_revision: str | None = "0002_phase1_security_and_performance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_lessons_course_lesson_type_order",
        "lessons",
        ["course_id", "lesson_type", "order_index"],
        if_not_exists=True,
    )
    op.create_index("ix_enrollments_course_status", "enrollments", ["course_id", "status"], if_not_exists=True)
    op.create_index("ix_enrollments_student_status", "enrollments", ["student_id", "status"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_enrollments_student_status", table_name="enrollments", if_exists=True)
    op.drop_index("ix_enrollments_course_status", table_name="enrollments", if_exists=True)
    op.drop_index("ix_lessons_course_lesson_type_order", table_name="lessons", if_exists=True)
