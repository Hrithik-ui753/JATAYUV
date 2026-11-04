from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Depth
class DepthTriggerRequest(BaseModel):
    image_id: str
    # Optional model selection: "pretrained" (official DAv2 Small) or
    # "jatayuv_drone_v1" (fine-tuned). Defaults to the configured default model.
    model_id: Optional[str] = None
    # Optional inference resolution (must be a multiple of 14; 518 is the official default).
    input_size: Optional[int] = None


class DepthResponse(BaseModel):
    id: str
    job_id: str
    image_id: str
    depth_map_path: str
    colormap_path: str
    # Metric fields are only populated for calibrated metric output; ``None`` means the
    # result is relative depth and must not be read as metres.
    min_depth_m: Optional[float] = None
    max_depth_m: Optional[float] = None
    mean_depth_m: Optional[float] = None
    mesh_obj_path: Optional[str] = None

    # Provenance / honesty metadata.
    depth_type: Optional[str] = None          # relative | metric_calibrated
    depth_unit: Optional[str] = None
    is_metric: Optional[bool] = None
    relative_min: Optional[float] = None
    relative_max: Optional[float] = None
    relative_mean: Optional[float] = None
    model_id: Optional[str] = None
    model_label: Optional[str] = None
    model_version: Optional[str] = None
    checkpoint_path: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    input_size: Optional[int] = None
    inference_ms: Optional[float] = None
    raw_depth_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DepthModelInfo(BaseModel):
    model_id: str
    label: str
    version: str
    description: str
    is_finetuned: bool
    checkpoint_path: str
    checkpoint_available: bool
    depth_type: str
    depth_unit: str

# Segmentation
class SegmentationTriggerRequest(BaseModel):
    image_id: str

class SegmentationResponse(BaseModel):
    id: str
    job_id: str
    image_id: str
    mask_path: str
    overlay_path: str
    class_distribution: Dict[str, float]
    geojson_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Damage Assessment
class DamageTriggerRequest(BaseModel):
    pre_image_id: str
    post_image_id: str

class DamageResponse(BaseModel):
    id: str
    job_id: str
    pre_image_id: str
    post_image_id: str
    damage_overlay_path: str
    total_buildings: int
    counts_by_level: Dict[str, int]
    damage_percentage: float
    severity_index: float
    geojson_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Change Detection
class ChangeTriggerRequest(BaseModel):
    before_image_id: str
    after_image_id: str

class ChangeResponse(BaseModel):
    id: str
    job_id: str
    before_image_id: str
    after_image_id: str
    diff_mask_path: str
    heatmap_path: str
    changed_area_pct: float
    changed_pixels: int
    significance_score: float
    created_at: datetime

    class Config:
        from_attributes = True

