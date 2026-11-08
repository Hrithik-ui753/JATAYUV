import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Video(Base):
    __tablename__ = "videos"
    __table_args__ = (
        Index("ix_videos_mission_id", "mission_id"),
        Index("ix_videos_created_at", "created_at"),
        UniqueConstraint("mission_id", "original_filename", name="uq_mission_filename"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(
        String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    frame_rate = Column(Integer, nullable=True)
    codec = Column(String(100), nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    upload_status = Column(
        String(50), default="pending", nullable=False
    )  # pending | uploading | uploaded | failed
    validation_status = Column(
        String(50), default="pending", nullable=False
    )  # pending | valid | invalid | unknown
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    mission = relationship("Mission", back_populates="videos")
    flight_metadata = relationship(
        "FlightMetadata", back_populates="video", cascade="all, delete-orphan"
    )
    frames = relationship("Frame", back_populates="video", cascade="all, delete-orphan")
