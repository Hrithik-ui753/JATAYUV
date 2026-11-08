"""Initial mission data spine

Add mission-oriented entities for SIH26158:
- missions
- videos
- flight_metadata
- frames
- camera_poses
- reconstructions
- georef_solutions
- validation_reports

The `jobs` table is extended additively (mission_id, stage) using batch mode
so existing data is preserved and no existing columns/tables are dropped.

This migration never touches existing tables beyond the additive jobs change.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


def _existing_indexes(table_name: str) -> set:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=:t ORDER BY name")
    ).fetchall()
    return {r[0] for r in rows}


revision: str = "001_initial_mission_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fk(name, table, ref_table, columns, ref_columns, ondelete=None):
    kwargs = {
        "name": name,
        "source": table,
        "referent": ref_table,
        "local_cols": columns,
        "remote_cols": ref_columns,
    }
    if ondelete:
        kwargs["ondelete"] = ondelete
    return sa.ForeignKeyConstraint(**kwargs)


def upgrade() -> None:
    # --- missions ---
    op.create_table(
        "missions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("mission_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location_name", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'created'"),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    mission_idxs = _existing_indexes("missions")
    with op.batch_alter_table("missions", schema=None) as batch_op:
        if "ix_missions_status_created" not in mission_idxs:
            batch_op.create_index("ix_missions_status_created", ["status", "created_at"])
        if "ix_missions_user_id" not in mission_idxs:
            batch_op.create_index("ix_missions_user_id", ["user_id"])
        if "ix_missions_project_id" not in mission_idxs:
            batch_op.create_index("ix_missions_project_id", ["project_id"])
        if "fk_missions_user" not in [c.name for c in batch_op.table.foreign_keys]:
            batch_op.create_foreign_key("fk_missions_user", "users", ["user_id"], ["id"])
        if "fk_missions_project" not in [c.name for c in batch_op.table.foreign_keys]:
            batch_op.create_foreign_key("fk_missions_project", "projects", ["project_id"], ["id"])
        batch_op.create_check_constraint(
            "ck_mission_status_values",
            "status IN ('cancelled','completed','created','failed','processing','ready','uploaded','uploading','validating')",
        )

    # --- videos ---
    op.create_table(
        "videos",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mission_id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("frame_rate", sa.Integer(), nullable=True),
        sa.Column("codec", sa.String(length=100), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "upload_status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "validation_status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("videos", schema=None) as batch_op:
        batch_op.create_index("ix_videos_mission_id", ["mission_id"])
        batch_op.create_index("ix_videos_created_at", ["created_at"])
        batch_op.create_unique_constraint("uq_mission_filename", ["mission_id", "original_filename"])
        batch_op.create_foreign_key("fk_videos_mission", "missions", ["mission_id"], ["id"], ondelete="CASCADE")

    # --- flight_metadata ---
    op.create_table(
        "flight_metadata",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mission_id", sa.String(length=36), nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=True),
        sa.Column("start_timestamp", sa.String(length=64), nullable=True),
        sa.Column("end_timestamp", sa.String(length=64), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("altitude_datum", sa.String(length=64), nullable=True),
        sa.Column("coordinate_reference_system", sa.String(length=64), nullable=True),
        sa.Column("horizontal_accuracy", sa.Float(), nullable=True),
        sa.Column("vertical_accuracy", sa.Float(), nullable=True),
        sa.Column("camera_make", sa.String(length=255), nullable=True),
        sa.Column("camera_model", sa.String(length=255), nullable=True),
        sa.Column("focal_length", sa.Float(), nullable=True),
        sa.Column("sensor_width", sa.Float(), nullable=True),
        sa.Column("sensor_height", sa.Float(), nullable=True),
        sa.Column("image_width", sa.Integer(), nullable=True),
        sa.Column("image_height", sa.Integer(), nullable=True),
        sa.Column("camera_intrinsics_json", sa.Text(), nullable=True),
        sa.Column("imu_data_path", sa.String(length=512), nullable=True),
        sa.Column("barometric_altitude", sa.Float(), nullable=True),
        sa.Column("rtk_enabled", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ppk_enabled", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("metadata_source", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("flight_metadata", schema=None) as batch_op:
        batch_op.create_index("ix_flight_mission_id", ["mission_id"])
        batch_op.create_index("ix_flight_video_id", ["video_id"])
        batch_op.create_foreign_key("fk_flight_mission", "missions", ["mission_id"], ["id"], ondelete="CASCADE")
        batch_op.create_foreign_key("fk_flight_video", "videos", ["video_id"], ["id"], ondelete="SET NULL")

    # --- frames ---
    op.create_table(
        "frames",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mission_id", sa.String(length=36), nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("frame_index", sa.Integer(), nullable=False),
        sa.Column("presentation_timestamp", sa.Float(), nullable=True),
        sa.Column("timestamp_seconds", sa.Float(), nullable=True),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("blur_score", sa.Float(), nullable=True),
        sa.Column("exposure_score", sa.Float(), nullable=True),
        sa.Column(
            "duplicate_status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'unique'"),
        ),
        sa.Column(
            "quality_status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'unreviewed'"),
        ),
        sa.Column("gps_latitude", sa.Float(), nullable=True),
        sa.Column("gps_longitude", sa.Float(), nullable=True),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("frames", schema=None) as batch_op:
        batch_op.create_index("ix_frames_mission_id", ["mission_id"])
        batch_op.create_index("ix_frames_video_id", ["video_id"])
        batch_op.create_index("ix_frames_frame_index", ["frame_index"])
        batch_op.create_index("ix_frames_presentation_timestamp", ["presentation_timestamp"])
        batch_op.create_index("ix_frames_created_at", ["created_at"])
        batch_op.create_unique_constraint("uq_video_frame_index", ["video_id", "frame_index"])
        batch_op.create_foreign_key("fk_frames_mission", "missions", ["mission_id"], ["id"], ondelete="CASCADE")
        batch_op.create_foreign_key("fk_frames_video", "videos", ["video_id"], ["id"], ondelete="CASCADE")

    # --- camera_poses ---
    op.create_table(
        "camera_poses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mission_id", sa.String(length=36), nullable=False),
        sa.Column("frame_id", sa.String(length=36), nullable=False),
        sa.Column("position_x", sa.Float(), nullable=True),
        sa.Column("position_y", sa.Float(), nullable=True),
        sa.Column("position_z", sa.Float(), nullable=True),
        sa.Column("rotation_matrix_json", sa.Text(), nullable=True),
        sa.Column("quaternion_json", sa.Text(), nullable=True),
        sa.Column(
            "coordinate_frame",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'world'"),
        ),
        sa.Column(
            "pose_source",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'unknown'"),
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("reprojection_error", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("camera_poses", schema=None) as batch_op:
        batch_op.create_index("ix_camera_pose_frame_id", ["frame_id"])
        batch_op.create_index("ix_camera_pose_mission_id", ["mission_id"])
        batch_op.create_index("ix_camera_pose_confidence", ["confidence"])
        batch_op.create_foreign_key("fk_pose_mission", "missions", ["mission_id"], ["id"], ondelete="CASCADE")
        batch_op.create_foreign_key("fk_pose_frame", "frames", ["frame_id"], ["id"], ondelete="CASCADE")

    # --- reconstructions ---
    op.create_table(
        "reconstructions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mission_id", sa.String(length=36), nullable=False),
        sa.Column("reconstruction_version", sa.String(length=64), nullable=False),
        sa.Column("reconstruction_method", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("point_cloud_path", sa.String(length=512), nullable=True),
        sa.Column("mesh_path", sa.String(length=512), nullable=True),
        sa.Column("texture_path", sa.String(length=512), nullable=True),
        sa.Column("coordinate_reference_system", sa.String(length=64), nullable=True),
        sa.Column("point_count", sa.Integer(), nullable=True),
        sa.Column("vertex_count", sa.Integer(), nullable=True),
        sa.Column("face_count", sa.Integer(), nullable=True),
        sa.Column("coverage_ratio", sa.Float(), nullable=True),
        sa.Column("processing_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("reconstructions", schema=None) as batch_op:
        batch_op.create_index("ix_reconstructions_mission_id", ["mission_id"])
        batch_op.create_index("ix_reconstructions_status", ["status"])
        batch_op.create_index("ix_reconstructions_created_at", ["created_at"])
        batch_op.create_foreign_key("fk_reconstructions_mission", "missions", ["mission_id"], ["id"], ondelete="CASCADE")

    # --- georef_solutions ---
    op.create_table(
        "georef_solutions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mission_id", sa.String(length=36), nullable=False),
        sa.Column("reconstruction_id", sa.String(length=36), nullable=False),
        sa.Column("coordinate_reference_system", sa.String(length=64), nullable=True),
        sa.Column("horizontal_datum", sa.String(length=64), nullable=True),
        sa.Column("vertical_datum", sa.String(length=64), nullable=True),
        sa.Column("scale_factor", sa.Float(), nullable=True),
        sa.Column("translation_json", sa.Text(), nullable=True),
        sa.Column("rotation_json", sa.Text(), nullable=True),
        sa.Column("scale_uncertainty", sa.Float(), nullable=True),
        sa.Column("horizontal_residual", sa.Float(), nullable=True),
        sa.Column("vertical_residual", sa.Float(), nullable=True),
        sa.Column("control_point_count", sa.Integer(), nullable=True),
        sa.Column("solution_method", sa.String(length=128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("georef_solutions", schema=None) as batch_op:
        batch_op.create_index("ix_georef_mission_id", ["mission_id"])
        batch_op.create_index("ix_georef_reconstruction_id", ["reconstruction_id"])
        batch_op.create_foreign_key("fk_georef_mission", "missions", ["mission_id"], ["id"], ondelete="CASCADE")
        batch_op.create_foreign_key("fk_georef_reconstruction", "reconstructions", ["reconstruction_id"], ["id"], ondelete="SET NULL")

    # --- validation_reports ---
    op.create_table(
        "validation_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mission_id", sa.String(length=36), nullable=False),
        sa.Column("reconstruction_id", sa.String(length=36), nullable=False),
        sa.Column(
            "validation_status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("spatial_accuracy", sa.Float(), nullable=True),
        sa.Column("completeness_ratio", sa.Float(), nullable=True),
        sa.Column("point_cloud_density", sa.Float(), nullable=True),
        sa.Column("reprojection_error", sa.Float(), nullable=True),
        sa.Column("processing_time_seconds", sa.Integer(), nullable=True),
        sa.Column("validation_method", sa.String(length=128), nullable=True),
        sa.Column("reference_data_source", sa.String(length=255), nullable=True),
        sa.Column("uncertainty_json", sa.Text(), nullable=True),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("validation_reports", schema=None) as batch_op:
        batch_op.create_index("ix_validation_mission_id", ["mission_id"])
        batch_op.create_index("ix_validation_reconstruction_id", ["reconstruction_id"])
        batch_op.create_index("ix_validation_generated_at", ["generated_at"])
        batch_op.create_foreign_key("fk_validation_mission", "missions", ["mission_id"], ["id"], ondelete="CASCADE")
        batch_op.create_foreign_key("fk_validation_reconstruction", "reconstructions", ["reconstruction_id"], ["id"], ondelete="SET NULL")

    # --- extend existing jobs table additively (preserve data, no drops) ---
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("mission_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("stage", sa.String(length=64), nullable=True))
        batch_op.create_index("ix_jobs_mission_id", ["mission_id"])
        batch_op.create_foreign_key("fk_jobs_mission", "missions", ["mission_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    # Reverse in dependency order.
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        existing_jobs_constraints = {c.name for c in batch_op.table.foreign_keys}
        if "fk_jobs_mission" in existing_jobs_constraints:
            batch_op.drop_constraint("fk_jobs_mission", type_="foreignkey")
        if "ix_jobs_mission_id" in [i.name for i in batch_op.table.indexes]:
            batch_op.drop_index("ix_jobs_mission_id")
        batch_op.drop_column("stage")
        batch_op.drop_column("mission_id")

    op.drop_table("validation_reports")
    op.drop_table("georef_solutions")
    op.drop_table("reconstructions")
    op.drop_table("camera_poses")
    op.drop_table("frames")
    op.drop_table("flight_metadata")
    op.drop_table("videos")
    op.drop_table("missions")
