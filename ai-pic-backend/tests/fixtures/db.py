from pathlib import Path

import pytest
from app.core.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def test_db():
    """SQLite file database for tests (isolated per test)."""
    db_path = Path("test.db")
    if db_path.exists():
        db_path.unlink()

    engine = create_engine(
        "sqlite:///./test.db", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from app import models  # noqa: F401  # ensure models are registered

    Base.metadata.create_all(bind=engine)

    try:
        yield TestingSessionLocal
    finally:
        engine.dispose()
        if db_path.exists():
            db_path.unlink()


@pytest.fixture
def db_session(test_db):
    """Database session fixture."""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db(db_session):
    """Compatibility alias for old tests."""
    yield db_session


@pytest.fixture
def test_db_session(db_session):
    """Compatibility fixture for old tests."""
    yield db_session
