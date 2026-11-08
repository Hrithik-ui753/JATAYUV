from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from backend.app.models.reconstruction import Reconstruction


class ReconstructionStartResponse(BaseModel):
    reconstruction_run_id: str
    mission_id: str
    status: str
    started_at: Optional[datetime] = None
    message: Optional[str] = None

    class Config:
        orm_mode = True


class ReconstructionStatusResponse(BaseModel):
    reconstruction_run_id: str
    mission_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    progress_pct: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        orm_mode = True


class ReconstructionReadinessResponse(BaseModel):
    mission_id: str
    selected_frame_count: int
    frame_files_readable: bool
    camera_intrinsics_available: bool
    valid_camera_pose_count: int
    has_poses: bool
    requires_dense_inputs: bool
    ready: bool
    warnings: List[str]

    class Config:
        orm_mode = True


class ReconstructionListResponse(BaseModel):
    items: List["ReconstructionDetailResponse"]
    total: int
    offset: int
    limit: int

    class Config:
        orm_mode = True


class ReconstructionDetailResponse(BaseModel):
    id: str
    mission_id: str
    reconstruction_version: str
    reconstruction_method: str
    status: str
    point_cloud_path: Optional[str] = None
    mesh_path: Optional[str] = None
    texture_path: Optional[str] = None
    coordinate_reference_system: Optional[str] = None
    coordinate_frame: Optional[str] = None
    units: Optional[str] = None
    point_count: Optional[int] = None
    vertex_count: Optional[int] = None
    face_count: Optional[int] = None
    texture_status: Optional[str] = None
    reprojection_error: Optional[float] = None
    processing_duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ReconstructionArtifactResponse(BaseModel):
    artifact_type: str
    storage_path: str
    relative_path: Optional[str] = None
    file_size_bytes: Optional[int] = None

    class Config:
        orm_mode = True


class ReconstructionReportResponse(BaseModel):
    reconstruction_id: str
    mission_id: str
    status: str
    method: Optional[str] = None
    coordinate_reference_system: Optional[str] = None
    coordinate_frame: Optional[str] = None
    units: Optional[str] = None
    point_count: Optional[int] = None
    vertex_count: Optional[int] = None
    face_count: Optional[int] = None
    texture_status: Optional[str] = None
    reprojection_error: Optional[float] = None
    processing_duration_seconds: Optional[int] = None
    runtime_seconds: Optional[int] = None
    stats: Dict[str, Any] = {}
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ReconstructionCancelResponse(BaseModel):
    reconstruction_id: str
    cancelled: bool
    status: str

    class Config:
        orm_mode = True
