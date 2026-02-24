from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _get_engine_kwargs() -> dict:
    kwargs: dict = {
        "echo": settings.SQLALCHEMY_ECHO,
        "pool_pre_ping": True,
    }

    if settings.DATABASE_URL.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT  # Connection pool timeout
        kwargs["pool_recycle"] = settings.DB_POOL_RECYCLE  # Recycle connections

    return kwargs


engine = create_engine(settings.DATABASE_URL, **_get_engine_kwargs())
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, class_=Session
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_health() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
