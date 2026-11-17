"""add p3 perception tables

Revision ID: 003_p3_perception_tables
Revises: 002_p2_frame_extensions
Create Date: 2026-11-08 00:00:00.000000

"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    Text,
)
import sqlalchemy as sa
from alembic import op

# 

def _create_table_if_missing(name, *args, **kwargs):
    """Create a table only when it does not already exist.

    Existing installations may have been provisioned by an older release (or by
    ``create_all``) before Alembic was introduced. Re-running the chain must not
    fail on those databases.
    """
    if name in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(name, *args, **kwargs)

# revision identifiers, used by Alembic.
revision = "003_p3_perception_tables"
down_revision = "002_p2_frame_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # PerceptionRun
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "perception_runs",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("mission_id", String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        Column("job_id", String(36), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        Column("video_id", String(36), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True),
        Column("processing_run_id", String(64), nullable=True),
        Column("status", String(32), nullable=False, server_default=op.inline_literal("pending")),
        Column("started_at", DateTime, nullable=True),
        Column("completed_at", DateTime, nullable=True),
        Column("cancelled_at", DateTime, nullable=True),
        Column("device", String(32), nullable=True),
        Column("depth_model_id", String(100), nullable=True),
        Column("depth_model_version", String(100), nullable=True),
        Column("depth_checkpoint_sha256", String(64), nullable=True),
        Column("segmentation_model_id", String(100), nullable=True),
        Column("segmentation_model_version", String(100), nullable=True),
        Column("segmentation_checkpoint_sha256", String(64), nullable=True),
        Column("dynamic_model_id", String(100), nullable=True),
        Column("dynamic_model_version", String(100), nullable=True),
        Column("dynamic_checkpoint_sha256", String(64), nullable=True),
        Column("batch_size", Integer, nullable=True),
        Column("total_selected_frames", Integer, nullable=True),
        Column("processed_frames", Integer, nullable=True),
        Column("failed_frames", Integer, nullable=True),
        Column("error_message", Text, nullable=True),
        Column("config_json", JSON, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
    )
    op.create_index("ix_perception_runs_mission_id", "perception_runs", ["mission_id"])
    op.create_index("ix_perception_runs_status", "perception_runs", ["status"])
    op.create_index("ix_perception_runs_created_at", "perception_runs", ["created_at"])

    # ------------------------------------------------------------------
    # FramePerception
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "frame_perceptions",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("perception_run_id", String(36), ForeignKey("perception_runs.id", ondelete="CASCADE"), nullable=False),
        Column("frame_id", String(36), ForeignKey("frames.id", ondelete="CASCADE"), nullable=False),
        Column("status", String(32), nullable=False, server_default=op.inline_literal("pending")),
        Column("processing_duration_seconds", Float(asdecimal=False), nullable=True),
        Column("error_message", Text, nullable=True),
        Column("warnings_json", JSON, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_frame_perceptions_perception_run_id", "frame_perceptions", ["perception_run_id"])
    op.create_index("ix_frame_perceptions_frame_id", "frame_perceptions", ["frame_id"])

    # ------------------------------------------------------------------
    # FrameDepthResult
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "frame_depth_results",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("frame_perception_id", String(36), ForeignKey("frame_perceptions.id", ondelete="CASCADE"), nullable=False),
        Column("depth_map_path", String(512), nullable=False),
        Column("depth_visualization_path", String(512), nullable=False),
        Column("raw_depth_path", String(512), nullable=True),
        Column("model_id", String(100), nullable=True),
        Column("model_version", String(100), nullable=True),
        Column("checkpoint_sha256", String(64), nullable=True),
        Column("input_width", Integer, nullable=True),
        Column("input_height", Integer, nullable=True),
        Column("output_width", Integer, nullable=True),
        Column("output_height", Integer, nullable=True),
        Column("inference_device", String(32), nullable=True),
        Column("inference_duration_ms", Float(asdecimal=False), nullable=True),
        Column("preprocessing_json", JSON, nullable=True),
        Column("depth_type", String(32), nullable=True),
        Column("depth_unit", String(64), nullable=True),
        Column("is_metric", Integer, nullable=True),
        Column("depth_min", Float(asdecimal=False), nullable=True),
        Column("depth_max", Float(asdecimal=False), nullable=True),
        Column("depth_mean", Float(asdecimal=False), nullable=True),
        Column("relative_min", Float(asdecimal=False), nullable=True),
        Column("relative_max", Float(asdecimal=False), nullable=True),
        Column("relative_mean", Float(asdecimal=False), nullable=True),
        Column("confidence_json", JSON, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_frame_depth_results_depth_type", "frame_depth_results", ["depth_type"])

    # ------------------------------------------------------------------
    # FrameSegmentationResult
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "frame_segmentation_results",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("frame_perception_id", String(36), ForeignKey("frame_perceptions.id", ondelete="CASCADE"), nullable=False),
        Column("mask_path", String(512), nullable=False),
        Column("visualization_path", String(512), nullable=False),
        Column("model_id", String(100), nullable=True),
        Column("model_version", String(100), nullable=True),
        Column("checkpoint_sha256", String(64), nullable=True),
        Column("input_width", Integer, nullable=True),
        Column("input_height", Integer, nullable=True),
        Column("output_width", Integer, nullable=True),
        Column("output_height", Integer, nullable=True),
        Column("inference_device", String(32), nullable=True),
        Column("inference_duration_ms", Float(asdecimal=False), nullable=True),
        Column("preprocessing_json", JSON, nullable=True),
        Column("class_distribution_json", JSON, nullable=False),
        Column("per_class_pixel_counts_json", JSON, nullable=False),
        Column("unsupported_class_handling_json", JSON, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )

    # ------------------------------------------------------------------
    # FrameDynamicObjectResult
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "frame_dynamic_object_results",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("frame_perception_id", String(36), ForeignKey("frame_perceptions.id", ondelete="CASCADE"), nullable=False),
        Column("dynamic_mask_path", String(512), nullable=True),
        Column("detections_json", JSON, nullable=False),
        Column("model_id", String(100), nullable=True),
        Column("model_version", String(100), nullable=True),
        Column("checkpoint_sha256", String(64), nullable=True),
        Column("inference_device", String(32), nullable=True),
        Column("inference_duration_ms", Float(asdecimal=False), nullable=True),
        Column("preprocessing_json", JSON, nullable=True),
        Column("dynamic_label_policy", String(64), nullable=True),
        Column("created_at", DateTime, nullable=False),
    )

    # ------------------------------------------------------------------
    # PerceptionArtifact
    # ------------------------------------------------------------------
    _create_table_if_missing(
        "perception_artifacts",
        Column("id", String(36), primary_key=True, default=op.inline_literal(str)),
        Column("perception_run_id", String(36), ForeignKey("perception_runs.id", ondelete="CASCADE"), nullable=False),
        Column("frame_id", String(36), ForeignKey("frames.id", ondelete="SET NULL"), nullable=True),
        Column("artifact_type", String(64), nullable=False),
        Column("storage_path", String(512), nullable=False),
        Column("relative_path", String(512), nullable=True),
        Column("file_size_bytes", Integer, nullable=True),
        Column("checksum_sha256", String(64), nullable=True),
        Column("mime_type", String(100), nullable=True),
        Column("description", Text, nullable=True),
        Column("model_id", String(100), nullable=True),
        Column("model_version", String(100), nullable=True),
        Column("checkpoint_sha256", String(64), nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    op.create_index("ix_perception_artifacts_perception_run_id", "perception_artifacts", ["perception_run_id"])
    op.create_index("ix_perception_artifacts_frame_id", "perception_artifacts", ["frame_id"])
    op.create_index("ix_perception_artifacts_artifact_type", "perception_artifacts", ["artifact_type"])


def downgrade() -> None:
    # Drop in reverse dependency order.
    op.drop_index("ix_perception_artifacts_artifact_type", table_name="perception_artifacts")
    op.drop_index("ix_perception_artifacts_frame_id", table_name="perception_artifacts")
    op.drop_index("ix_perception_artifacts_perception_run_id", table_name="perception_artifacts")
    op.drop_table("perception_artifacts")

    op.drop_table("frame_dynamic_object_results")
    op.drop_table("frame_segmentation_results")
    op.drop_index("ix_frame_depth_results_depth_type", table_name="frame_depth_results")
    op.drop_table("frame_depth_results")
    op.drop_index("ix_frame_perceptions_frame_id", table_name="frame_perceptions")
    op.drop_index("ix_frame_perceptions_perception_run_id", table_name="frame_perceptions")
    op.drop_table("frame_perceptions")

    op.drop_index("ix_perception_runs_created_at", table_name="perception_runs")
    op.drop_index("ix_perception_runs_status", table_name="perception_runs")
    op.drop_index("ix_perception_runs_mission_id", table_name="perception_runs")
    op.drop_table("perception_runs")
