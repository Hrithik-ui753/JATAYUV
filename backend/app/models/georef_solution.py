import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class GeorefSolution(Base):
    __tablename__ = "georef_solutions"
    __table_args__ = (
        Index("ix_georef_mission_id", "mission_id"),
        Index("ix_georef_reconstruction_id", "reconstruction_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(
        String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reconstruction_id = Column(
        String(36), ForeignKey("reconstructions.id", ondelete="SET NULL"), nullable=False, index=True
    )
    coordinate_reference_system = Column(String(64), nullable=True)
    horizontal_datum = Column(String(64), nullable=True)
    vertical_datum = Column(String(64), nullable=True)
    scale_factor = Column(Float, nullable=True)
    translation_json = Column(Text, nullable=True)
    rotation_json = Column(Text, nullable=True)
    scale_uncertainty = Column(Float, nullable=True)
    horizontal_residual = Column(Float, nullable=True)
    vertical_residual = Column(Float, nullable=True)
    control_point_count = Column(Integer, nullable=True)
    solution_method = Column(String(128), nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    mission = relationship("Mission", back_populates="georef_solutions")
    reconstruction = relationship("Reconstruction", back_populates="georef_solution")
