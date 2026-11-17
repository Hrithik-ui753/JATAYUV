"""add p5 ground control points and checkpoint observations

Revision ID: 006_p5_georef_control_points
Revises: 005_p6_reconstruction_tables
Create Date: 2026-11-08 00:00:00.000000

"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Float,
    Index,
    String,
    Text,
    JSON,
)
import sqlalchemy as sa
from alembic import op



def _create_table_if_missing(name, *args, **kwargs):
    """Create a table only when it does not already exist.

    Existing installations may have been provisioned by an older release (or by
    ``create_all``) before Alembic was introduced. Re-running the chain must not
    fail on those databases.
    """
    if name in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(name, *args, **kwargs)

revision = "006_p5_georef_control_points"
down_revision = "005_p6_reconstruction_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _create_table_if_missing(
        "ground_control_points",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("mission_id", String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        Column("georef_processing_run_id", String(36), ForeignKey("georef_processing_runs.id", ondelete="SET NULL"), nullable=True),
        Column("label", String(128), nullable=True),
        Column("category", String(64), nullable=True),
        Column("role", String(32), nullable=False),
        Column("local_x", Float, nullable=True),
        Column("local_y", Float, nullable=True),
        Column("local_z", Float, nullable=True),
        Column("lat", Float, nullable=True),
        Column("lon", Float, nullable=True),
        Column("elevation", Float, nullable=True),
        Column("target_x", Float, nullable=True),
        Column("target_y", Float, nullable=True),
        Column("target_z", Float, nullable=True),
        Column("horizontal_accuracy", Float, nullable=True),
        Column("vertical_accuracy", Float, nullable=True),
        Column("measurement_source", Text, nullable=True),
        Column("measurement_method", Text, nullable=True),
        Column("observed_at", DateTime, nullable=True),
        Column("provenance_json", JSON, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
    )
    op.create_index("ix_ground_control_points_mission_id", "ground_control_points", ["mission_id"])
    op.create_index("ix_ground_control_points_role", "ground_control_points", ["role"])

    _create_table_if_missing(
        "checkpoint_observations",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("mission_id", String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        Column("georef_processing_run_id", String(36), ForeignKey("georef_processing_runs.id", ondelete="CASCADE"), nullable=False),
        Column("gcp_id", String(36), ForeignKey("ground_control_points.id", ondelete="SET NULL"), nullable=True),
        Column("observed_x", Float, nullable=True),
        Column("observed_y", Float, nullable=True),
        Column("observed_z", Float, nullable=True),
        Column("observed_lat", Float, nullable=True),
        Column("observed_lon", Float, nullable=True),
        Column("observed_elevation", Float, nullable=True),
        Column("reference_x", Float, nullable=True),
        Column("reference_y", Float, nullable=True),
        Column("reference_z", Float, nullable=True),
        Column("horizontal_error", Float, nullable=True),
        Column("vertical_error", Float, nullable=True),
        Column("horizontal_distance_error", Float, nullable=True),
        Column("three_d_error", Float, nullable=True),
        Column("easting_error", Float, nullable=True),
        Column("northing_error", Float, nullable=True),
        Column("elevation_difference", Float, nullable=True),
        Column("status", String(32), nullable=False),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_checkpoint_observations_mission_id", "checkpoint_observations", ["mission_id"])
    op.create_index("ix_checkpoint_observations_georef_processing_run_id", "checkpoint_observations", ["georef_processing_run_id"])
    op.create_index("ix_checkpoint_observations_gcp_id", "checkpoint_observations", ["gcp_id"])


def downgrade() -> None:
    op.drop_index("ix_checkpoint_observations_gcp_id", table_name="checkpoint_observations")
    op.drop_index("ix_checkpoint_observations_georef_processing_run_id", table_name="checkpoint_observations")
    op.drop_index("ix_checkpoint_observations_mission_id", table_name="checkpoint_observations")
    op.drop_table("checkpoint_observations")

    op.drop_index("ix_ground_control_points_role", table_name="ground_control_points")
    op.drop_index("ix_ground_control_points_mission_id", table_name="ground_control_points")
    op.drop_table("ground_control_points")
