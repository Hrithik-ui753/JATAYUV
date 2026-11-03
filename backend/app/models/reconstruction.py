import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Reconstruction3D(Base):
    __tablename__ = "reconstructions_3d"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    pointcloud_ply_path = Column(String(512), nullable=False)
    mesh_obj_path = Column(String(512), nullable=True)
    dsm_tiff_path = Column(String(512), nullable=True)
    num_points = Column(Integer, default=0, nullable=False)
    camera_count = Column(Integer, default=0, nullable=False)
    reprojection_error_px = Column(Float, default=0.0, nullable=False)
    bounds_json = Column(Text, nullable=True)  # min/max x, y, z
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="reconstructions")

