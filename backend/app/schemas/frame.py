from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FrameResponse(BaseModel):
    id: str
    mission_id: str
    video_id: str
    frame_index: int = Field(ge=0)
    presentation_timestamp: Optional[float] = None
    timestamp_seconds: Optional[float] = None
    storage_path: str
    width: Optional[int] = None
    height: Optional[int] = None
    blur_score: Optional[float] = None
    exposure_score: Optional[float] = None
    duplicate_status: str
    quality_status: str
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    altitude: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    # Do not leak internal storage paths to unauthorised clients.
    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        data["storage_path"] = None
        return data
