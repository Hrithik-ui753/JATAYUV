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
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    perception_run_id = Column(String(36), ForeignKey("perception_runs.id", ondelete="SET NULL"), nullable=True)
    tracking_run_id = Column(String(36), nullable=True)
    reconstruction_id = Column(String(36), ForeignKey("reconstructions.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    config_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", backref="georef_processing_runs")

    __table_args__ = (
        Index("ix_georef_processing_runs_mission_id", "mission_id"),
        Index("ix_georef_processing_runs_status", "status"),
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
    status = Column(String(32), nullable=False, default="computed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    georef_processing_run = relationship("GeorefProcessingRun", backref="coordinate_transformations")


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

    georef_processing_run = relationship("GeorefProcessingRun", backref="spatial_validation_metrics")


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

    georef_processing_run = relationship("GeorefProcessingRun", backref="georef_artifacts")
