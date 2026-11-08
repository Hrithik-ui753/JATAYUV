from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ValidationReportResponse(BaseModel):
    id: str
    mission_id: str
    reconstruction_id: str
    validation_status: str
    spatial_accuracy: Optional[float] = None
    completeness_ratio: Optional[float] = None
    point_cloud_density: Optional[float] = None
    reprojection_error: Optional[float] = None
    processing_time_seconds: Optional[int] = None
    validation_method: Optional[str] = None
    reference_data_source: Optional[str] = None
    uncertainty_json: Optional[str] = None
    metrics_json: Optional[str] = None
    warnings_json: Optional[str] = None
    generated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
