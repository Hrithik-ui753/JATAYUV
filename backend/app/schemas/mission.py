from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MissionBase(BaseModel):
    mission_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location_name: Optional[str] = None


class MissionCreate(MissionBase):
    project_id: str


class MissionUpdate(BaseModel):
    mission_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location_name: Optional[str] = None
    status: Optional[str] = None


class MissionResponse(MissionBase):
    id: str
    user_id: str
    project_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MissionListResponse(MissionResponse):
    """Lightweight list item; avoids eager-loading nested collections in list endpoints."""
    video_count: Optional[int] = None
    reconstruction_count: Optional[int] = None
