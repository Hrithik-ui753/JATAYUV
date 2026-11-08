import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Frame(Base):
    __tablename__ = "frames"
    __table_args__ = (
        Index("ix_frames_mission_id", "mission_id"),
        Index("ix_frames_video_id", "video_id"),
        Index("ix_frames_frame_index", "frame_index"),
        Index("ix_frames_presentation_timestamp", "presentation_timestamp"),
        Index("ix_frames_created_at", "created_at"),
        UniqueConstraint("video_id", "frame_index", name="uq_video_frame_index"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(
        String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id = Column(
        String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame_index = Column(Integer, nullable=False)
    presentation_timestamp = Column(Float, nullable=True)  # original PTS preserved
    timestamp_seconds = Column(Float, nullable=True)  # computed wall-clock seconds
    storage_path = Column(String(512), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    blur_score = Column(Float, nullable=True)
    exposure_score = Column(Float, nullable=True)
    duplicate_status = Column(
        String(32), default="unique", nullable=False
    )  # unique | duplicate | candidate
    quality_status = Column(
        String(32), default="unreviewed", nullable=False
    )  # unreviewed | accepted | rejected | low_quality
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    mission = relationship("Mission", back_populates="frames")
    video = relationship("Video", back_populates="frames")
    camera_pose = relationship(
        "CameraPose", back_populates="frame", cascade="all, delete-orphan", uselist=False
    )
