from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    project_id: str
    job_type: str
    status: str
    progress_pct: int
    error_message: Optional[str] = None
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobLogResponse(BaseModel):
    id: str
    job_id: str
    level: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}

