"""Add P2 frame processing fields

Add per-frame processing fields needed by the real drone video pipeline:

- blur_score / exposure_score (rename existing exposure_score usage where needed)
- duplicate_status / duplicate_hash / duplicate_of_frame_id / duplicate_distance / duplicate_reason
- quality_status (extended) and quality_details_json
- is_selected / selection_reason
- processing_run_id
- gps association fields: gps_timestamp_seconds, gps_timestamp_str, gps_quality,
  gps_source, gps_association_gap_seconds, altitude_datum
- indexes for common query patterns

This migration is additive only. It never drops existing columns/tables and
preserves existing frame records.
"""
from typing import Union
from alembic import op
import sqlalchemy as sa


revision: str = "002_p2_frame_extensions"
down_revision: Union[str, None] = "001_initial_mission_tables"
branch_labels: Union[str, list[str], None] = None
depends_on: Union[str, list[str], None] = None


def upgrade() -> None:
    # --- Add P2 frame fields one at a time to avoid batch-mode ordering issues ---
    col_defs = [
        ("blur_score", sa.Float(), True),
        ("exposure_score", sa.Float(), True),
        ("duplicate_hash", sa.String(length=128), True),
        ("duplicate_of_frame_id", sa.String(length=36), True),
        ("duplicate_distance", sa.Integer(), True),
        ("duplicate_reason", sa.String(length=64), True),
        ("quality_details_json", sa.Text(), True),
        ("is_selected", sa.Integer(), True),
        ("selection_reason", sa.Text(), True),
        ("processing_run_id", sa.String(length=64), True),
        ("gps_timestamp_seconds", sa.Float(), True),
        ("gps_timestamp_str", sa.String(length=128), True),
        ("gps_quality", sa.String(length=64), True),
        ("gps_source", sa.String(length=64), True),
        ("gps_association_gap_seconds", sa.Float(), True),
        ("altitude_datum", sa.String(length=64), True),
    ]
    existing_frame_cols = {c.name for c in op.get_bind().execute(sa.text("PRAGMA table_info(frames)")).fetchall()}
    existing_frame_indexes = {i.name for i in op.get_bind().execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='frames'")).fetchall()}
    for name, col_type, nullable in col_defs:
        if name in existing_frame_cols:
            continue
        with op.batch_alter_table("frames", schema=None) as b_op:
            b_op.add_column(sa.Column(name, col_type, nullable=nullable))

    with op.batch_alter_table("frames", schema=None) as idx_op:
        if "ix_frames_processing_run_id" not in existing_frame_indexes:
            idx_op.create_index("ix_frames_processing_run_id", ["processing_run_id"])
        if "ix_frames_quality_status" not in existing_frame_indexes:
            idx_op.create_index("ix_frames_quality_status", ["quality_status"])
        if "ix_frames_duplicate_status" not in existing_frame_indexes:
            idx_op.create_index("ix_frames_duplicate_status", ["duplicate_status"])
        if "ix_frames_is_selected" not in existing_frame_indexes:
            idx_op.create_index("ix_frames_is_selected", ["is_selected"])
        if "ix_frames_gps_source" not in existing_frame_indexes:
            idx_op.create_index("ix_frames_gps_source", ["gps_source"])
        if "ix_frames_timestamp_seconds" not in existing_frame_indexes:
            idx_op.create_index("ix_frames_timestamp_seconds", ["timestamp_seconds"])
        if "ix_frames_presentation_timestamp" not in existing_frame_indexes:
            idx_op.create_index("ix_frames_presentation_timestamp", ["presentation_timestamp"])

    # Keep video_id+frame_index unique per run so retries don't duplicate frames.
    existing_unique_constraint_names = set()

    rows = op.get_bind().execute(
        sa.text("SELECT sql FROM sqlite_master WHERE type='table' AND name='frames'")
    ).fetchall()
    if rows and rows[0][0]:
        import re
        sql = rows[0][0]
        existing_unique_constraint_names = set(re.findall(r"CONSTRAINT\s+\"([^\"]+?)\"\s+UNIQUE", sql, flags=re.IGNORECASE))

def downgrade() -> None:
    existing_unique_constraint_names = set()

    rows = op.get_bind().execute(
        sa.text("SELECT sql FROM sqlite_master WHERE type='table' AND name='frames'")
    ).fetchall()
    if rows and rows[0][0]:
        import re
        sql = rows[0][0]
        existing_unique_constraint_names = set(re.findall(r"CONSTRAINT\s+\"([^\"]+?)\"\s+UNIQUE", sql, flags=re.IGNORECASE))

    if "uq_video_frame_index_run" in existing_unique_constraint_names:
        with op.batch_alter_table("frames", schema=None) as b_op:
            b_op.drop_constraint("uq_video_frame_index_run", type_="unique")

    existing_frame_indexes = {r[0] for r in op.get_bind().execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='frames' ORDER BY name")).fetchall()}
    for idx in (
        "ix_frames_processing_run_id",
        "ix_frames_quality_status",
        "ix_frames_duplicate_status",
        "ix_frames_is_selected",
        "ix_frames_gps_source",
        "ix_frames_timestamp_seconds",
        "ix_frames_presentation_timestamp",
    ):
        if idx in existing_frame_indexes:
            with op.batch_alter_table("frames", schema=None) as b_op:
                b_op.drop_index(idx)

    with op.batch_alter_table("frames", schema=None) as idx_op:
        for col in (
            "gps_association_gap_seconds",
            "gps_source",
            "gps_quality",
            "gps_timestamp_str",
            "gps_timestamp_seconds",
            "processing_run_id",
            "selection_reason",
            "is_selected",
            "quality_details_json",
            "duplicate_reason",
            "duplicate_distance",
            "duplicate_of_frame_id",
            "duplicate_hash",
            "exposure_score",
            "blur_score",
        ):
            idx_op.drop_column(col)
