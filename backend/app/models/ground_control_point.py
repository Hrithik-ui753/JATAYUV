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

    mission = relationship("Mission", backref="ground_control_points")
    georef_processing_run = relationship("GeorefProcessingRun", backref="ground_control_points")

    __table_args__ = (
        Index("ix_ground_control_points_role", "role"),
    )
