#!/usr/bin/env python3
"""
Migration generation utility for modular LMS backend.

This script generates module-specific migrations with proper dependency management.
It supports:
- Granular module migrations (users, auth, courses, etc.)
- Automatic dependency resolution
- Enhanced migration metadata
- Backward compatibility checks

Usage:
  python scripts/generate_module_migration.py --module users --message "Add user preferences"
  python scripts/generate_module_migration.py --module courses --message "Add course categories" --dependencies users
"""

import argparse
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_module_dependencies():
    """Define module dependencies for migration ordering."""
    return {
        "users": [],
        "auth": ["users"],
        "courses": ["users"],
        "enrollments": ["users", "courses"],
        "quizzes": ["users", "courses"],
        "files": ["users"],
        "certificates": ["users", "courses"],
        "assignments": ["users", "courses"],
        "payments": ["users", "courses", "enrollments"],
        "instructors": ["users"],
        "admin": ["users"],
        "analytics": ["users", "courses", "enrollments"],
        "websocket": ["users"],
    }

def generate_migration_filename(module_name: str, message: str) -> str:
    """Generate filename for migration based on module and message."""
    # Clean message for filename
    clean_message = message.lower().replace(' ', '_').replace('-', '_').replace('.', '')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{module_name}_{clean_message}.py"

def create_module_migration(module_name: str, message: str, dependencies: list = None):
    """Create a new module-specific migration file."""
    if not dependencies:
        dependencies = get_module_dependencies().get(module_name, [])
    
    # Create directory if it doesn't exist
    versions_dir = Path("alembic/versions") / module_name
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = generate_migration_filename(module_name, message)
    filepath = versions_dir / filename
    
    # Get current latest revision in this module
    latest_revision = None
    if versions_dir.exists():
        migration_files = sorted(versions_dir.glob("*.py"))
        if migration_files:
            # Get the most recent migration
            latest_file = migration_files[-1]
            latest_revision = latest_file.stem.split('_')[1] if '_' in latest_file.stem else None
    
    # Create migration content
    content = f'''"""{message}

Revision ID: {uuid.uuid4().hex[:8]}_{module_name}
Revises: {latest_revision if latest_revision else 'None'}
Create Date: {datetime.now().isoformat()}
Module: {module_name}
Dependencies: {dependencies}
Migration Type: standard
"""

from collections.abc import Sequence
from typing import List, Optional

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "{uuid.uuid4().hex[:8]}_{module_name}"
down_revision: str | None = {repr(latest_revision)}
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = {repr(dependencies)}

# Migration metadata
module_name: str = "{module_name}"
dependencies: List[str] = {repr(dependencies)}
migration_type: str = "standard"
description: str = "{message}"


def upgrade() -> None:
    """Apply the migration upgrades with enhanced safety checks."""
    # Safety check: verify current database state before applying changes
    _pre_upgrade_validation()
    
    # TODO: Implement your upgrade operations here
    # Example:
    # op.add_column('users', sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    # op.create_index('ix_users_preferences', 'users', ['preferences'])
    
    # Post-upgrade validation
    _post_upgrade_validation()


def downgrade() -> None:
    """Apply the migration downgrades with enhanced safety and data preservation."""
    # Safety check: verify current database state before rolling back
    _pre_downgrade_validation()
    
    # TODO: Implement your downgrade operations here
    # Example:
    # op.drop_index('ix_users_preferences', table_name='users')
    # op.drop_column('users', 'preferences')
    
    # Post-downgrade validation
    _post_downgrade_validation()


def _pre_upgrade_validation() -> None:
    """Validate preconditions before upgrading."""
    connection = op.get_bind()
    # Check if table exists
    result = connection.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
    )
    if not result.scalar():
        raise RuntimeError(f"Required table 'users' does not exist for {module_name} migration")


def _post_upgrade_validation() -> None:
    """Validate postconditions after upgrading."""
    connection = op.get_bind()
    # Verify column was added
    result = connection.execute(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'preferences'"
    )
    if result.scalar() == 0:
        raise RuntimeError(f"Column 'preferences' was not created in 'users' table")


def _pre_downgrade_validation() -> None:
    """Validate preconditions before downgrading."""
    connection = op.get_bind()
    # Check if column exists before removing
    result = connection.execute(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'preferences'"
    )
    if result.scalar() == 0:
        raise RuntimeError(f"Column 'preferences' does not exist for downgrade in {module_name} migration")


def _post_downgrade_validation() -> None:
    """Validate postconditions after downgrading."""
    connection = op.get_bind()
    # Verify column was removed
    result = connection.execute(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'preferences'"
    )
    if result.scalar() > 0:
        raise RuntimeError(f"Column 'preferences' still exists after downgrade in {module_name} migration")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate module-specific migrations")
    parser.add_argument("--module", required=True, help="Module name (e.g., users, courses)")
    parser.add_argument("--message", required=True, help="Migration description")
    parser.add_argument("--dependencies", nargs="*", help="List of dependent modules")
    
    args = parser.parse_args()
    
    try:
        create_module_migration(args.module, args.message, args.dependencies)
        print(f"✓ Migration created: {filepath}")
        print(f"  Module: {args.module}")
        print(f"  Message: {args.message}")
        print(f"  Dependencies: {args.dependencies or []}")
    except Exception as e:
        print(f"✗ Error creating migration: {e}")
        sys.exit(1)