import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # preprocessing, depth_estimation, semantic_segmentation, damage_assessment, change_detection, reconstruction_3d
    status = Column(String(50), default="pending", nullable=False)  # pending, queued, processing, completed, failed, cancelled
    progress_pct = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    timeout_seconds = Column(Integer, default=3600, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="jobs")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan", order_by="JobLog.created_at")

