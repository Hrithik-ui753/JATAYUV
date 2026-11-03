from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ReconstructionTriggerRequest(BaseModel):
    project_id: str
    image_ids: Optional[List[str]] = None

class ReconstructionResponse(BaseModel):
    id: str
    project_id: str
    job_id: str
    pointcloud_ply_path: str
    mesh_obj_path: Optional[str] = None
    dsm_tiff_path: Optional[str] = None
    num_points: int
    camera_count: int
    reprojection_error_px: float
    bounds: Optional[Dict[str, float]] = None
    created_at: datetime

    class Config:
        from_attributes = True

