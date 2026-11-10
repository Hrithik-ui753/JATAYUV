"""add p6 reconstruction run and artifact tables

Revision ID: 005_p6_reconstruction_tables
Revises: 004_p5_georef_tables
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

revision = "005_p6_reconstruction_tables"
down_revision = "004_p5_georef_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # ReconstructionRun
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "reconstruction_runs",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("mission_id", String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        Column("georef_processing_run_id", String(36), ForeignKey("georef_processing_runs.id", ondelete="SET NULL"), nullable=True),
        Column("processing_run_id", String(36), ForeignKey("processing_runs.id", ondelete="SET NULL"), nullable=True),
        Column("reconstruction_version", String(64), nullable=False),
        Column("reconstruction_method", String(128), nullable=False),
        Column("status", String(50), nullable=False),
        Column("coordinate_reference_system", String(64), nullable=True),
        Column("coordinate_frame", String(64), nullable=True),
        Column("units", String(64), nullable=True),
        Column("point_cloud_path", String(512), nullable=True),
        Column("mesh_path", String(512), nullable=True),
        Column("texture_path", String(512), nullable=True),
        Column("mtl_path", String(512), nullable=True),
        Column("vertex_count", Integer, nullable=True),
        Column("face_count", Integer, nullable=True),
        Column("point_count", Integer, nullable=True),
        Column("source_frame_ids_json", JSON, nullable=True),
        Column("processing_duration_seconds", Integer, nullable=True),
        Column("error_message", Text, nullable=True),
        Column("started_at", DateTime, nullable=True),
        Column("completed_at", DateTime, nullable=True),
        Column("cancelled_at", DateTime, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
    )
    op.create_index("ix_reconstruction_runs_mission_id", "reconstruction_runs", ["mission_id"])
    op.create_index("ix_reconstruction_runs_status", "reconstruction_runs", ["status"])

    # ------------------------------------------------------------------
    # ReconstructionFrame
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "reconstruction_frames",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("reconstruction_run_id", String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False),
        Column("frame_id", String(36), ForeignKey("frames.id", ondelete="SET NULL"), nullable=False),
        Column("camera_pose_id", String(36), ForeignKey("camera_poses.id", ondelete="SET NULL"), nullable=True),
        Column("depth_artifact_id", String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True),
        Column("segmentation_artifact_id", String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True),
        Column("dynamic_mask_artifact_id", String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True),
        Column("contribution_status", String(64), nullable=True),
        Column("notes_json", JSON, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_reconstruction_frames_reconstruction_run_id", "reconstruction_frames", ["reconstruction_run_id"])
    op.create_index("ix_reconstruction_frames_frame_id", "reconstruction_frames", ["frame_id"])
    op.create_index("ix_reconstruction_frames_camera_pose_id", "reconstruction_frames", ["camera_pose_id"])
    op.create_index("ix_reconstruction_frames_depth_artifact_id", "reconstruction_frames", ["depth_artifact_id"])
    op.create_index("ix_reconstruction_frames_segmentation_artifact_id", "reconstruction_frames", ["segmentation_artifact_id"])
    op.create_index("ix_reconstruction_frames_dynamic_mask_artifact_id", "reconstruction_frames", ["dynamic_mask_artifact_id"])


    # ------------------------------------------------------------------
    # PointCloudArtifact
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "point_cloud_artifacts",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("reconstruction_run_id", String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False),
        Column("storage_path", String(512), nullable=False),
        Column("relative_path", String(512), nullable=True),
        Column("file_size_bytes", Integer, nullable=True),
        Column("checksum_sha256", String(64), nullable=True),
        Column("mime_type", String(100), nullable=True),
        Column("coordinate_frame", String(64), nullable=True),
        Column("units", String(64), nullable=True),
        Column("point_count", Integer, nullable=True),
        Column("bounds_min", JSON, nullable=True),
        Column("bounds_max", JSON, nullable=True),
        Column("extent", JSON, nullable=True),
        Column("density", Float, nullable=True),
        Column("description", Text, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_point_cloud_artifacts_reconstruction_run_id", "point_cloud_artifacts", ["reconstruction_run_id"])

    # ------------------------------------------------------------------
    # MeshArtifact
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "mesh_artifacts",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("reconstruction_run_id", String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False),
        Column("storage_path", String(512), nullable=False),
        Column("relative_path", String(512), nullable=True),
        Column("file_size_bytes", Integer, nullable=True),
        Column("checksum_sha256", String(64), nullable=True),
        Column("mime_type", String(100), nullable=True),
        Column("coordinate_frame", String(64), nullable=True),
        Column("units", String(64), nullable=True),
        Column("vertex_count", Integer, nullable=True),
        Column("face_count", Integer, nullable=True),
        Column("is_watertight", JSON, nullable=True),
        Column("bounds_min", JSON, nullable=True),
        Column("bounds_max", JSON, nullable=True),
        Column("extent", JSON, nullable=True),
        Column("surface_area", Float, nullable=True),
        Column("description", Text, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_mesh_artifacts_reconstruction_run_id", "mesh_artifacts", ["reconstruction_run_id"])

    # ------------------------------------------------------------------
    # TextureArtifact
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "texture_artifacts",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("reconstruction_run_id", String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False),
        Column("storage_path", String(512), nullable=False),
        Column("relative_path", String(512), nullable=True),
        Column("file_size_bytes", Integer, nullable=True),
        Column("checksum_sha256", String(64), nullable=True),
        Column("mime_type", String(100), nullable=True),
        Column("texture_type", String(64), nullable=True),
        Column("source_frame_ids_json", JSON, nullable=True),
        Column("texture_generation_parameters_json", JSON, nullable=True),
        Column("description", Text, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_texture_artifacts_reconstruction_run_id", "texture_artifacts", ["reconstruction_run_id"])

    # ------------------------------------------------------------------
    # ReconstructionQualityReport
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "reconstruction_quality_reports",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("reconstruction_run_id", String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False),
        Column("validated_point_count", Integer, nullable=True),
        Column("validated_registered_images", Integer, nullable=True),
        Column("validated_reprojection_error_px", Float, nullable=True),
        Column("validated_point_cloud_density", Float, nullable=True),
        Column("validated_mesh_vertex_count", Integer, nullable=True),
        Column("validated_mesh_face_count", Integer, nullable=True),
        Column("validated_connected_components", Integer, nullable=True),
        Column("validated_mesh_completeness_indicators_json", JSON, nullable=True),
        Column("processing_runtime_seconds", Integer, nullable=True),
        Column("processing_failures_json", JSON, nullable=True),
        Column("geometry_source_provenance_json", JSON, nullable=True),
        Column("validation_status", String(64), nullable=True),
        Column("validation_notes", Text, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_reconstruction_quality_reports_reconstruction_run_id", "reconstruction_quality_reports", ["reconstruction_run_id"])


def downgrade() -> None:
    op.drop_index("ix_reconstruction_quality_reports_reconstruction_run_id", table_name="reconstruction_quality_reports")
    op.drop_table("reconstruction_quality_reports")

    op.drop_index("ix_texture_artifacts_reconstruction_run_id", table_name="texture_artifacts")
    op.drop_table("texture_artifacts")

    op.drop_index("ix_mesh_artifacts_reconstruction_run_id", table_name="mesh_artifacts")
    op.drop_table("mesh_artifacts")

    op.drop_index("ix_point_cloud_artifacts_reconstruction_run_id", table_name="point_cloud_artifacts")
    op.drop_table("point_cloud_artifacts")

    op.drop_index("ix_reconstruction_frames_dynamic_mask_artifact_id", table_name="reconstruction_frames")
    op.drop_index("ix_reconstruction_frames_segmentation_artifact_id", table_name="reconstruction_frames")
    op.drop_index("ix_reconstruction_frames_depth_artifact_id", table_name="reconstruction_frames")
    op.drop_index("ix_reconstruction_frames_camera_pose_id", table_name="reconstruction_frames")
    op.drop_index("ix_reconstruction_frames_frame_id", table_name="reconstruction_frames")
    op.drop_index("ix_reconstruction_frames_reconstruction_run_id", table_name="reconstruction_frames")
    op.drop_table("reconstruction_frames")

    op.drop_index("ix_reconstruction_runs_status", table_name="reconstruction_runs")
    op.drop_index("ix_reconstruction_runs_mission_id", table_name="reconstruction_runs")
    op.drop_table("reconstruction_runs")
