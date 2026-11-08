from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VideoProcessingConfig(BaseModel):
    max_frames: Optional[int] = Field(None, ge=0)
    sample_interval_seconds: Optional[float] = Field(None, gt=0)
    blur_threshold: Optional[float] = Field(None, ge=0)
    severe_blur_threshold: Optional[float] = Field(None, ge=0)
    exposure_low: Optional[float] = Field(None, ge=0)
    exposure_high: Optional[float] = Field(None, ge=0)
    min_width: Optional[int] = Field(None, ge=0)
    min_height: Optional[int] = Field(None, ge=0)
    dhash_size: Optional[int] = Field(None, ge=1)
    near_duplicate_hamming_max: Optional[int] = Field(None, ge=0)
    temporal_window_frames: Optional[int] = Field(None, ge=0)
    prefer_keep_newer: Optional[bool] = None
    min_temporal_spacing_seconds: Optional[float] = Field(None, ge=0)
    max_selected_frames: Optional[int] = Field(None, ge=0)
    motion_proxy_enabled: Optional[bool] = None
    scene_change_proxy_enabled: Optional[bool] = None
    motion_threshold: Optional[float] = Field(None, ge=0)
    scene_change_threshold: Optional[float] = Field(None, ge=0)
    gps_max_gap_seconds: Optional[float] = Field(None, ge=0)
    gps_allow_interpolation: Optional[bool] = None
    gps_interpolation_max_gap_seconds: Optional[float] = Field(None, ge=0)
    telemetry_csv_path: Optional[str] = None
    timeout_seconds: Optional[int] = Field(None, ge=0)

    model_config = {"extra": "ignore"}


class VideoMetadataResponse(BaseModel):
    container_format: Optional[str] = None
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    nominal_fps: Optional[float] = None
    avg_fps: Optional[float] = None
    codec_name: Optional[str] = None
    codec_long_name: Optional[str] = None
    pixel_format: Optional[str] = None
    stream_time_base: Optional[str] = None
    nb_frames: Optional[int] = None
    probe_duration_method: Optional[str] = None
    truncated_probe: Optional[bool] = None

    model_config = {"from_attributes": True}


class VideoProcessingStatusResponse(BaseModel):
    status: str
    stage: Optional[str] = None
    progress_pct: Optional[int] = None
    celery_task_id: Optional[str] = None
    processing_run_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    jobs: Optional[List[Dict[str, Any]]] = None

    model_config = {"from_attributes": True}


class ProcessingReportResponse(BaseModel):
    mission_id: str
    processing_run_id: Optional[str] = None
    job_id: Optional[str] = None
    job_status: Optional[str] = None
    job_stage: Optional[str] = None
    progress_pct: Optional[int] = None
    total_frames: int = 0
    frames_accepted: int = 0
    frames_warning: int = 0
    frames_rejected: int = 0
    frames_unreviewed: int = 0
    duplicate_frames: int = 0
    selected_frames: int = 0
    gps_associated_frames: int = 0
    gps_coverage_pct: float = 0.0
    error_message: Optional[str] = None
    notes: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class EnqueueProcessingResponse(BaseModel):
    job_id: str
    celery_task_id: Optional[str] = None
    processing_run_id: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}
