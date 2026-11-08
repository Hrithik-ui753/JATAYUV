import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class CameraPose(Base):
    __tablename__ = "camera_poses"
    __table_args__ = (
        Index("ix_camera_pose_frame_id", "frame_id"),
        Index("ix_camera_pose_mission_id", "mission_id"),
        Index("ix_camera_pose_confidence", "confidence"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(
        String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame_id = Column(
        String(36), ForeignKey("frames.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    position_z = Column(Float, nullable=True)
    rotation_matrix_json = Column(Text, nullable=True)
    quaternion_json = Column(Text, nullable=True)
    coordinate_frame = Column(
        String(64), default="world", nullable=False
    )  # world | camera | image
    pose_source = Column(
        String(64), default="unknown", nullable=False
    )  # sfm | slam | manual | unknown
    confidence = Column(Float, nullable=True)
    reprojection_error = Column(Float, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    mission = relationship("Mission", back_populates="camera_poses")
    frame = relationship("Frame", back_populates="camera_pose")
