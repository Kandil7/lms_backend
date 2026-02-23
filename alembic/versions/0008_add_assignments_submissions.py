"""add assignments and submissions tables

Revision ID: 0008_add_assignments_submissions
Revises: 0007_add_users_mfa_enabled
Create Date: 2026-02-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_add_assignments_submissions"
down_revision: str | None = "0007_add_users_mfa_enabled"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "assignments" not in tables:
        op.create_table(
            "assignments",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("instructions", sa.Text(), nullable=True),
            sa.Column("course_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("instructor_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'draft'")),
            sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("max_points", sa.Integer(), nullable=True),
            sa.Column("grading_type", sa.String(length=50), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("status IN ('draft','published','archived')", name="ck_assignments_status"),
            sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["instructor_id"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.alter_column("assignments", "status", server_default=None)
        op.alter_column("assignments", "is_published", server_default=None)

    inspector = sa.inspect(bind)
    assignment_indexes = {index["name"] for index in inspector.get_indexes("assignments")}
    if "ix_assignments_course_created_at" not in assignment_indexes:
        op.create_index("ix_assignments_course_created_at", "assignments", ["course_id", "created_at"], if_not_exists=True)
    if "ix_assignments_instructor_created_at" not in assignment_indexes:
        op.create_index(
            "ix_assignments_instructor_created_at",
            "assignments",
            ["instructor_id", "created_at"],
            if_not_exists=True,
        )
    if "ix_assignments_is_published_created_at" not in assignment_indexes:
        op.create_index(
            "ix_assignments_is_published_created_at",
            "assignments",
            ["is_published", "created_at"],
            if_not_exists=True,
        )
    if "ix_assignments_status" not in assignment_indexes:
        op.create_index("ix_assignments_status", "assignments", ["status"], if_not_exists=True)
    if "ix_assignments_due_date" not in assignment_indexes:
        op.create_index("ix_assignments_due_date", "assignments", ["due_date"], if_not_exists=True)
    if "ix_assignments_grading_type" not in assignment_indexes:
        op.create_index("ix_assignments_grading_type", "assignments", ["grading_type"], if_not_exists=True)
    if "ix_assignments_is_published" not in assignment_indexes:
        op.create_index("ix_assignments_is_published", "assignments", ["is_published"], if_not_exists=True)
    if "ix_assignments_course_id" not in assignment_indexes:
        op.create_index("ix_assignments_course_id", "assignments", ["course_id"], if_not_exists=True)
    if "ix_assignments_instructor_id" not in assignment_indexes:
        op.create_index("ix_assignments_instructor_id", "assignments", ["instructor_id"], if_not_exists=True)
    if "ix_assignments_created_at" not in assignment_indexes:
        op.create_index("ix_assignments_created_at", "assignments", ["created_at"], if_not_exists=True)

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "submissions" not in tables:
        op.create_table(
            "submissions",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("enrollment_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("assignment_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'submitted'")),
            sa.Column("grade", sa.Float(), nullable=True),
            sa.Column("max_grade", sa.Float(), nullable=True),
            sa.Column("feedback", sa.Text(), nullable=True),
            sa.Column("feedback_attachments", sa.JSON(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("file_urls", sa.JSON(), nullable=True),
            sa.Column("submission_type", sa.String(length=50), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("status IN ('submitted','graded','returned','revised')", name="ck_submissions_status"),
            sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("enrollment_id", "assignment_id", name="uq_submissions_enrollment_assignment"),
        )
        op.alter_column("submissions", "status", server_default=None)

    inspector = sa.inspect(bind)
    submission_indexes = {index["name"] for index in inspector.get_indexes("submissions")}
    if "ix_submissions_enrollment_status" not in submission_indexes:
        op.create_index("ix_submissions_enrollment_status", "submissions", ["enrollment_id", "status"], if_not_exists=True)
    if "ix_submissions_assignment_status" not in submission_indexes:
        op.create_index("ix_submissions_assignment_status", "submissions", ["assignment_id", "status"], if_not_exists=True)
    if "ix_submissions_enrollment_submitted_at" not in submission_indexes:
        op.create_index(
            "ix_submissions_enrollment_submitted_at",
            "submissions",
            ["enrollment_id", "submitted_at"],
            if_not_exists=True,
        )
    if "ix_submissions_status" not in submission_indexes:
        op.create_index("ix_submissions_status", "submissions", ["status"], if_not_exists=True)
    if "ix_submissions_submission_type" not in submission_indexes:
        op.create_index("ix_submissions_submission_type", "submissions", ["submission_type"], if_not_exists=True)
    if "ix_submissions_enrollment_id" not in submission_indexes:
        op.create_index("ix_submissions_enrollment_id", "submissions", ["enrollment_id"], if_not_exists=True)
    if "ix_submissions_assignment_id" not in submission_indexes:
        op.create_index("ix_submissions_assignment_id", "submissions", ["assignment_id"], if_not_exists=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "submissions" in tables:
        op.drop_index("ix_submissions_assignment_id", table_name="submissions", if_exists=True)
        op.drop_index("ix_submissions_enrollment_id", table_name="submissions", if_exists=True)
        op.drop_index("ix_submissions_submission_type", table_name="submissions", if_exists=True)
        op.drop_index("ix_submissions_status", table_name="submissions", if_exists=True)
        op.drop_index("ix_submissions_enrollment_submitted_at", table_name="submissions", if_exists=True)
        op.drop_index("ix_submissions_assignment_status", table_name="submissions", if_exists=True)
        op.drop_index("ix_submissions_enrollment_status", table_name="submissions", if_exists=True)
        op.drop_table("submissions")

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "assignments" in tables:
        op.drop_index("ix_assignments_created_at", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_instructor_id", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_course_id", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_is_published", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_grading_type", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_due_date", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_status", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_is_published_created_at", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_instructor_created_at", table_name="assignments", if_exists=True)
        op.drop_index("ix_assignments_course_created_at", table_name="assignments", if_exists=True)
        op.drop_table("assignments")
