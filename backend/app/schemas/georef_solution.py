from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GeorefSolutionResponse(BaseModel):
    id: str
    mission_id: str
    reconstruction_id: str
    coordinate_reference_system: Optional[str] = None
    horizontal_datum: Optional[str] = None
    vertical_datum: Optional[str] = None
    scale_factor: Optional[float] = None
    translation_json: Optional[str] = None
    rotation_json: Optional[str] = None
    scale_uncertainty: Optional[float] = None
    horizontal_residual: Optional[float] = None
    vertical_residual: Optional[float] = None
    control_point_count: Optional[int] = None
    solution_method: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}
