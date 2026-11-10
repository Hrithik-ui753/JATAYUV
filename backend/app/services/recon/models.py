from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship, backref

from backend.app.core.database import Base


class ReconstructionRun(Base):
    __tablename__ = "reconstruction_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
<<<<<<< HEAD
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    georef_processing_run_id = Column(String(36), ForeignKey("georef_processing_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    processing_run_id = Column(String(36), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
=======
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    georef_processing_run_id = Column(String(36), ForeignKey("georef_processing_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    processing_run_id = Column(String(36), ForeignKey("processing_runs.id", ondelete="SET NULL"), nullable=True, index=True)
>>>>>>> origin/main
    reconstruction_version = Column(String(64), nullable=False)
    reconstruction_method = Column(String(128), nullable=False)
    status = Column(String(50), nullable=False)
    coordinate_reference_system = Column(String(64), nullable=True)
    coordinate_frame = Column(String(64), nullable=True)
    units = Column(String(64), nullable=True)
    point_cloud_path = Column(String(512), nullable=True)
    mesh_path = Column(String(512), nullable=True)
    texture_path = Column(String(512), nullable=True)
    mtl_path = Column(String(512), nullable=True)
    vertex_count = Column(Integer, nullable=True)
    face_count = Column(Integer, nullable=True)
    point_count = Column(Integer, nullable=True)
    source_frame_ids_json = Column(JSON, nullable=True)
    processing_duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", backref="reconstruction_runs")
    georef_processing_run = relationship("GeorefProcessingRun", backref="reconstruction_runs")
<<<<<<< HEAD
    job = relationship("Job", backref="reconstruction_runs")
=======
    processing_run = relationship("ProcessingRun", backref="reconstruction_runs")
>>>>>>> origin/main
    frames = relationship("ReconstructionFrame", backref="reconstruction_run", cascade="all, delete-orphan")
    point_cloud_artifacts = relationship("PointCloudArtifact", backref="reconstruction_run", cascade="all, delete-orphan")
    mesh_artifacts = relationship("MeshArtifact", backref="reconstruction_run", cascade="all, delete-orphan")
    texture_artifacts = relationship("TextureArtifact", backref="reconstruction_run", cascade="all, delete-orphan")
    quality_report = relationship("ReconstructionQualityReport", backref="reconstruction_run", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_reconstruction_runs_mission_id", "mission_id"),
        Index("ix_reconstruction_runs_status", "status"),
    )


class ReconstructionFrame(Base):
    __tablename__ = "reconstruction_frames"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
<<<<<<< HEAD
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False)
    frame_id = Column(String(36), ForeignKey("frames.id", ondelete="SET NULL"), nullable=False)
    camera_pose_id = Column(String(36), ForeignKey("camera_poses.id", ondelete="SET NULL"), nullable=True)
    depth_artifact_id = Column(String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True)
    segmentation_artifact_id = Column(String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True)
    dynamic_mask_artifact_id = Column(String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True)
=======
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    frame_id = Column(String(36), ForeignKey("frames.id", ondelete="SET NULL"), nullable=False, index=True)
    camera_pose_id = Column(String(36), ForeignKey("camera_poses.id", ondelete="SET NULL"), nullable=True, index=True)
    depth_artifact_id = Column(String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True, index=True)
    segmentation_artifact_id = Column(String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True, index=True)
    dynamic_mask_artifact_id = Column(String(36), ForeignKey("perception_artifacts.id", ondelete="SET NULL"), nullable=True, index=True)
>>>>>>> origin/main
    contribution_status = Column(String(64), nullable=True)
    notes_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_reconstruction_frames_reconstruction_run_id", "reconstruction_run_id"),
        Index("ix_reconstruction_frames_frame_id", "frame_id"),
        Index("ix_reconstruction_frames_camera_pose_id", "camera_pose_id"),
        Index("ix_reconstruction_frames_depth_artifact_id", "depth_artifact_id"),
        Index("ix_reconstruction_frames_segmentation_artifact_id", "segmentation_artifact_id"),
        Index("ix_reconstruction_frames_dynamic_mask_artifact_id", "dynamic_mask_artifact_id"),
    )


class PointCloudArtifact(Base):
    __tablename__ = "point_cloud_artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
<<<<<<< HEAD
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False)
=======
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False, index=True)
>>>>>>> origin/main
    storage_path = Column(String(512), nullable=False)
    relative_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    coordinate_frame = Column(String(64), nullable=True)
    units = Column(String(64), nullable=True)
    point_count = Column(Integer, nullable=True)
    bounds_min = Column(JSON, nullable=True)
    bounds_max = Column(JSON, nullable=True)
    extent = Column(JSON, nullable=True)
    density = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_point_cloud_artifacts_reconstruction_run_id", "reconstruction_run_id"),
    )


class MeshArtifact(Base):
    __tablename__ = "mesh_artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
<<<<<<< HEAD
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False)
=======
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False, index=True)
>>>>>>> origin/main
    storage_path = Column(String(512), nullable=False)
    relative_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    coordinate_frame = Column(String(64), nullable=True)
    units = Column(String(64), nullable=True)
    vertex_count = Column(Integer, nullable=True)
    face_count = Column(Integer, nullable=True)
    is_watertight = Column(JSON, nullable=True)
    bounds_min = Column(JSON, nullable=True)
    bounds_max = Column(JSON, nullable=True)
    extent = Column(JSON, nullable=True)
    surface_area = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_mesh_artifacts_reconstruction_run_id", "reconstruction_run_id"),
    )


class TextureArtifact(Base):
    __tablename__ = "texture_artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
<<<<<<< HEAD
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False)
=======
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False, index=True)
>>>>>>> origin/main
    storage_path = Column(String(512), nullable=False)
    relative_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    texture_type = Column(String(64), nullable=True)
    source_frame_ids_json = Column(JSON, nullable=True)
    texture_generation_parameters_json = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_texture_artifacts_reconstruction_run_id", "reconstruction_run_id"),
    )


class ReconstructionQualityReport(Base):
    __tablename__ = "reconstruction_quality_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
<<<<<<< HEAD
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False)
=======
    reconstruction_run_id = Column(String(36), ForeignKey("reconstruction_runs.id", ondelete="CASCADE"), nullable=False, index=True)
>>>>>>> origin/main
    validated_point_count = Column(Integer, nullable=True)
    validated_registered_images = Column(Integer, nullable=True)
    validated_reprojection_error_px = Column(Float, nullable=True)
    validated_point_cloud_density = Column(Float, nullable=True)
    validated_mesh_vertex_count = Column(Integer, nullable=True)
    validated_mesh_face_count = Column(Integer, nullable=True)
    validated_connected_components = Column(Integer, nullable=True)
    validated_mesh_completeness_indicators_json = Column(JSON, nullable=True)
    processing_runtime_seconds = Column(Integer, nullable=True)
    processing_failures_json = Column(JSON, nullable=True)
    geometry_source_provenance_json = Column(JSON, nullable=True)
    validation_status = Column(String(64), nullable=True)
    validation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_reconstruction_quality_reports_reconstruction_run_id", "reconstruction_run_id"),
    )
