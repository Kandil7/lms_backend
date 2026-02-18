"""add users.mfa_enabled column

Revision ID: 0007_add_users_mfa_enabled
Revises: 0006_add_users_email_verified_at
Create Date: 2026-02-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_add_users_mfa_enabled"
down_revision: str | None = "0006_add_users_email_verified_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.alter_column("users", "mfa_enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "mfa_enabled")
