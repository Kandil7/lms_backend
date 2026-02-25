"""Add missing course/lesson columns for schema compatibility.

Revision ID: 0013_add_missing_course_lesson_columns
Revises: 0012_add_admins_table
Create Date: 2026-02-25 16:40:00.000000
"""

from __future__ import annotations

from collections.abc import Iterable

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "0013_add_missing_course_lesson_columns"
down_revision = "0012_add_admins_table"
branch_labels = None
depends_on = None


def _existing_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {col["name"] for col in inspector.get_columns(table_name)}


def _existing_indexes(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _add_columns_if_missing(table_name: str, columns: Iterable[sa.Column]) -> None:
    existing = _existing_columns(table_name)
    for column in columns:
        if column.name not in existing:
            op.add_column(table_name, column)


def upgrade() -> None:
    if _table_exists("courses"):
        _add_columns_if_missing(
            "courses",
            (
                sa.Column("price", sa.Numeric(10, 2), nullable=True),
                sa.Column("currency", sa.String(length=3), nullable=True),
                sa.Column("is_free", sa.Boolean(), nullable=True),
                sa.Column("long_description", sa.Text(), nullable=True),
                sa.Column("preview_video_url", sa.String(length=500), nullable=True),
                sa.Column("requirements", sa.JSON(), nullable=True),
                sa.Column("learning_objectives", sa.JSON(), nullable=True),
                sa.Column("total_reviews", sa.Integer(), nullable=True),
                sa.Column("total_quizzes", sa.Integer(), nullable=True),
                sa.Column("enrollment_count", sa.Integer(), nullable=True),
                sa.Column("average_rating", sa.Float(), nullable=True),
                sa.Column("status", sa.String(length=20), nullable=True),
            ),
        )

    if _table_exists("lessons"):
        existing_columns = _existing_columns("lessons")
        if "is_published" not in existing_columns:
            op.add_column(
                "lessons",
                sa.Column(
                    "is_published",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                ),
            )
            op.alter_column("lessons", "is_published", server_default=None)

        existing_indexes = _existing_indexes("lessons")
        if "ix_lessons_is_published" not in existing_indexes:
            op.create_index("ix_lessons_is_published", "lessons", ["is_published"])
        if "ix_lessons_course_published" not in existing_indexes:
            op.create_index(
                "ix_lessons_course_published",
                "lessons",
                ["course_id", "is_published"],
            )


def downgrade() -> None:
    if _table_exists("lessons"):
        existing_indexes = _existing_indexes("lessons")
        if "ix_lessons_course_published" in existing_indexes:
            op.drop_index("ix_lessons_course_published", table_name="lessons")
        if "ix_lessons_is_published" in existing_indexes:
            op.drop_index("ix_lessons_is_published", table_name="lessons")

        existing_columns = _existing_columns("lessons")
        if "is_published" in existing_columns:
            op.drop_column("lessons", "is_published")

    if _table_exists("courses"):
        existing_columns = _existing_columns("courses")
        for column_name in (
            "status",
            "average_rating",
            "enrollment_count",
            "total_quizzes",
            "total_reviews",
            "learning_objectives",
            "requirements",
            "preview_video_url",
            "long_description",
            "is_free",
            "currency",
            "price",
        ):
            if column_name in existing_columns:
                op.drop_column("courses", column_name)
