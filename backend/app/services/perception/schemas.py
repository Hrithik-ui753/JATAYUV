from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PerceptionProcessRequest(BaseModel):
    model_id: Optional[str] = None
    segmentation_model_id: Optional[str] = None
    dynamic_model_id: Optional[str] = None
    depth_input_size: Optional[int] = None
    batch_size: Optional[int] = Field(None, ge=1)
    device: Optional[str] = None
    timeout_seconds: Optional[int] = Field(None, ge=0)
    telemetry_csv_path: Optional[str] = None

    model_config = {"extra": "ignore"}


class PerceptionModelInfo(BaseModel):
    model_id: Optional[str] = None
    architecture: Optional[str] = None
    variant: Optional[str] = None
    source: Optional[str] = None
    license: Optional[str] = None
    checkpoint_path: Optional[str] = None
    checkpoint_available: Optional[bool] = None
    checkpoint_sha256: Optional[str] = None
    version: Optional[str] = None
    input_resolution: Optional[int] = None
    output_type: Optional[str] = None
    depth_type: Optional[str] = None
    depth_unit: Optional[str] = None
    is_metric: Optional[bool] = None
    supported_classes: Optional[List[Dict[str, Any]]] = None
    target_mapping: Optional[Dict[str, str]] = None
    supported_categories: Optional[List[str]] = None
    dynamic_available: Optional[bool] = None
    notes: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class PerceptionRunStatus(BaseModel):
    perception_run_id: Optional[str] = None
    mission_id: Optional[str] = None
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


class FrameDepthOutput(BaseModel):
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


class FrameSegmentationOutput(BaseModel):
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


class DynamicDetection(BaseModel):
    category: str
    label: str
    score: Optional[float] = None
    box: Optional[List[float]] = None
    mask_path: Optional[str] = None
    dynamic_label: str = "POTENTIALLY_DYNAMIC"

    model_config = {"from_attributes": True}


class FrameDynamicOutput(BaseModel):
    frame_id: str
    dynamic_mask_path: Optional[str] = None
    detections: List[DynamicDetection] = []
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    inference_device: Optional[str] = None
    inference_duration_ms: Optional[float] = None
    dynamic_label_policy: Optional[str] = None
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class FramePerceptionOutput(BaseModel):
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
    depth: Optional[FrameDepthOutput] = None
    segmentation: Optional[FrameSegmentationOutput] = None
    dynamic: Optional[FrameDynamicOutput] = None
    perception_run_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PerceptionReport(BaseModel):
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
