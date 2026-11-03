from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Depth
class DepthTriggerRequest(BaseModel):
    image_id: str

class DepthResponse(BaseModel):
    id: str
    job_id: str
    image_id: str
    depth_map_path: str
    colormap_path: str
    min_depth_m: float
    max_depth_m: float
    mean_depth_m: float
    mesh_obj_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

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

