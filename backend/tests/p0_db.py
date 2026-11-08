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

    # Reset the import-time schema catalog so each temporary database is built
    # from a clean BoundMetaData, avoiding the platform's schema collision.
    Base.metadata.clear()

    # Import the exact models the P0 tests and the mission pipeline use. Keep this
    # list in sync with the tests that touch these tables.
    from backend.app.models.user import User  # noqa: F401
    from backend.app.models.project import Project  # noqa: F401
    from backend.app.models.job import Job  # noqa: F401
    from backend.app.models.image import Image  # noqa: F401
    from backend.app.models.artifact import Artifact  # noqa: F401
    from backend.app.models.reconstruction import Reconstruction, Reconstruction3D  # noqa: F401
    from backend.app.models.job_log import JobLog  # noqa: F401
    from backend.app.models.refresh_token import RefreshToken  # noqa: F401
    from backend.app.models.mission import Mission  # noqa: F401
    from backend.app.models.video import Video  # noqa: F401
    from backend.app.models.flight_metadata import FlightMetadata  # noqa: F401
    from backend.app.models.frame import Frame  # noqa: F401
    from backend.app.models.camera_pose import CameraPose  # noqa: F401
    from backend.app.models.georef_solution import GeorefSolution  # noqa: F401
    from backend.app.models.validation_report import ValidationReport  # noqa: F401
    from backend.app.models.ai_model_version import AIModelVersion  # noqa: F401

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
