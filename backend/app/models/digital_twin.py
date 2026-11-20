"""JATAYUV Digital Twin & Inspection Workflow Database Models.

Stores:
1. Transmission Corridors & corridor-level assets.
2. Digital Twin Assets (towers, conductor spans, insulator strings) with physical CRS or local relative coordinates.
3. Engineer Verification & field annotation state (human verification vs AI observation).
4. Inspection Tasks and maintenance repair lifecycle work orders.
"""
from __future__ import annotations

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
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class Corridor(Base):
    __tablename__ = "corridors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    voltage_kv = Column(Float, default=220.0, nullable=False)
    total_span_length_km = Column(Float, default=0.0, nullable=False)
    crs = Column(String(64), default="LOCAL_RELATIVE_3D", nullable=False)  # EPSG:4326 | EPSG:326xx | LOCAL_RELATIVE_3D
    is_georeferenced = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project = relationship("Project", backref="corridors")
    assets = relationship("CorridorAsset", back_populates="corridor", cascade="all, delete-orphan")


class CorridorAsset(Base):
    __tablename__ = "corridor_assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    corridor_id = Column(String(36), ForeignKey("corridors.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_tag = Column(String(64), nullable=False, index=True)  # TOWER-001, LINE-001, etc.
    asset_type = Column(String(64), nullable=False)  # transmission_tower, transmission_line, insulator, crossarm
    nominal_position_x = Column(Float, default=0.0, nullable=False)
    nominal_position_y = Column(Float, default=0.0, nullable=False)
    nominal_position_z = Column(Float, default=0.0, nullable=False)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    gps_altitude = Column(Float, nullable=True)
    health_status = Column(String(64), default="HEALTHY", nullable=False)  # HEALTHY | NEEDS_REVIEW | DEFECT_CONFIRMED | MAINTENANCE_SCHEDULED
    structural_tilt_deg = Column(Float, default=0.0, nullable=False)
    last_inspected_at = Column(DateTime, nullable=True)
    attributes_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    corridor = relationship("Corridor", back_populates="assets")


class InspectionFindingVerification(Base):
    __tablename__ = "inspection_finding_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_track_id = Column(String(64), nullable=False, index=True)
    anomaly_id = Column(String(64), nullable=False, index=True)
    finding_type = Column(String(64), default="AI_OBSERVATION", nullable=False)  # AI_OBSERVATION | VERIFIED_FINDING
    verification_status = Column(
        String(64), default="UNVERIFIED", nullable=False
    )  # UNVERIFIED | VERIFIED_DEFECT | FALSE_POSITIVE | ACCEPTED_CONDITION
    verified_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    engineer_notes = Column(Text, default="", nullable=False)
    repair_status = Column(
        String(64), default="PENDING_REVIEW", nullable=False
    )  # PENDING_REVIEW | WORK_ORDER_CREATED | IN_REPAIR | REPAIRED | RESOLVED
    field_photo_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    mission = relationship("Mission", backref="verifications")
    verified_by = relationship("User")


class InspectionTask(Base):
    __tablename__ = "inspection_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)
    priority = Column(String(32), default="MEDIUM", nullable=False)  # LOW | MEDIUM | HIGH | URGENT
    status = Column(String(32), default="OPEN", nullable=False)  # OPEN | ASSIGNED | IN_PROGRESS | COMPLETED | CANCELLED
    assigned_to = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=True)
    target_asset_ids_json = Column(Text, default="[]", nullable=False)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    mission = relationship("Mission", backref="tasks")

