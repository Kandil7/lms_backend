"""Add instructors table

Revision ID: 0011_add_instructors_table
Revises: 0010_add_payment_tables
Create Date: 2026-02-23 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0011_add_instructors_table'
down_revision = '0010_add_payment_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create instructors table
    op.create_table(
        'instructors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bio', sa.Text(), nullable=False),
        sa.Column('expertise', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('teaching_experience_years', sa.Integer(), nullable=False),
        sa.Column('education_level', sa.String(100), nullable=False),
        sa.Column('institution', sa.String(255), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('verification_status', sa.String(50), nullable=False),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('verification_document_url', sa.String(1000), nullable=True),
        sa.Column('verification_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    # Drop instructors table
    op.drop_table('instructors')