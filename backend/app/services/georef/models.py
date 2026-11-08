from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

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
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class GeorefProcessingRun(Base):
    __tablename__ = "georef_processing_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    perception_run_id = Column(String(36), ForeignKey("perception_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    tracking_run_id = Column(String(36), ForeignKey("tracking_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    reconstruction_id = Column(String(36), ForeignKey("reconstructions.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(32), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    config_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", backref="georef_processing_runs")
    perception_run = relationship("PerceptionRun", backref="georef_processing_run")
    tracking_run = relationship("TrackingRun", backref="georef_processing_run")
    reconstruction = relationship("Reconstruction", backref="georef_processing_run")
    transformations = relationship("CoordinateTransformation", backref="georef_processing_run", cascade="all, delete-orphan")
    control_points = relationship("GroundControlPoint", backref="georef_processing_run", cascade="all, delete-orphan")
    checkpoint_observations = relationship("CheckpointObservation", backref="georef_processing_run", cascade="all, delete-orphan")
    artifacts = relationship("GeorefArtifact", backref="georef_processing_run", cascade="all, delete-orphan")
    validation_metrics = relationship("SpatialValidationMetric", backref="georef_processing_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_georef_processing_runs_mission_id", "mission_id"),
        Index("ix_georef_processing_runs_status", "status"),
    )


class GroundControlPoint(Base):
    __tablename__ = "ground_control_points"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    georef_processing_run_id = Column(String(36), ForeignKey("georef_processing_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    label = Column(String(128), nullable=True)
    category = Column(String(64), nullable=True)
    role = Column(String(32), nullable=False)
    local_x = Column(Float, nullable=True)
    local_y = Column(Float, nullable=True)
    local_z = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    elevation = Column(Float, nullable=True)
    target_x = Column(Float, nullable=True)
    target_y = Column(Float, nullable=True)
    target_z = Column(Float, nullable=True)
    horizontal_accuracy = Column(Float, nullable=True)
    vertical_accuracy = Column(Float, nullable=True)
    measurement_source = Column(Text, nullable=True)
    measurement_method = Column(Text, nullable=True)
    observed_at = Column(DateTime, nullable=True)
    provenance_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_gcps_mission_id", "mission_id"),
        Index("ix_gcps_role", "role"),
    )


class CoordinateTransformation(Base):
    __tablename__ = "coordinate_transformations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    georef_processing_run_id = Column(String(36), ForeignKey("georef_processing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_crs = Column(String(64), nullable=False)
    target_crs = Column(String(64), nullable=False)
    source_coordinate_frame = Column(String(64), nullable=True)
    target_coordinate_frame = Column(String(64), nullable=True)
    horizontal_datum = Column(String(64), nullable=True)
    vertical_datum = Column(String(64), nullable=True)
    translation_x = Column(Float, nullable=True)
    translation_y = Column(Float, nullable=True)
    translation_z = Column(Float, nullable=True)
    scale_factor = Column(Float, nullable=True)
    rotation_matrix_json = Column(Text, nullable=True)
    transformation_method = Column(String(128), nullable=True)
    scale_method = Column(String(128), nullable=True)
    residuals_json = Column(JSON, nullable=True)
    uncertainty_json = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_coordinate_transformations_georef_run_id", "georef_processing_run_id"),
    )


class CheckpointObservation(Base):
    __tablename__ = "checkpoint_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    georef_processing_run_id = Column(String(36), ForeignKey("georef_processing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    gcp_id = Column(String(36), ForeignKey("ground_control_points.id", ondelete="SET NULL"), nullable=True, index=True)
    observed_x = Column(Float, nullable=True)
    observed_y = Column(Float, nullable=True)
    observed_z = Column(Float, nullable=True)
    observed_lat = Column(Float, nullable=True)
    observed_lon = Column(Float, nullable=True)
    observed_elevation = Column(Float, nullable=True)
    reference_x = Column(Float, nullable=True)
    reference_y = Column(Float, nullable=True)
    reference_z = Column(Float, nullable=True)
    horizontal_error = Column(Float, nullable=True)
    vertical_error = Column(Float, nullable=True)
    horizontal_distance_error = Column(Float, nullable=True)
    three_d_error = Column(Float, nullable=True)
    easting_error = Column(Float, nullable=True)
    northing_error = Column(Float, nullable=True)
    elevation_difference = Column(Float, nullable=True)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_checkpoint_observations_georef_run_id", "georef_processing_run_id"),
    )


class SpatialValidationMetric(Base):
    __tablename__ = "spatial_validation_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    georef_processing_run_id = Column(String(36), ForeignKey("georef_processing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(64), nullable=False)
    value = Column(Float, nullable=True)
    count = Column(Integer, nullable=True)
    reference_source = Column(Text, nullable=True)
    units = Column(String(64), nullable=True)
    checkpoint_ids_json = Column(JSON, nullable=True)
    method = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_spatial_validation_metrics_georef_run_id", "georef_processing_run_id"),
    )


class GeorefArtifact(Base):
    __tablename__ = "georef_artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    georef_processing_run_id = Column(String(36), ForeignKey("georef_processing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type = Column(String(64), nullable=False)
    storage_path = Column(String(512), nullable=False)
    relative_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    source_artifact_ids_json = Column(JSON, nullable=True)
    version = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_georef_artifacts_georef_run_id", "georef_processing_run_id"),
        Index("ix_georef_artifacts_artifact_type", "artifact_type"),
    )
