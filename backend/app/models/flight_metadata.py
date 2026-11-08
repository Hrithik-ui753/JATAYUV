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


class FlightMetadata(Base):
    __tablename__ = "flight_metadata"
    __table_args__ = (
        Index("ix_flight_mission_id", "mission_id"),
        Index("ix_flight_video_id", "video_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(
        String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id = Column(
        String(36), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    start_timestamp = Column(String(64), nullable=True)  # ISO-ish or GPS time
    end_timestamp = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)  # ellipsoidal (default), overridden by datum fields
    altitude_datum = Column(
        String(64), nullable=True
    )  # ellipsoidal | orthometric | relative | unknown
    coordinate_reference_system = Column(String(64), nullable=True)  # EPSG:xxxx
    horizontal_accuracy = Column(Float, nullable=True)
    vertical_accuracy = Column(Float, nullable=True)
    camera_make = Column(String(255), nullable=True)
    camera_model = Column(String(255), nullable=True)
    focal_length = Column(Float, nullable=True)
    sensor_width = Column(Float, nullable=True)
    sensor_height = Column(Float, nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    camera_intrinsics_json = Column(Text, nullable=True)
    imu_data_path = Column(String(512), nullable=True)
    barometric_altitude = Column(Float, nullable=True)
    rtk_enabled = Column(Integer, default=0, nullable=False)  # 0/1
    ppk_enabled = Column(Integer, default=0, nullable=False)
    metadata_source = Column(String(128), nullable=True)  # exif | srgb | gopro | dji | mission planner | manual
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    mission = relationship("Mission", back_populates="flight_metadata")
    video = relationship("Video", back_populates="flight_metadata")
