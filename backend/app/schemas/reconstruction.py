from datetime import datetime
<<<<<<< HEAD
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

<<<<<<< HEAD

class MissionReconstructionResponse(BaseModel):
    """Mission-scoped reconstruction record (``Reconstruction`` model)."""

=======
=======
from typing import Optional
from pydantic import BaseModel, Field


class ReconstructionResponse(BaseModel):
>>>>>>> origin/main
    id: str
    mission_id: str
    reconstruction_version: str
    reconstruction_method: str
    status: str
    point_cloud_path: Optional[str] = None
    mesh_path: Optional[str] = None
    texture_path: Optional[str] = None
    coordinate_reference_system: Optional[str] = None
    point_count: Optional[int] = None
    vertex_count: Optional[int] = None
    face_count: Optional[int] = None
    coverage_ratio: Optional[float] = None
    processing_duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

<<<<<<< HEAD
    class Config:
        from_attributes = True
=======
    model_config = {"from_attributes": True}
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
