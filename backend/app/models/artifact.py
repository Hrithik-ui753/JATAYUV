import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Artifact(Base):
    """Files produced by analysis or reconstruction jobs (depth maps, masks, point clouds, etc.)."""
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type = Column(
        String(100), nullable=False
    )  # depth_map | colormap | segmentation_mask | overlay | damage_overlay | diff_mask | heatmap | point_cloud | mesh_obj | geojson
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    job = relationship("Job", back_populates="artifacts")

