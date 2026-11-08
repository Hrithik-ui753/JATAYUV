from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CameraPoseResponse(BaseModel):
    id: str
    mission_id: str
    frame_id: str
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    rotation_matrix_json: Optional[str] = None
    quaternion_json: Optional[str] = None
    coordinate_frame: str
    pose_source: str
    confidence: Optional[float] = None
    reprojection_error: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}
