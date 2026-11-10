"""Baseline schema for tables that predate the mission data spine.

Revision 001 builds the mission/video tables but assumes the core platform
tables (users, projects, images, jobs, inference results, ...) already exist,
because older installations created them with ``Base.metadata.create_all``.
That made ``alembic upgrade head`` fail on a genuinely empty database.

This baseline revision materialises the core tables from the SQLAlchemy model
metadata so the migration chain is self-contained. It is a migration-time
operation only; the application no longer relies on ``create_all`` for schema
provisioning.

Revision ID: 000_base_schema
Revises: None
"""
from __future__ import annotations

from typing import Union

from alembic import op

import backend.app.models  # noqa: F401  (registers every model table)
from backend.app.core.database import Base

revision: str = "000_base_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, list[str], None] = None
depends_on: Union[str, list[str], None] = None


# Core platform tables that existed before the mission data spine (revision 001).
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
        Base.metadata.tables[name].create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(CORE_TABLES):
        Base.metadata.tables[name].drop(bind, checkfirst=True)
