from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VideoCreate(BaseModel):
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int = Field(..., ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    duration_seconds: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=0)
    height: Optional[int] = Field(None, ge=0)
    frame_rate: Optional[int] = Field(None, ge=0)
    codec: Optional[str] = Field(None, max_length=100)
    checksum_sha256: Optional[str] = Field(None, max_length=64)
    storage_path: str = Field(..., description="Internal storage path; not exposed in responses.")


class VideoUploadResponse(BaseModel):
    """Response returned after a video registration, before processing."""
    id: str
    mission_id: str
    original_filename: str
    file_size_bytes: int
    mime_type: Optional[str] = None
    upload_status: str
    validation_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class VideoResponse(VideoUploadResponse):
    duration_seconds: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_rate: Optional[int] = None
    codec: Optional[str] = None
    checksum_sha256: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
