import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location_name = Column(String(255), nullable=False)
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="projects")
    images = relationship("Image", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    reconstructions = relationship("Reconstruction3D", back_populates="project", cascade="all, delete-orphan")
<<<<<<< HEAD
    missions = relationship("Mission", back_populates="project", cascade="all, delete-orphan")
=======
<<<<<<< HEAD
=======
    missions = relationship("Mission", back_populates="project", cascade="all, delete-orphan")
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

