"""Add course enhancement fields for frontend compatibility

Revision ID: 0009_add_course_enhancement_fields
Revises: 0008_add_assignments_submissions
Create Date: 2026-02-23 14:30:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0009_add_course_enhancement_fields'
down_revision = '0008_add_assignments_submissions'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("courses")}

    columns_to_add: list[sa.Column] = [
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("is_free", sa.Boolean(), nullable=True),
        sa.Column("long_description", sa.Text(), nullable=True),
        sa.Column("preview_video_url", sa.String(length=500), nullable=True),
        sa.Column("requirements", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("learning_objectives", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("total_reviews", sa.Integer(), nullable=True),
        sa.Column("total_quizzes", sa.Integer(), nullable=True),
        sa.Column("enrollment_count", sa.Integer(), nullable=True),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
    ]

    for column in columns_to_add:
        if column.name not in existing:
            op.add_column("courses", column)


def downgrade():
    # Remove new columns from courses table
    op.drop_column('courses', 'status')
    op.drop_column('courses', 'average_rating')
    op.drop_column('courses', 'enrollment_count')
    op.drop_column('courses', 'total_quizzes')
    op.drop_column('courses', 'total_reviews')
    op.drop_column('courses', 'learning_objectives')
    op.drop_column('courses', 'requirements')
    op.drop_column('courses', 'preview_video_url')
    op.drop_column('courses', 'long_description')
    op.drop_column('courses', 'is_free')
    op.drop_column('courses', 'currency')
    op.drop_column('courses', 'price')
