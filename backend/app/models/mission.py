import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

MISSION_STATUSES = frozenset([
    "created",
    "uploading",
    "uploaded",
    "validating",
    "ready",
    "processing",
    "completed",
    "failed",
    "cancelled",
])


class Mission(Base):
    __tablename__ = "missions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    mission_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location_name = Column(String(255), nullable=True)
    status = Column(
        String(50),
        default="created",
        nullable=False,
        index=True,
        server_default="created",
    )
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="missions")
    project = relationship("Project", back_populates="missions")
    videos = relationship("Video", back_populates="mission", cascade="all, delete-orphan")
    flight_metadata = relationship(
        "FlightMetadata", back_populates="mission", cascade="all, delete-orphan"
    )
    frames = relationship("Frame", back_populates="mission", cascade="all, delete-orphan")
    camera_poses = relationship(
        "CameraPose", back_populates="mission", cascade="all, delete-orphan"
    )
    reconstructions = relationship(
        "Reconstruction", back_populates="mission", cascade="all, delete-orphan"
    )
    georef_solutions = relationship(
        "GeorefSolution", back_populates="mission", cascade="all, delete-orphan"
    )
    validation_reports = relationship(
        "ValidationReport", back_populates="mission", cascade="all, delete-orphan"
    )
    jobs = relationship("Job", back_populates="mission")

    __table_args__ = (
        Index("ix_missions_status_created", "status", "created_at"),
        Index("ix_missions_user_id", "user_id"),
        Index("ix_missions_project_id", "project_id"),
        CheckConstraint(
            f"status IN ({','.join(repr(s) for s in sorted(MISSION_STATUSES))})",
            name="ck_mission_status_values",
        ),
    )
