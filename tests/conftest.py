import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("ALLOW_PUBLIC_ROLE_REGISTRATION", "true")

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def engine(tmp_path_factory) -> Generator[Engine, None, None]:
    test_database_url = os.getenv("TEST_DATABASE_URL", "").strip()
    if test_database_url:
        engine = create_engine(test_database_url, pool_pre_ping=True)
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        yield engine
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        return

    db_dir = tmp_path_factory.mktemp("db")
    db_path = db_dir / "test.sqlite"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
