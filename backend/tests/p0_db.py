"""Shared helper for P0 integrity tests that need an isolated SQLite database.

The P0 tests create many temporary databases during a run. On this platform a
`metadata.create_all(bind=engine)` can raise `index ... already exists` when the
BoundMetaData is shared across imports. This helper isolates the fixture database
to the import that creates it by importing only the truly required models right
before building the schema.
"""
from __future__ import annotations

import pathlib
from tempfile import mkdtemp
from typing import Callable

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base


def make_isolated_db(db_path: pathlib.Path | str) -> tuple[create_engine, sessionmaker]:
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    # Ensure every model is registered on the shared metadata before create_all.
    # Do NOT call Base.metadata.clear(): modules are already imported by the app,
    # so clearing the registry detaches their tables and create_all then builds
    # an empty schema ("no such table: users").
    import backend.app.models  # noqa: F401

    create_all_result = Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, TestingSession


def list_indexes(db_path: pathlib.Path | str) -> dict[str, list[dict]]:
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as conn:
        insp = inspect(conn)
        return {t: insp.get_indexes(t) for t in sorted(insp.get_table_names())}
