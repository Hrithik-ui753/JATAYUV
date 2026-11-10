from typing import Dict, List

from sqlalchemy import create_engine, inspect, text
<<<<<<< HEAD
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
=======
from sqlalchemy.orm import declarative_base, sessionmaker
>>>>>>> origin/main
from backend.app.core.config import settings

# SQLite connection args for multithreaded fast access
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = scoped_session(SessionLocal)

Base = declarative_base()
Base.query = db.query_property()



def ensure_sqlite_columns(table: str, columns: Dict[str, str]) -> List[str]:
    """Idempotently add missing columns to an existing SQLite table.

    SQLite cannot alter constraints, but ``ADD COLUMN`` is supported and safe. This keeps
    databases created before the depth-provenance columns were introduced working
    without a destructive migration or a manual Alembic run.
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        return []
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return []
    existing = {column["name"] for column in inspector.get_columns(table)}
    added: List[str] = []
    with engine.begin() as connection:
        for name, ddl in columns.items():
            if name in existing:
                continue
            connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {ddl}'))
            added.append(name)
    return added


def ensure_depth_result_schema() -> List[str]:
    """Add the depth provenance columns to legacy ``depth_results`` tables."""
    return ensure_sqlite_columns(
        "depth_results",
        {
            "depth_type": "VARCHAR(32)",
            "depth_unit": "VARCHAR(64)",
            "model_id": "VARCHAR(100)",
            "model_label": "VARCHAR(200)",
            "model_version": "VARCHAR(100)",
            "checkpoint_path": "VARCHAR(512)",
            "checkpoint_sha256": "VARCHAR(64)",
            "input_size": "INTEGER",
            "inference_ms": "FLOAT",
            "relative_min": "FLOAT",
            "relative_max": "FLOAT",
            "relative_mean": "FLOAT",
            "raw_depth_path": "VARCHAR(512)",
        },
    )



def ensure_sqlite_columns(table: str, columns: Dict[str, str]) -> List[str]:
    """Idempotently add missing columns to an existing SQLite table.

    SQLite cannot alter constraints, but ``ADD COLUMN`` is supported and safe. This keeps
    databases created before the depth-provenance columns were introduced working
    without a destructive migration or a manual Alembic run.
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        return []
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return []
    existing = {column["name"] for column in inspector.get_columns(table)}
    added: List[str] = []
    with engine.begin() as connection:
        for name, ddl in columns.items():
            if name in existing:
                continue
            connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {ddl}'))
            added.append(name)
    return added


def ensure_depth_result_schema() -> List[str]:
    """Add the depth provenance columns to legacy ``depth_results`` tables."""
    return ensure_sqlite_columns(
        "depth_results",
        {
            "depth_type": "VARCHAR(32)",
            "depth_unit": "VARCHAR(64)",
            "model_id": "VARCHAR(100)",
            "model_label": "VARCHAR(200)",
            "model_version": "VARCHAR(100)",
            "checkpoint_path": "VARCHAR(512)",
            "checkpoint_sha256": "VARCHAR(64)",
            "input_size": "INTEGER",
            "inference_ms": "FLOAT",
            "relative_min": "FLOAT",
            "relative_max": "FLOAT",
            "relative_mean": "FLOAT",
            "raw_depth_path": "VARCHAR(512)",
        },
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

