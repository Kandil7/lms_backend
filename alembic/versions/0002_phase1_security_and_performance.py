"""phase 1 security and performance indexes

Revision ID: 0002_phase1_security_and_performance
Revises: 0001_initial_schema
Create Date: 2026-02-18
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_phase1_security_and_performance"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_users_created_at", "users", ["created_at"], if_not_exists=True)

    op.create_index("ix_courses_created_at", "courses", ["created_at"], if_not_exists=True)
    op.create_index("ix_courses_difficulty_level", "courses", ["difficulty_level"], if_not_exists=True)
    op.create_index(
        "ix_courses_is_published_created_at",
        "courses",
        ["is_published", "created_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_courses_instructor_created_at",
        "courses",
        ["instructor_id", "created_at"],
        if_not_exists=True,
    )

    op.create_index(
        "ix_enrollments_student_enrolled_at",
        "enrollments",
        ["student_id", "enrolled_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_enrollments_course_enrolled_at",
        "enrollments",
        ["course_id", "enrolled_at"],
        if_not_exists=True,
    )

    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"], if_not_exists=True)
    op.create_index("ix_refresh_tokens_revoked_at", "refresh_tokens", ["revoked_at"], if_not_exists=True)
    op.create_index(
        "ix_refresh_tokens_user_revoked",
        "refresh_tokens",
        ["user_id", "revoked_at"],
        if_not_exists=True,
    )

    op.create_index(
        "ix_uploaded_files_uploader_created_at",
        "uploaded_files",
        ["uploader_id", "created_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_uploaded_files_uploader_type_created_at",
        "uploaded_files",
        ["uploader_id", "file_type", "created_at"],
        if_not_exists=True,
    )

    op.create_index(
        "ix_certificates_student_revoked_issued_at",
        "certificates",
        ["student_id", "is_revoked", "issued_at"],
        if_not_exists=True,
    )

    op.create_index(
        "ix_lesson_progress_enrollment_status",
        "lesson_progress",
        ["enrollment_id", "status"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_lesson_progress_enrollment_completed_at",
        "lesson_progress",
        ["enrollment_id", "completed_at"],
        if_not_exists=True,
    )

    op.create_index("ix_quiz_attempts_submitted_at", "quiz_attempts", ["submitted_at"], if_not_exists=True)
    op.create_index(
        "ix_quiz_attempts_enrollment_status_submitted_at",
        "quiz_attempts",
        ["enrollment_id", "status", "submitted_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_quiz_attempts_enrollment_status_submitted_at", table_name="quiz_attempts", if_exists=True)
    op.drop_index("ix_quiz_attempts_submitted_at", table_name="quiz_attempts", if_exists=True)

    op.drop_index("ix_lesson_progress_enrollment_completed_at", table_name="lesson_progress", if_exists=True)
    op.drop_index("ix_lesson_progress_enrollment_status", table_name="lesson_progress", if_exists=True)

    op.drop_index("ix_certificates_student_revoked_issued_at", table_name="certificates", if_exists=True)

    op.drop_index("ix_uploaded_files_uploader_type_created_at", table_name="uploaded_files", if_exists=True)
    op.drop_index("ix_uploaded_files_uploader_created_at", table_name="uploaded_files", if_exists=True)

    op.drop_index("ix_refresh_tokens_user_revoked", table_name="refresh_tokens", if_exists=True)
    op.drop_index("ix_refresh_tokens_revoked_at", table_name="refresh_tokens", if_exists=True)
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens", if_exists=True)

    op.drop_index("ix_enrollments_course_enrolled_at", table_name="enrollments", if_exists=True)
    op.drop_index("ix_enrollments_student_enrolled_at", table_name="enrollments", if_exists=True)

    op.drop_index("ix_courses_instructor_created_at", table_name="courses", if_exists=True)
    op.drop_index("ix_courses_is_published_created_at", table_name="courses", if_exists=True)
    op.drop_index("ix_courses_difficulty_level", table_name="courses", if_exists=True)
    op.drop_index("ix_courses_created_at", table_name="courses", if_exists=True)

    op.drop_index("ix_users_created_at", table_name="users", if_exists=True)
