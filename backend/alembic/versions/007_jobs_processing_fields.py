"""add job ownership and processing-run linkage

The P2 video-processing orchestration stores the initiating user on the job
(``owner_id``) and tags each run with ``processing_run_id`` so frames, reports
and retries can be scoped to a single run. These columns were present in the
service code and API schemas but missing from both the ORM model and the
database schema.

Revision ID: 007_jobs_processing_fields
Revises: 006_p5_georef_control_points
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_jobs_processing_fields"
down_revision: Union[str, None] = "006_p5_georef_control_points"
branch_labels: Union[str, list[str], None] = None
depends_on: Union[str, list[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    columns = {c["name"] for c in insp.get_columns("jobs")}
    indexes = {i["name"] for i in insp.get_indexes("jobs")}

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        if "owner_id" not in columns:
            batch_op.add_column(sa.Column("owner_id", sa.String(length=36), nullable=True))
        if "processing_run_id" not in columns:
            batch_op.add_column(sa.Column("processing_run_id", sa.String(length=64), nullable=True))

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        if "ix_jobs_owner_id" not in indexes:
            batch_op.create_index("ix_jobs_owner_id", ["owner_id"])
        if "ix_jobs_processing_run_id" not in indexes:
            batch_op.create_index("ix_jobs_processing_run_id", ["processing_run_id"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    columns = {c["name"] for c in insp.get_columns("jobs")}
    indexes = {i["name"] for i in insp.get_indexes("jobs")}

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        if "ix_jobs_processing_run_id" in indexes:
            batch_op.drop_index("ix_jobs_processing_run_id")
        if "ix_jobs_owner_id" in indexes:
            batch_op.drop_index("ix_jobs_owner_id")
        if "processing_run_id" in columns:
            batch_op.drop_column("processing_run_id")
        if "owner_id" in columns:
            batch_op.drop_column("owner_id")
