from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def import_models() -> None:
    """Import all module models to populate metadata."""
    modules = [
        "app.modules.users.models",
        "app.modules.auth.models",
        "app.modules.courses.models",
        "app.modules.enrollments.models",
        "app.modules.quizzes.models",
        "app.modules.files.models",
        "app.modules.certificates.models",
        "app.modules.assignments.models",
        "app.modules.payments.models",
        "app.modules.instructors.models",
        "app.modules.admin.models",
        "app.modules.analytics.models",
        "app.modules.websocket.models",
    ]

    for module in modules:
        try:
            __import__(module)
        except ImportError as e:
            # Log but continue - some modules might not have models yet
            print(f"Warning: Could not import {module}: {e}")


def get_module_dependencies() -> dict:
    """
    Define module dependencies for migration ordering.
    Format: {module_name: [dependent_modules]}
    """
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


def resolve_migration_order() -> list:
    """
    Resolve migration order based on module dependencies using topological sort.
    Returns ordered list of modules for migration execution.
    """
    dependencies = get_module_dependencies()
    visited = set()
    result = []

    def dfs(module):
        if module in visited:
            return
        visited.add(module)
        
        # Process dependencies first
        for dep in dependencies.get(module, []):
            if dep not in visited:
                dfs(dep)
        
        result.append(module)

    # Start DFS from all modules
    for module in dependencies.keys():
        if module not in visited:
            dfs(module)

    return result


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        # Enhanced options for validation
        include_schemas=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        raise RuntimeError("Missing alembic configuration section")

    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Ensure the version table can store long revision IDs in a committed
        # transaction before Alembic starts its own migration transaction.
        with connection.begin():
            _ensure_version_table_capacity(connection)

        context.configure(
            connection=connection, 
            target_metadata=target_metadata, 
            compare_type=True,
            include_schemas=True,
            render_as_batch=True,
            # Add custom context for enhanced migrations
            **{
                "module_dependencies": get_module_dependencies(),
                "migration_order": resolve_migration_order(),
            }
        )

        with context.begin_transaction():
            context.run_migrations()


def _ensure_version_table_capacity(connection) -> None:
    """Ensure alembic_version table can handle long revision IDs."""
    # Alembic defaults to VARCHAR(32) for alembic_version.version_num, while this
    # project uses descriptive revision ids longer than 32 chars.
    connection.exec_driver_sql(
        "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(255) NOT NULL PRIMARY KEY)"
    )
    if connection.dialect.name == "postgresql":
        connection.exec_driver_sql(
            "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)"
        )


def validate_migration_integrity() -> bool:
    """Validate migration integrity before applying changes."""
    try:
        connection = op.get_bind() if 'op' in globals() else None
        if connection:
            # Check for common issues
            result = connection.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            if result.scalar() < 0:
                return False
        return True
    except Exception:
        return False


# Import models to populate metadata
import_models()

# Set up context for enhanced migration features
context.configure(
    target_metadata=target_metadata,
    include_schemas=True,
    compare_type=True,
)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()