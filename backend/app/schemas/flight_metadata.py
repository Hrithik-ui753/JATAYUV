from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FlightMetadataCreate(BaseModel):
    video_id: Optional[str] = None
    start_timestamp: Optional[str] = Field(None, max_length=64)
    end_timestamp: Optional[str] = Field(None, max_length=64)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude: Optional[float] = None
    altitude_datum: Optional[str] = Field(None, max_length=64)
    coordinate_reference_system: Optional[str] = Field(None, max_length=64)
    horizontal_accuracy: Optional[float] = Field(None, ge=0)
    vertical_accuracy: Optional[float] = Field(None, ge=0)
    camera_make: Optional[str] = Field(None, max_length=255)
    camera_model: Optional[str] = Field(None, max_length=255)
    focal_length: Optional[float] = None
    sensor_width: Optional[float] = None
    sensor_height: Optional[float] = None
    image_width: Optional[int] = Field(None, ge=0)
    image_height: Optional[int] = Field(None, ge=0)
    camera_intrinsics_json: Optional[str] = Field(None)
    imu_data_path: Optional[str] = Field(None, max_length=512)
    barometric_altitude: Optional[float] = None
    rtk_enabled: Optional[bool] = None
    ppk_enabled: Optional[bool] = None
    metadata_source: Optional[str] = Field(None, max_length=128)


class FlightMetadataResponse(BaseModel):
    id: str
    mission_id: str
    video_id: Optional[str] = None
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    altitude_datum: Optional[str] = None
    coordinate_reference_system: Optional[str] = None
    horizontal_accuracy: Optional[float] = None
    vertical_accuracy: Optional[float] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    focal_length: Optional[float] = None
    sensor_width: Optional[float] = None
    sensor_height: Optional[float] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    camera_intrinsics_json: Optional[str] = None
    imu_data_path: Optional[str] = None
    barometric_altitude: Optional[float] = None
    rtk_enabled: Optional[bool] = None
    ppk_enabled: Optional[bool] = None
    metadata_source: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
