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
<<<<<<< HEAD
        Index("ix_frames_frame_index", "frame_index"),
        Index("ix_frames_presentation_timestamp", "presentation_timestamp"),
        Index("ix_frames_created_at", "created_at"),
        Index("ix_frames_processing_run_id", "processing_run_id"),
        Index("ix_frames_quality_status", "quality_status"),
        Index("ix_frames_duplicate_status", "duplicate_status"),
        Index("ix_frames_is_selected", "is_selected"),
        Index("ix_frames_gps_source", "gps_source"),
        Index("ix_frames_timestamp_seconds", "timestamp_seconds"),
=======
        Index("ix_frames_mission_id", "mission_id"),
        Index("ix_frames_video_id", "video_id"),
        Index("ix_frames_frame_index", "frame_index"),
        Index("ix_frames_presentation_timestamp", "presentation_timestamp"),
        Index("ix_frames_created_at", "created_at"),
>>>>>>> origin/main
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
<<<<<<< HEAD
    )  # unique | exact_duplicate | near_duplicate | candidate
    duplicate_hash = Column(String(128), nullable=True)
    duplicate_of_frame_id = Column(String(36), nullable=True)
    duplicate_distance = Column(Integer, nullable=True)
    duplicate_reason = Column(String(64), nullable=True)
    quality_status = Column(
        String(32), default="unreviewed", nullable=False
    )  # unreviewed | accepted | warning | rejected | low_quality
    quality_details_json = Column(Text, nullable=True)
    is_selected = Column(Integer, default=0, nullable=True)
    selection_reason = Column(Text, nullable=True)
    processing_run_id = Column(String(64), nullable=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    altitude_datum = Column(String(64), nullable=True)
    gps_timestamp_seconds = Column(Float, nullable=True)
    gps_timestamp_str = Column(String(128), nullable=True)
    gps_quality = Column(String(64), nullable=True)
    gps_source = Column(String(64), nullable=True)
    gps_association_gap_seconds = Column(Float, nullable=True)
=======
    )  # unique | duplicate | candidate
    quality_status = Column(
        String(32), default="unreviewed", nullable=False
    )  # unreviewed | accepted | rejected | low_quality
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
>>>>>>> origin/main
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    mission = relationship("Mission", back_populates="frames")
    video = relationship("Video", back_populates="frames")
    camera_pose = relationship(
        "CameraPose", back_populates="frame", cascade="all, delete-orphan", uselist=False
    )
