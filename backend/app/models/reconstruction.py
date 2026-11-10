import uuid
from datetime import datetime, timezone
<<<<<<< HEAD
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

=======
<<<<<<< HEAD
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

=======
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

>>>>>>> origin/main
ReconstructionStatus = None  # placeholder, enum added in __table_args below


class Reconstruction(Base):
    __tablename__ = "reconstructions"
    __table_args__ = (
<<<<<<< HEAD
=======
        Index("ix_reconstructions_mission_id", "mission_id"),
>>>>>>> origin/main
        Index("ix_reconstructions_status", "status"),
        Index("ix_reconstructions_created_at", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(
        String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reconstruction_version = Column(String(64), nullable=False)  # e.g. "2026-03-14T14-00-00"
    reconstruction_method = Column(String(128), nullable=False)  # colmap_sfm | openmvg | unknown
    status = Column(
        String(50), default="pending", nullable=False
    )  # pending | queued | processing | completed | failed | cancelled

    point_cloud_path = Column(String(512), nullable=True)
    mesh_path = Column(String(512), nullable=True)
    texture_path = Column(String(512), nullable=True)
    coordinate_reference_system = Column(String(64), nullable=True)  # EPSG:xxxx
    point_count = Column(Integer, nullable=True)
    vertex_count = Column(Integer, nullable=True)
    face_count = Column(Integer, nullable=True)
    coverage_ratio = Column(Float, nullable=True)
    processing_duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    mission = relationship("Mission", back_populates="reconstructions")
    georef_solution = relationship(
        "GeorefSolution", back_populates="reconstruction", uselist=False
    )
    validation_reports = relationship(
        "ValidationReport", back_populates="reconstruction", cascade="all, delete-orphan"
    )


# Legacy project-scoped reconstruction class kept for backwards compatibility
# with the existing reconstruction API and any code that imports
# ``Reconstruction3D`` from ``backend.app.models.reconstruction``.
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
<<<<<<< HEAD
    bounds_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="reconstructions")
=======
<<<<<<< HEAD
    bounds_json = Column(Text, nullable=True)  # min/max x, y, z
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="reconstructions")

=======
    bounds_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="reconstructions")
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
