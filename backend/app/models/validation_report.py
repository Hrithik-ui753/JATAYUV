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


class ValidationReport(Base):
    __tablename__ = "validation_reports"
    __table_args__ = (
        Index("ix_validation_mission_id", "mission_id"),
        Index("ix_validation_reconstruction_id", "reconstruction_id"),
        Index("ix_validation_generated_at", "generated_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(
        String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reconstruction_id = Column(
        String(36), ForeignKey("reconstructions.id", ondelete="SET NULL"), nullable=False, index=True
    )
    validation_status = Column(
        String(50), default="pending", nullable=False
    )  # pending | running | passed | failed | unavailable
    spatial_accuracy = Column(Float, nullable=True)
    completeness_ratio = Column(Float, nullable=True)
    point_cloud_density = Column(Float, nullable=True)
    reprojection_error = Column(Float, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    validation_method = Column(String(128), nullable=True)
    reference_data_source = Column(String(255), nullable=True)
    uncertainty_json = Column(Text, nullable=True)
    metrics_json = Column(Text, nullable=True)
    warnings_json = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=True)

    mission = relationship("Mission", back_populates="validation_reports")
    reconstruction = relationship("Reconstruction", back_populates="validation_reports")
