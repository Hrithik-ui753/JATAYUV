from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    location_name: str
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location_name: Optional[str] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None

class ProjectResponse(ProjectBase):
    id: str
    owner_id: str
    image_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

