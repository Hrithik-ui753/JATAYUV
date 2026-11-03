import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class DepthResult(Base):
    __tablename__ = "depth_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    image_id = Column(String(36), ForeignKey("images.id"), nullable=False)
    depth_map_path = Column(String(512), nullable=False)
    colormap_path = Column(String(512), nullable=False)
    min_depth_m = Column(Float, nullable=False)
    max_depth_m = Column(Float, nullable=False)
    mean_depth_m = Column(Float, nullable=False)
    mesh_obj_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    image = relationship("Image", back_populates="depth_results")

class SegmentationResult(Base):
    __tablename__ = "segmentation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    image_id = Column(String(36), ForeignKey("images.id"), nullable=False)
    mask_path = Column(String(512), nullable=False)
    overlay_path = Column(String(512), nullable=False)
    class_distribution_json = Column(Text, nullable=False)  # JSON {building: 28.4, ...}
    geojson_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    image = relationship("Image", back_populates="segmentation_results")

class DamageAssessmentResult(Base):
    __tablename__ = "damage_assessment_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    pre_image_id = Column(String(36), ForeignKey("images.id"), nullable=False)
    post_image_id = Column(String(36), ForeignKey("images.id"), nullable=False)
    damage_overlay_path = Column(String(512), nullable=False)
    total_buildings = Column(Integer, nullable=False)
    counts_by_level_json = Column(Text, nullable=False)  # JSON {no_damage: 10, minor: 4...}
    damage_percentage = Column(Float, nullable=False)
    severity_index = Column(Float, nullable=False)  # 0 to 1.0
    geojson_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class ChangeDetectionResult(Base):
    __tablename__ = "change_detection_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    before_image_id = Column(String(36), ForeignKey("images.id"), nullable=False)
    after_image_id = Column(String(36), ForeignKey("images.id"), nullable=False)
    diff_mask_path = Column(String(512), nullable=False)
    heatmap_path = Column(String(512), nullable=False)
    changed_area_pct = Column(Float, nullable=False)
    changed_pixels = Column(Integer, nullable=False)
    significance_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

