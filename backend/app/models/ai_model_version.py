import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from backend.app.core.database import Base


class AIModelVersion(Base):
    """Tracks AI model versions, their performance metrics and availability."""
    __tablename__ = "ai_model_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String(100), nullable=False, index=True)   # e.g. depth_anything_v2
    display_name = Column(String(200), nullable=False)              # e.g. Depth Anything V2 Large
    version = Column(String(50), nullable=False)                    # e.g. 1.0.0
    task_type = Column(String(100), nullable=False)                 # depth_estimation | segmentation | damage_assessment | change_detection | reconstruction_3d
    weights_path = Column(String(500), nullable=True)               # relative path under MODELS_DIR
    description = Column(Text, nullable=True)
    accuracy_metrics = Column(JSON, nullable=True)                  # {"mIoU": 0.82, "F1": 0.91, ...}
    is_active = Column(String(1), default="1", nullable=False)      # "1" active, "0" deprecated
    loaded_at = Column(DateTime, nullable=True)                     # last time model was loaded into memory
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

