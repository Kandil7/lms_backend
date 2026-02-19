from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def import_models() -> None:
    # Import module model packages so metadata is populated.
    modules = [
        "app.modules.users.models",
        "app.modules.auth.models",
        "app.modules.courses.models",
        "app.modules.enrollments.models",
        "app.modules.quizzes.models",
        "app.modules.files.models",
        "app.modules.certificates.models",
    ]

    for module in modules:
        try:
            __import__(module)
        except Exception:
            continue


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
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

        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


def _ensure_version_table_capacity(connection) -> None:
    # Alembic defaults to VARCHAR(32) for alembic_version.version_num, while this
    # project uses descriptive revision ids longer than 32 chars.
    connection.exec_driver_sql(
        "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(255) NOT NULL PRIMARY KEY)"
    )
    if connection.dialect.name == "postgresql":
        connection.exec_driver_sql(
            "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)"
        )


import_models()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
