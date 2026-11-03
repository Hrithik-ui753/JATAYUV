from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ExifTelemetry(BaseModel):
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    focal_length_mm: Optional[float] = None
    iso: Optional[int] = None
    exposure_time: Optional[str] = None
    altitude_m: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heading_deg: Optional[float] = None
    capture_time: Optional[str] = None

class ImageResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_path: str
    thumbnail_path: Optional[str] = None
    file_size_bytes: int
    width: int
    height: int
    format: str
    is_preprocessed: bool
    preprocessed_path: Optional[str] = None
    telemetry: Optional[ExifTelemetry] = None
    created_at: datetime

    class Config:
        from_attributes = True

