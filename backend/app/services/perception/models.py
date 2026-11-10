from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class PerceptionRun(Base):
    __tablename__ = "perception_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(
        String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True)
    processing_run_id = Column(String(64), nullable=True, index=True)
    status = Column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    device = Column(String(32), nullable=True)
    depth_model_id = Column(String(100), nullable=True)
    depth_model_version = Column(String(100), nullable=True)
    depth_checkpoint_sha256 = Column(String(64), nullable=True)
    segmentation_model_id = Column(String(100), nullable=True)
    segmentation_model_version = Column(String(100), nullable=True)
    segmentation_checkpoint_sha256 = Column(String(64), nullable=True)
    dynamic_model_id = Column(String(100), nullable=True)
    dynamic_model_version = Column(String(100), nullable=True)
    dynamic_checkpoint_sha256 = Column(String(64), nullable=True)
    batch_size = Column(Integer, nullable=True)
    total_selected_frames = Column(Integer, nullable=True)
    processed_frames = Column(Integer, nullable=True)
    failed_frames = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    config_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    mission = relationship("Mission", backref="perception_runs")
    video = relationship("Video", backref="perception_runs")
    job = relationship("Job", backref="perception_run")
    frames = relationship(
        "FramePerception",
        backref="perception_run",
        cascade="all, delete-orphan",
<<<<<<< HEAD
        order_by="FramePerception.created_at",
=======
        order_by="FramePerception.frame_index",
>>>>>>> origin/main
    )

    __table_args__ = (
        Index("ix_perception_runs_status", "status"),
        Index("ix_perception_runs_mission_status", "mission_id", "status"),
        Index("ix_perception_runs_created_at", "created_at"),
    )


class FramePerception(Base):
    __tablename__ = "frame_perceptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    perception_run_id = Column(
        String(36), ForeignKey("perception_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame_id = Column(
<<<<<<< HEAD
        String(36), ForeignKey("frames.id", ondelete="CASCADE"), nullable=False
=======
        String(36), ForeignKey("frames.id", ondelete="CASCADE"), nullable=False, index=True
>>>>>>> origin/main
    )
    status = Column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    processing_duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    warnings_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    frame = relationship("Frame", backref="frame_perceptions")
    depth_result = relationship(
        "FrameDepthResult", backref="frame_perception", uselist=False, cascade="all, delete-orphan"
    )
    segmentation_result = relationship(
        "FrameSegmentationResult",
        backref="frame_perception",
        uselist=False,
        cascade="all, delete-orphan",
    )
    dynamic_result = relationship(
        "FrameDynamicObjectResult",
        backref="frame_perception",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_frame_perceptions_status", "status"),
        Index("ix_frame_perceptions_frame_id", "frame_id"),
    )


class FrameDepthResult(Base):
    __tablename__ = "frame_depth_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    frame_perception_id = Column(
        String(36), ForeignKey("frame_perceptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    depth_map_path = Column(String(512), nullable=False)
    depth_visualization_path = Column(String(512), nullable=False)
    raw_depth_path = Column(String(512), nullable=True)
    model_id = Column(String(100), nullable=True)
    model_version = Column(String(100), nullable=True)
    checkpoint_sha256 = Column(String(64), nullable=True)
    input_width = Column(Integer, nullable=True)
    input_height = Column(Integer, nullable=True)
    output_width = Column(Integer, nullable=True)
    output_height = Column(Integer, nullable=True)
    inference_device = Column(String(32), nullable=True)
    inference_duration_ms = Column(Float, nullable=True)
    preprocessing_json = Column(JSON, nullable=True)
    depth_type = Column(String(32), nullable=True)
    depth_unit = Column(String(64), nullable=True)
    is_metric = Column(Integer, nullable=True)
    depth_min = Column(Float, nullable=True)
    depth_max = Column(Float, nullable=True)
    depth_mean = Column(Float, nullable=True)
    relative_min = Column(Float, nullable=True)
    relative_max = Column(Float, nullable=True)
    relative_mean = Column(Float, nullable=True)
    confidence_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (Index("ix_frame_depth_results_depth_type", "depth_type"),)


class FrameSegmentationResult(Base):
    __tablename__ = "frame_segmentation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    frame_perception_id = Column(
        String(36), ForeignKey("frame_perceptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mask_path = Column(String(512), nullable=False)
    visualization_path = Column(String(512), nullable=False)
    model_id = Column(String(100), nullable=True)
    model_version = Column(String(100), nullable=True)
    checkpoint_sha256 = Column(String(64), nullable=True)
    input_width = Column(Integer, nullable=True)
    input_height = Column(Integer, nullable=True)
    output_width = Column(Integer, nullable=True)
    output_height = Column(Integer, nullable=True)
    inference_device = Column(String(32), nullable=True)
    inference_duration_ms = Column(Float, nullable=True)
    preprocessing_json = Column(JSON, nullable=True)
    class_distribution_json = Column(JSON, nullable=False)
    per_class_pixel_counts_json = Column(JSON, nullable=False)
    unsupported_class_handling_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


class FrameDynamicObjectResult(Base):
    __tablename__ = "frame_dynamic_object_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    frame_perception_id = Column(
        String(36), ForeignKey("frame_perceptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dynamic_mask_path = Column(String(512), nullable=True)
    detections_json = Column(JSON, nullable=False)
    model_id = Column(String(100), nullable=True)
    model_version = Column(String(100), nullable=True)
    checkpoint_sha256 = Column(String(64), nullable=True)
    inference_device = Column(String(32), nullable=True)
    inference_duration_ms = Column(Float, nullable=True)
    preprocessing_json = Column(JSON, nullable=True)
    dynamic_label_policy = Column(String(64), nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


class PerceptionArtifact(Base):
    __tablename__ = "perception_artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    perception_run_id = Column(
        String(36), ForeignKey("perception_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
<<<<<<< HEAD
    frame_id = Column(String(36), ForeignKey("frames.id", ondelete="SET NULL"), nullable=True)
=======
    frame_id = Column(String(36), ForeignKey("frames.id", ondelete="SET NULL"), nullable=True, index=True)
>>>>>>> origin/main
    artifact_type = Column(String(64), nullable=False)
    storage_path = Column(String(512), nullable=False)
    relative_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    model_id = Column(String(100), nullable=True)
    model_version = Column(String(100), nullable=True)
    checkpoint_sha256 = Column(String(64), nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("ix_perception_artifacts_type", "artifact_type"),
        Index("ix_perception_artifacts_frame_id", "frame_id"),
    )
