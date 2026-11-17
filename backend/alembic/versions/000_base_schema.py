
"""Baseline schema for core platform tables.

Creates the core SQLAlchemy tables before mission-related migrations.
Existing tables are preserved.
"""

from __future__ import annotations

from typing import Union

from alembic import op

import backend.app.models  # noqa: F401 - register model metadata
from backend.app.core.database import Base


revision: str = "000_base_schema"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


CORE_TABLES = (
    "users",
    "projects",
    "images",
    "jobs",
    "depth_results",
    "segmentation_results",
    "damage_assessment_results",
    "change_detection_results",
    "reconstructions_3d",
    "ai_model_versions",
    "artifacts",
    "job_logs",
    "refresh_tokens",
)


def upgrade() -> None:
    bind = op.get_bind()

    for name in CORE_TABLES:
        table = Base.metadata.tables.get(name)

        if table is None:
            raise RuntimeError(
                f"Required SQLAlchemy model table '{name}' "
                "was not registered in Base.metadata."
            )

        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()

    for name in reversed(CORE_TABLES):
        table = Base.metadata.tables.get(name)

        if table is not None:
            table.drop(bind=bind, checkfirst=True)
