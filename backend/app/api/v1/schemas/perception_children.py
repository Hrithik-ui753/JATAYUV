from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FrameDepthResponse(BaseModel):
    frame_id: str
    depth_map_path: Optional[str] = None
    depth_visualization_path: Optional[str] = None
    raw_depth_path: Optional[str] = None
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    depth_type: Optional[str] = None
    depth_unit: Optional[str] = None
    is_metric: Optional[bool] = None
    input_width: Optional[int] = None
    input_height: Optional[int] = None
    output_width: Optional[int] = None
    output_height: Optional[int] = None
    inference_device: Optional[str] = None
    inference_duration_ms: Optional[float] = None
    depth_min: Optional[float] = None
    depth_max: Optional[float] = None
    depth_mean: Optional[float] = None
    relative_min: Optional[float] = None
    relative_max: Optional[float] = None
    relative_mean: Optional[float] = None
    confidence: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class FrameSegmentationResponse(BaseModel):
    frame_id: str
    mask_path: Optional[str] = None
    visualization_path: Optional[str] = None
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    input_width: Optional[int] = None
    input_height: Optional[int] = None
    output_width: Optional[int] = None
    output_height: Optional[int] = None
    inference_device: Optional[str] = None
    inference_duration_ms: Optional[float] = None
    class_distribution: Dict[str, float] = {}
    per_class_pixel_counts: Dict[str, int] = {}
    unsupported_class_handling: Dict[str, str] = {}
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class FrameDynamicMaskResponse(BaseModel):
    frame_id: str
    dynamic_mask_path: Optional[str] = None
    detections: List[Dict[str, Any]] = []
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    inference_device: Optional[str] = None
    inference_duration_ms: Optional[float] = None
    dynamic_label_policy: Optional[str] = None
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class FramePerceptionResponse(BaseModel):
    frame_id: str
    mission_id: Optional[str] = None
    video_id: Optional[str] = None
    frame_index: Optional[int] = None
    presentation_timestamp: Optional[float] = None
    timestamp_seconds: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    altitude: Optional[float] = None
    altitude_datum: Optional[str] = None
    gps_source: Optional[str] = None
    gps_association_gap_seconds: Optional[float] = None
    status: str
    processing_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    warnings: Dict[str, Any] = {}
    depth: Optional[FrameDepthResponse] = None
    segmentation: Optional[FrameSegmentationResponse] = None
    dynamic: Optional[FrameDynamicMaskResponse] = None
    perception_run_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MissionPerceptionProcessResponse(BaseModel):
    perception_run_id: str
    mission_id: str
    status: str
    started_at: Optional[datetime] = None
    message: Optional[str] = None
    status_url: Optional[str] = None

    model_config = {"from_attributes": True}


class MissionPerceptionStatusResponse(BaseModel):
    perception_run_id: str
    mission_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    device: Optional[str] = None
    total_selected_frames: Optional[int] = None
    processed_frames: Optional[int] = None
    failed_frames: Optional[int] = None
    progress_pct: Optional[int] = None
    error_message: Optional[str] = None
    depth_model_id: Optional[str] = None
    segmentation_model_id: Optional[str] = None
    dynamic_model_id: Optional[str] = None

    model_config = {"from_attributes": True}


class MissionPerceptionReportResponse(BaseModel):
    perception_run_id: Optional[str] = None
    mission_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    device: Optional[str] = None
    total_selected_frames: Optional[int] = None
    processed_frames: Optional[int] = None
    failed_frames: Optional[int] = None
    depth_model_id: Optional[str] = None
    depth_model_version: Optional[str] = None
    depth_checkpoint_sha256: Optional[str] = None
    segmentation_model_id: Optional[str] = None
    segmentation_model_version: Optional[str] = None
    segmentation_checkpoint_sha256: Optional[str] = None
    dynamic_model_id: Optional[str] = None
    dynamic_model_version: Optional[str] = None
    dynamic_checkpoint_sha256: Optional[str] = None
    batch_size: Optional[int] = None
    total_runtime_seconds: Optional[float] = None
    artifact_counts: Dict[str, int] = {}
    error_message: Optional[str] = None
    warnings: List[str] = []
    notes: List[str] = []

    model_config = {"from_attributes": True}


class MissionPerceptionModelsResponse(BaseModel):
    models: Dict[str, Any]

    model_config = {"from_attributes": True}


class MissionCancelResponse(BaseModel):
    perception_run_id: str
    cancelled: bool
    status: str

    model_config = {"from_attributes": True}
