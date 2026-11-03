import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    thumbnail_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    format = Column(String(20), nullable=False)
    is_preprocessed = Column(Boolean, default=False, nullable=False)
    preprocessed_path = Column(String(512), nullable=True)
    
    # Serialized EXIF / GPS Telemetry JSON
    telemetry_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="images")
    depth_results = relationship("DepthResult", back_populates="image", cascade="all, delete-orphan")
    segmentation_results = relationship("SegmentationResult", back_populates="image", cascade="all, delete-orphan")

