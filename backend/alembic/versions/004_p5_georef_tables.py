"""add p5 georeferencing and spatial validation tables

Revision ID: 004_p5_georef_tables
Revises: 003_p3_perception_tables
Create Date: 2026-11-08 00:00:00.000000

"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Float,
    String,
    Text,
    JSON,
    Boolean,
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

revision = "004_p5_georef_tables"
down_revision = "003_p3_perception_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # GeorefProcessingRun
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "georef_processing_runs",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("mission_id", String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        Column("perception_run_id", String(36), ForeignKey("perception_runs.id", ondelete="SET NULL"), nullable=True),
        Column("tracking_run_id", String(36), ForeignKey("tracking_runs.id", ondelete="SET NULL"), nullable=True),
        Column("reconstruction_id", String(36), ForeignKey("reconstructions.id", ondelete="SET NULL"), nullable=True),
        Column("status", String(32), nullable=False),
        Column("started_at", DateTime, nullable=True),
        Column("completed_at", DateTime, nullable=True),
        Column("cancelled_at", DateTime, nullable=True),
        Column("error_message", Text, nullable=True),
        Column("config_json", JSON, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
    )
    op.create_index("ix_georef_processing_runs_mission_id", "georef_processing_runs", ["mission_id"])
    op.create_index("ix_georef_processing_runs_status", "georef_processing_runs", ["status"])

    # ------------------------------------------------------------------
    # CoordinateTransformation
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "coordinate_transformations",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("georef_processing_run_id", String(36), ForeignKey("georef_processing_runs.id", ondelete="CASCADE"), nullable=False, index=True),
        Column("source_crs", String(64), nullable=False),
        Column("target_crs", String(64), nullable=False),
        Column("source_coordinate_frame", String(64), nullable=True),
        Column("target_coordinate_frame", String(64), nullable=True),
        Column("horizontal_datum", String(64), nullable=True),
        Column("vertical_datum", String(64), nullable=True),
        Column("translation_x", Float, nullable=True),
        Column("translation_y", Float, nullable=True),
        Column("translation_z", Float, nullable=True),
        Column("scale_factor", Float, nullable=True),
        Column("rotation_matrix_json", Text, nullable=True),
        Column("transformation_method", String(128), nullable=True),
        Column("scale_method", String(128), nullable=True),
        Column("residuals_json", JSON, nullable=True),
        Column("uncertainty_json", JSON, nullable=True),
        Column("status", String(32), nullable=False),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_coordinate_transformations_georef_run_id", "coordinate_transformations", ["georef_processing_run_id"])

    # ------------------------------------------------------------------
    # SpatialValidationMetric
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "spatial_validation_metrics",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("georef_processing_run_id", String(36), ForeignKey("georef_processing_runs.id", ondelete="CASCADE"), nullable=False, index=True),
        Column("metric_name", String(64), nullable=False),
        Column("value", Float, nullable=True),
        Column("count", Integer, nullable=True),
        Column("reference_source", Text, nullable=True),
        Column("units", String(64), nullable=True),
        Column("checkpoint_ids_json", JSON, nullable=True),
        Column("method", String(128), nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_spatial_validation_metrics_georef_run_id", "spatial_validation_metrics", ["georef_processing_run_id"])

    # ------------------------------------------------------------------
    # GeorefArtifact
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "georef_artifacts",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("georef_processing_run_id", String(36), ForeignKey("georef_processing_runs.id", ondelete="CASCADE"), nullable=False, index=True),
        Column("artifact_type", String(64), nullable=False),
        Column("storage_path", String(512), nullable=False),
        Column("relative_path", String(512), nullable=True),
        Column("file_size_bytes", Integer, nullable=True),
        Column("checksum_sha256", String(64), nullable=True),
        Column("mime_type", String(100), nullable=True),
        Column("description", Text, nullable=True),
        Column("source_artifact_ids_json", JSON, nullable=True),
        Column("version", String(64), nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_georef_artifacts_georef_run_id", "georef_artifacts", ["georef_processing_run_id"])
    op.create_index("ix_georef_artifacts_artifact_type", "georef_artifacts", ["artifact_type"])


def downgrade() -> None:
    op.drop_index("ix_georef_artifacts_artifact_type", table_name="georef_artifacts")
    op.drop_index("ix_georef_artifacts_georef_run_id", table_name="georef_artifacts")
    op.drop_table("georef_artifacts")

    op.drop_index("ix_spatial_validation_metrics_georef_run_id", table_name="spatial_validation_metrics")
    op.drop_table("spatial_validation_metrics")


    op.drop_index("ix_coordinate_transformations_georef_run_id", table_name="coordinate_transformations")
    op.drop_table("coordinate_transformations")


    op.drop_index("ix_georef_processing_runs_status", table_name="georef_processing_runs")
    op.drop_index("ix_georef_processing_runs_mission_id", table_name="georef_processing_runs")
    op.drop_table("georef_processing_runs")
