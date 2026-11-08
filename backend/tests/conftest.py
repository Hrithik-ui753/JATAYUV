from __future__ import annotations

import os
from typing import Generator, Optional

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import backend.app.core.database as db_mod
from backend.app.core.database import Base


@pytest.fixture
def isolation_db(tmp_path_factory: pytest.TempPathFactory) -> Generator[str, None, None]:
    """Create an isolated SQLite database file for a test module."""
    db_url = "sqlite:///" + str(tmp_path_factory.mktemp("db") / "jatayuv_test.db")
    yield db_url


@pytest.fixture
def db_session(isolation_db: str) -> Generator[Session, None, None]:
    """Yield a sqlalchemy Session connected to a test DB, with Base metadata created."""
    engine = create_engine(
        isolation_db,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def fresh_db_url(isolation_db: str) -> str:
    return isolation_db
