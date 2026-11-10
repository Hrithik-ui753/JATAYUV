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


class CheckpointObservation(Base):
    __tablename__ = "checkpoint_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
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

    mission = relationship("Mission", backref="checkpoint_observations")
    georef_processing_run = relationship("GeorefProcessingRun", backref="checkpoint_observations")
    gcp = relationship("GroundControlPoint", backref="checkpoint_observations")

    __table_args__ = ()
