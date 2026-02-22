"""add users.email_verified_at column

Revision ID: 0006_add_users_email_verified_at
Revises: 0005_phase1_remaining_indexes
Create Date: 2026-02-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_add_users_email_verified_at"
down_revision: str | None = "0005_phase1_remaining_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}

    if "email_verified_at" not in columns:
        op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))

    indexes = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_email_verified_at" not in indexes:
        op.create_index("ix_users_email_verified_at", "users", ["email_verified_at"], if_not_exists=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("users")}
    columns = {column["name"] for column in inspector.get_columns("users")}

    if "ix_users_email_verified_at" in indexes:
        op.drop_index("ix_users_email_verified_at", table_name="users", if_exists=True)

    if "email_verified_at" in columns:
        op.drop_column("users", "email_verified_at")
