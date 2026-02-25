"""Add admins table

Revision ID: 0012_add_admins_table
Revises: 0011_add_instructors_table
Create Date: 2026-02-23 20:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0012_add_admins_table'
down_revision = '0011_add_instructors_table'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "admins" in inspector.get_table_names():
        return

    # Create admins table
    op.create_table(
        'admins',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('security_level', sa.String(20), nullable=False),
        sa.Column('mfa_required', sa.Boolean(), nullable=False),
        sa.Column('ip_whitelist', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('time_restrictions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('emergency_contacts', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_setup_complete', sa.Boolean(), nullable=False),
        sa.Column('setup_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('security_policy_accepted', sa.Boolean(), nullable=False),
        sa.Column('security_policy_version', sa.String(20), nullable=False),
        sa.Column('last_security_review', sa.DateTime(timezone=True), nullable=True),
        sa.Column('security_health_score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "admins" in inspector.get_table_names():
        op.drop_table('admins')
